import io
import os
import time
import json
import wave
import asyncio
import numpy as np
import opuslib_next
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from config.logger import setup_logging
from core.utils.util import audio_to_data
from core.handle.abortHandle import handleAbortMessage
from core.handle.intentHandler import handle_user_intent
from core.utils.output_counter import check_device_output_limit
from core.handle.sendAudioHandle import send_stt_message, SentenceType

TAG = __name__
logger = setup_logging()

USE_AGENT_RUNTIME = os.environ.get("USE_AGENT_RUNTIME", "1") == "1"

# ── Spectral analysis thresholds ──────────────────────────────────────
# RMS energy floor: frames below this are ambient noise / faint echo → skip.
RMS_ENERGY_FLOOR = 80

# RMS above this → strong signal, likely direct human speech into mic.
RMS_HUMAN_THRESHOLD = 600

# Spectral flatness: TTS echo is tonal (low flatness), human speech is noisier.
# Below this → echo-like spectrum.
SPECTRAL_FLATNESS_ECHO_CEIL = 0.03

# Above this → human-like spectrum.
SPECTRAL_FLATNESS_HUMAN_FLOOR = 0.08

# ── Frame count thresholds ────────────────────────────────────────────
# Fast-path: spectral analysis says "human-like" → need fewer frames.
BARGE_IN_FAST_FRAMES = 2

# Normal-path (ambiguous spectral or no analysis available).
BARGE_IN_CONSECUTIVE_FRAMES = 3

# Slow-path: spectral analysis says "echo-like" → need more frames.
BARGE_IN_SLOW_FRAMES = 5

# Fallback when no TTS embedding available.
BARGE_IN_NO_EMBEDDING_FRAMES = 8

# After passing Stage 1, collect M more frames for echo embedding check.
ECHO_CHECK_BUFFER_FRAMES = 5

# Cooldown after an echo detection rejects barge-in (seconds).
ECHO_REJECT_COOLDOWN_S = 0.3

# Cosine similarity threshold: above this = TTS echo.
ECHO_SIMILARITY_THRESHOLD = 0.6

# Post-TTS cooldown: long when no echo detection available, short otherwise.
POST_TTS_COOLDOWN_LONG_S = 1.2
POST_TTS_COOLDOWN_SHORT_S = 0.2

# Force barge-in after this many sustained voice frames, regardless of echo check.
FORCE_BARGE_IN_FRAMES = 30

# During active TTS without echo detection, only process every Nth audio frame
# to reduce CPU load and keep the event loop responsive for WebSocket keepalive.
TTS_THROTTLE_SKIP_FRAMES = 2

# Pre-roll: number of audio frames to retain while TTS is playing.
# These frames are prepended to ASR when barge-in is confirmed, recovering
# the beginning of the user's utterance that would otherwise be lost.
PRE_ROLL_FRAMES = 20  # ~1.2s at 60ms/frame

# Grace period: allow up to N consecutive False frames without resetting counters.
GRACE_PERIOD_FRAMES = 3

# Timeout for echo check network call (seconds).
ECHO_CHECK_TIMEOUT_S = 0.5

# ── Spectral analysis helpers ─────────────────────────────────────────

_spectral_decoder_cache: dict = {}


def _get_spectral_decoder(conn) -> opuslib_next.Decoder:
    conn_id = id(conn)
    if conn_id not in _spectral_decoder_cache:
        _spectral_decoder_cache[conn_id] = opuslib_next.Decoder(16000, 1)
    return _spectral_decoder_cache[conn_id]


def _cleanup_spectral_decoder(conn):
    _spectral_decoder_cache.pop(id(conn), None)


def _compute_rms(pcm_int16: np.ndarray) -> float:
    if len(pcm_int16) == 0:
        return 0.0
    return float(np.sqrt(np.mean(pcm_int16.astype(np.float64) ** 2)))


def _compute_spectral_flatness(pcm_int16: np.ndarray) -> float:
    """Ratio of geometric mean to arithmetic mean of the power spectrum.
    Low values (~0.01-0.06) indicate tonal/TTS-like audio.
    Higher values (~0.10-0.30) indicate noisy/natural human speech."""
    if len(pcm_int16) < 64:
        return 0.0
    spectrum = np.abs(np.fft.rfft(pcm_int16.astype(np.float32)))
    spectrum = spectrum[spectrum > 1e-10]
    if len(spectrum) == 0:
        return 0.0
    log_mean = np.mean(np.log(spectrum))
    arith_mean = np.mean(spectrum)
    if arith_mean < 1e-10:
        return 0.0
    return float(np.exp(log_mean) / arith_mean)


def _classify_frame(opus_packet: bytes, conn) -> str:
    """Classify a single opus frame as 'echo', 'human', or 'ambiguous'
    based on RMS energy and spectral flatness.  Pure CPU, no network."""
    try:
        decoder = _get_spectral_decoder(conn)
        pcm_bytes = decoder.decode(opus_packet, 960)
        pcm_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)

        rms = _compute_rms(pcm_int16)
        if rms < RMS_ENERGY_FLOOR:
            return "echo"

        flatness = _compute_spectral_flatness(pcm_int16)

        # Primary: RMS energy (proximity to mic is the best discriminator)
        if rms >= RMS_HUMAN_THRESHOLD:
            return "human"

        # Below human threshold: use flatness as tiebreaker
        if flatness <= SPECTRAL_FLATNESS_ECHO_CEIL:
            return "echo"

        return "ambiguous"
    except Exception:
        return "ambiguous"


async def handleAudioMessage(conn: "ConnectionHandler", audio):
    # ── Agent runtime delegation (feature flag) ──────────────────────────
    if USE_AGENT_RUNTIME and hasattr(conn, "agent_orchestrator") and conn.agent_orchestrator:
        have_voice = conn.vad.is_vad(conn, audio)

        if hasattr(conn, "just_woken_up") and conn.just_woken_up:
            have_voice = False
            if not hasattr(conn, "vad_resume_task") or conn.vad_resume_task.done():
                conn.vad_resume_task = asyncio.create_task(resume_vad_detection(conn))
            return

        # Agent runtime handles barge-in via InterruptSkill (no legacy _handle_barge_in)
        # Skip orchestrator during TTS if voice barge-in is disabled (button-only mode)
        if conn.config.get("enable_voice_barge_in", True) or not conn.client_is_speaking:
            await conn.agent_orchestrator.process_frame(conn, audio)

        await no_voice_close_connect(conn, have_voice)
        await conn.asr.receive_audio(conn, audio, have_voice)
        return

    # ── Legacy path ──────────────────────────────────────────────────────
    # During active TTS without echo detection, throttle at the top level
    # to avoid VAD + spectral analysis on every frame (reduces event-loop load).
    if conn.client_is_speaking and conn.client_listen_mode != "manual":
        tts_emb = getattr(conn, "tts_reference_embedding", None)
        vp = getattr(conn, "voiceprint_provider", None)
        if not (tts_emb is not None and vp and vp.enabled):
            throttle = getattr(conn, "_audio_msg_throttle", 0) + 1
            conn._audio_msg_throttle = throttle
            if throttle % TTS_THROTTLE_SKIP_FRAMES != 0:
                return
    else:
        conn._audio_msg_throttle = 0

    have_voice = conn.vad.is_vad(conn, audio)

    if hasattr(conn, "just_woken_up") and conn.just_woken_up:
        have_voice = False
        if not hasattr(conn, "vad_resume_task") or conn.vad_resume_task.done():
            conn.vad_resume_task = asyncio.create_task(resume_vad_detection(conn))
        return

    if conn.client_is_speaking and conn.client_listen_mode != "manual":
        if conn.config.get("enable_voice_barge_in", True):
            await _handle_barge_in(conn, audio, have_voice)

    await no_voice_close_connect(conn, have_voice)
    await conn.asr.receive_audio(conn, audio, have_voice)


async def _handle_barge_in(conn: "ConnectionHandler", audio: bytes, have_voice: bool):
    """Spectral-aware barge-in with adaptive thresholds and pre-roll buffer.

    Flow:
      1. Accumulate audio into pre-roll ring buffer (preserves speech onset).
      2. Adaptive post-TTS cooldown (short if echo detection is ready).
      3. Per-frame spectral classification (echo / human / ambiguous).
      4. Dynamic Stage 1 threshold based on spectral vote.
      5. Stage 2: embedding echo check (only for ambiguous frames) or fast accept.
      6. FORCE_BARGE_IN safety net unchanged.
      7. On acceptance: prepend pre-roll buffer to ASR to recover truncated beginning.
    """
    # Accumulate all incoming audio into a pre-roll ring buffer.
    # When barge-in is confirmed, this buffer is prepended to asr_audio
    # so the beginning of the user's utterance is not lost.
    pre_roll = getattr(conn, "_barge_in_pre_roll", [])
    pre_roll.append(audio)
    if len(pre_roll) > PRE_ROLL_FRAMES:
        pre_roll = pre_roll[-PRE_ROLL_FRAMES:]
    conn._barge_in_pre_roll = pre_roll

    counter = getattr(conn, "_barge_in_counter", 0)
    echo_buf = getattr(conn, "_echo_check_buffer", [])
    cooldown_until = getattr(conn, "_echo_cooldown_until", 0.0)
    sustained = getattr(conn, "_sustained_voice_frames", 0)
    no_voice_streak = getattr(conn, "_barge_in_no_voice_streak", 0)
    human_votes = getattr(conn, "_spectral_human_votes", 0)
    echo_votes = getattr(conn, "_spectral_echo_votes", 0)

    # Adaptive post-TTS cooldown
    barge_in_active = getattr(conn, "_barge_in_active", False)
    tts_stop_time = getattr(conn, "tts_last_stop_time", 0.0)
    tts_emb = getattr(conn, "tts_reference_embedding", None)
    vp = getattr(conn, "voiceprint_provider", None)
    has_echo_detection = (tts_emb is not None and vp and vp.enabled)

    cooldown_s = conn.config.get("post_tts_cooldown_s", POST_TTS_COOLDOWN_SHORT_S if has_echo_detection else POST_TTS_COOLDOWN_LONG_S)
    if not barge_in_active and tts_stop_time > 0 and (time.monotonic() - tts_stop_time) < cooldown_s:
        return

    if not have_voice:
        no_voice_streak += 1
        conn._barge_in_no_voice_streak = no_voice_streak

        if no_voice_streak > GRACE_PERIOD_FRAMES:
            if counter > 0 or sustained > 0:
                logger.bind(tag=TAG).debug(
                    f"[BARGE_IN] Reset: no_voice_streak={no_voice_streak} "
                    f"(had counter={counter}, sustained={sustained})"
                )
            _reset_barge_in_state(conn)
        return

    conn._barge_in_no_voice_streak = 0

    # Spectral classification of current frame
    classification = _classify_frame(audio, conn)

    if classification == "echo":
        echo_votes += 1
    elif classification == "human":
        human_votes += 1
    conn._spectral_human_votes = human_votes
    conn._spectral_echo_votes = echo_votes

    sustained += 1
    conn._sustained_voice_frames = sustained

    # Force barge-in safety net
    if sustained >= FORCE_BARGE_IN_FRAMES:
        # Without echo detection, require simple majority of human votes.
        if not has_echo_detection and human_votes < sustained * 0.6:
            if sustained < FORCE_BARGE_IN_FRAMES + 5:
                return
        logger.bind(tag=TAG).info(
            f"[BARGE_IN] Force accepted (sustained={sustained} frames "
            f"~{sustained * 60}ms, human_votes={human_votes}, echo_votes={echo_votes})"
        )
        pre_roll_audio = list(conn._barge_in_pre_roll)
        _reset_barge_in_state(conn)
        await handleAbortMessage(conn)
        conn.asr_audio.extend(pre_roll_audio)
        return

    if time.monotonic() < cooldown_until:
        return

    counter += 1
    conn._barge_in_counter = counter

    # Dynamic Stage 1 threshold based on spectral votes
    total_votes = human_votes + echo_votes
    if total_votes > 0 and human_votes > echo_votes * 2:
        required_frames = BARGE_IN_FAST_FRAMES
    elif total_votes > 0 and echo_votes > human_votes * 2:
        required_frames = BARGE_IN_SLOW_FRAMES
    else:
        required_frames = BARGE_IN_CONSECUTIVE_FRAMES

    if counter < required_frames:
        return

    # Stage 2: decide based on spectral confidence + embedding
    if has_echo_detection:
        # Strong human signal → accept immediately, no embedding check needed
        if total_votes >= 3 and human_votes >= total_votes * 0.7:
            logger.bind(tag=TAG).info(
                f"[BARGE_IN] Fast accepted (spectral: human={human_votes}/{total_votes}, "
                f"rms/flatness confirmed human) after {counter} frames ~{counter * 60}ms"
            )
            pre_roll_audio = list(conn._barge_in_pre_roll)
            _reset_barge_in_state(conn)
            await handleAbortMessage(conn)
            conn.asr_audio.extend(pre_roll_audio)
            return

        # Strong echo signal → reject without embedding check
        if total_votes >= 3 and echo_votes >= total_votes * 0.8:
            conn._echo_cooldown_until = time.monotonic() + ECHO_REJECT_COOLDOWN_S
            logger.bind(tag=TAG).info(
                f"[BARGE_IN] Fast rejected (spectral: echo={echo_votes}/{total_votes}) "
                f"after {counter} frames ~{counter * 60}ms"
            )
            conn._barge_in_counter = 0
            conn._echo_check_buffer = []
            return

        # Ambiguous → fall through to embedding echo check
        echo_buf.append(audio)
        conn._echo_check_buffer = echo_buf

        if len(echo_buf) < ECHO_CHECK_BUFFER_FRAMES:
            return

        conn._barge_in_counter = 0
        conn._echo_check_buffer = []

        is_echo, score = await _check_echo_with_timeout(conn, echo_buf, tts_emb, vp)
        if is_echo:
            conn._echo_cooldown_until = time.monotonic() + ECHO_REJECT_COOLDOWN_S
            logger.bind(tag=TAG).info(
                f"[BARGE_IN] Rejected (embedding echo): score={score:.3f} "
                f">= {ECHO_SIMILARITY_THRESHOLD} "
                f"(spectral: human={human_votes}, echo={echo_votes}, sustained={sustained})"
            )
            return

        logger.bind(tag=TAG).info(
            f"[BARGE_IN] Accepted (embedding confirmed human): score={score:.3f} "
            f"< {ECHO_SIMILARITY_THRESHOLD} "
            f"(spectral: human={human_votes}, echo={echo_votes})"
        )
        pre_roll_audio = list(conn._barge_in_pre_roll)
        _reset_barge_in_state(conn)
        await handleAbortMessage(conn)
        conn.asr_audio.extend(pre_roll_audio)
    else:
        # No embedding available — use spectral + frame count
        if counter >= BARGE_IN_NO_EMBEDDING_FRAMES:
            # Accept if human votes show clear majority.
            # Relaxed from supermajority to simple majority for responsiveness.
            if human_votes < 2 or human_votes < echo_votes * 2:
                if counter < BARGE_IN_NO_EMBEDDING_FRAMES + 4:
                    return
            logger.bind(tag=TAG).info(
                f"[BARGE_IN] Accepted (no embedding, frame+spectral) "
                f"after {counter} frames ~{counter * 60}ms "
                f"(spectral: human={human_votes}, echo={echo_votes})"
            )
            pre_roll_audio = list(conn._barge_in_pre_roll)
            _reset_barge_in_state(conn)
            await handleAbortMessage(conn)
            conn.asr_audio.extend(pre_roll_audio)


def _reset_barge_in_state(conn):
    """Reset all barge-in tracking state."""
    conn._barge_in_counter = 0
    conn._echo_check_buffer = []
    conn._sustained_voice_frames = 0
    conn._echo_cooldown_until = 0.0
    conn._barge_in_no_voice_streak = 0
    conn._spectral_human_votes = 0
    conn._spectral_echo_votes = 0
    conn._barge_in_pre_roll = []


async def _check_echo_with_timeout(conn, opus_packets, tts_embedding, vp) -> tuple:
    """Run echo check with a timeout. If voiceprint service is slow, assume not echo
    (let the user through rather than blocking indefinitely)."""
    try:
        result = await asyncio.wait_for(
            _check_echo(conn, opus_packets, tts_embedding, vp),
            timeout=ECHO_CHECK_TIMEOUT_S,
        )
        return result
    except asyncio.TimeoutError:
        logger.bind(tag=TAG).warning(
            f"[ECHO_CHECK] Timed out after {ECHO_CHECK_TIMEOUT_S}s — assuming real speech"
        )
        return False, 0.0


async def _check_echo(conn, opus_packets, tts_embedding, vp) -> tuple:
    """Decode opus buffer -> WAV -> extract embedding -> compare with TTS."""
    try:
        decoder = opuslib_next.Decoder(16000, 1)
        pcm_frames = []
        for pkt in opus_packets:
            if pkt and len(pkt) > 0:
                pcm = decoder.decode(pkt, 960)
                if pcm:
                    pcm_frames.append(pcm)
        del decoder

        if not pcm_frames:
            if conn.client_is_speaking:
                return True, 1.0
            return False, 0.0

        pcm_data = b"".join(pcm_frames)
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(pcm_data)
        wav_buf.seek(0)
        wav_data = wav_buf.read()

        mic_embedding = await vp.extract_embedding(wav_data)
        if mic_embedding is None:
            if conn.client_is_speaking:
                logger.bind(tag=TAG).warning(
                    "[ECHO_CHECK] Embedding extraction failed during TTS playback — assuming echo"
                )
                return True, 1.0
            return False, 0.0

        score = vp.cosine_similarity(mic_embedding, tts_embedding)
        return score >= ECHO_SIMILARITY_THRESHOLD, score

    except Exception as e:
        logger.bind(tag=TAG).error(f"[ECHO_CHECK] failed: {e}")
        if conn.client_is_speaking:
            logger.bind(tag=TAG).warning(
                "[ECHO_CHECK] Exception during TTS playback — assuming echo"
            )
            return True, 1.0
        return False, 0.0


async def resume_vad_detection(conn: "ConnectionHandler"):
    suppress_s = conn.config.get("post_wakeup_suppress_s", 2.0)
    await asyncio.sleep(suppress_s)
    conn.just_woken_up = False


async def startToChat(conn: "ConnectionHandler", text):
    # 检查输入是否是JSON格式（包含说话人信息）
    speaker_name = None
    language_tag = None
    actual_text = text

    try:
        # 尝试解析JSON格式的输入
        if text.strip().startswith("{") and text.strip().endswith("}"):
            data = json.loads(text)
            if "speaker" in data and "content" in data:
                speaker_name = data["speaker"]
                language_tag = data["language"]
                actual_text = data["content"]
                conn.logger.bind(tag=TAG).info(f"Parsed speaker: {speaker_name}")

                # 直接使用JSON格式的文本，不解析
                actual_text = text
    except (json.JSONDecodeError, KeyError):
        # 如果解析失败，继续使用原始文本
        pass

    # 保存说话人信息到连接对象
    if speaker_name:
        conn.current_speaker = speaker_name
    else:
        conn.current_speaker = None

    if conn.need_bind:
        await check_bind_device(conn)
        return

    # 如果当日的输出字数大于限定的字数
    if conn.max_output_size > 0:
        if check_device_output_limit(
            conn.headers.get("device-id"), conn.max_output_size
        ):
            await max_out_size(conn)
            return
    # manual 模式下不打断正在播放的内容
    if conn.client_is_speaking and conn.client_listen_mode != "manual":
        await handleAbortMessage(conn)

    # 首先进行意图分析，使用实际文本内容
    intent_handled = await handle_user_intent(conn, actual_text)

    if intent_handled:
        # 如果意图已被处理，不再进行聊天
        return

    # 意图未被处理，继续常规聊天流程，使用实际文本内容
    await send_stt_message(conn, actual_text)
    conn.executor.submit(conn.chat, actual_text)


async def no_voice_close_connect(conn: "ConnectionHandler", have_voice):
    if have_voice:
        conn.last_activity_time = time.time() * 1000
        return
    # 只有在已经初始化过时间戳的情况下才进行超时检查
    if conn.last_activity_time > 0.0:
        no_voice_time = time.time() * 1000 - conn.last_activity_time
        close_connection_no_voice_time = int(
            conn.config.get("close_connection_no_voice_time", 120)
        )
        if (
            not conn.close_after_chat
            and no_voice_time > 1000 * close_connection_no_voice_time
        ):
            conn.close_after_chat = True
            conn.client_abort = False
            end_prompt = conn.config.get("end_prompt", {})
            if end_prompt and end_prompt.get("enable", True) is False:
                conn.logger.bind(tag=TAG).info("Dialogue ended; no closing prompt needed")
                await conn.close()
                return
            prompt = end_prompt.get("prompt")
            if not prompt:
                prompt = "请你以```时间过得真快```未来头，用富有感情、依依不舍的话来结束这场对话吧。！"
            await startToChat(conn, prompt)


async def max_out_size(conn: "ConnectionHandler"):
    # 播放超出最大输出字数的提示
    conn.client_abort = False
    text = "不好意思，我现在有点事情要忙，明天这个时候我们再聊，约好了哦！明天不见不散，拜拜！"
    await send_stt_message(conn, text)
    file_path = "config/assets/max_output_size.wav"
    opus_packets = await audio_to_data(file_path)
    conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
    conn.close_after_chat = True


async def check_bind_device(conn: "ConnectionHandler"):
    if conn.bind_code:
        # 确保bind_code是6位数字
        if len(conn.bind_code) != 6:
            conn.logger.bind(tag=TAG).error(f"Invalid bind code format: {conn.bind_code}")
            text = "绑定码格式错误，请检查配置。"
            await send_stt_message(conn, text)
            return

        text = f"请登录控制面板，输入{conn.bind_code}，绑定设备。"
        await send_stt_message(conn, text)

        # 播放提示音
        music_path = "config/assets/bind_code.wav"
        opus_packets = await audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.FIRST, opus_packets, text))

        # 逐个播放数字
        for i in range(6):  # 确保只播放6位数字
            try:
                digit = conn.bind_code[i]
                num_path = f"config/assets/bind_code/{digit}.wav"
                num_packets = await audio_to_data(num_path)
                conn.tts.tts_audio_queue.put((SentenceType.MIDDLE, num_packets, None))
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"Failed to play digit audio: {e}")
                continue
        conn.tts.tts_audio_queue.put((SentenceType.LAST, [], None))
    else:
        # 播放未绑定提示
        conn.client_abort = False
        text = f"没有找到该设备的版本信息，请正确配置 OTA地址，然后重新编译固件。"
        await send_stt_message(conn, text)
        music_path = "config/assets/bind_not_found.wav"
        opus_packets = await audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
