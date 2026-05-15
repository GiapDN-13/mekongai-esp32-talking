import os
import re
import time
import random
import difflib
import traceback
from pathlib import Path
from core.handle.sendAudioHandle import send_stt_message
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.utils.dialogue import Message
from core.providers.tts.dto.dto import TTSMessageDTO, SentenceType, ContentType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__

MUSIC_CACHE = {}

play_music_function_desc = {
    "type": "function",
    "function": {
        "name": "play_music",
        "description": (
            "Phát nhạc khi người dùng yêu cầu nghe nhạc, hát, bật nhạc. "
            "Ví dụ: 'bật nhạc đi', 'phát bài Trống Cơm', 'nghe nhạc thư giãn'. "
            "Tool này phát nhạc local nếu có, hoặc gợi ý dùng Zing MP3/SoundCloud nếu không có."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "song_name": {
                    "type": "string",
                    "description": "Tên bài hát. Dùng 'random' nếu không chỉ định cụ thể.",
                }
            },
            "required": ["song_name"],
        },
    },
}


@register_function("play_music", play_music_function_desc, ToolType.SYSTEM_CTL)
def play_music(conn: "ConnectionHandler", song_name: str = "random"):
    try:
        cache = initialize_music_handler(conn)

        if not cache.get("music_files"):
            return _delegate_to_online(conn, song_name)

        if song_name and song_name != "random":
            best = _find_best_match(song_name, cache["music_files"])
            if not best:
                return _delegate_to_online(conn, song_name)

        if not conn.loop or not conn.loop.is_running():
            return ActionResponse(
                action=Action.RESPONSE,
                result="error",
                response="Hệ thống đang bận, quý vị thử lại sau nha!",
            )

        music_intent = (
            f"Phát nhạc {song_name}" if song_name != "random" else "Phát nhạc ngẫu nhiên"
        )

        task = conn.loop.create_task(handle_music_command(conn, music_intent))
        task.add_done_callback(lambda f: _log_done(conn, f))

        return ActionResponse(
            action=Action.NONE, result="playing", response="Đang phát nhạc cho quý vị nha!"
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Lỗi xử lý phát nhạc: {e}")
        return ActionResponse(
            action=Action.RESPONSE,
            result=str(e),
            response="Có lỗi khi phát nhạc, quý vị thử lại sau nha!",
        )


def _delegate_to_online(conn, song_name):
    """Không có nhạc local → hướng dẫn LLM dùng Zing MP3 / SoundCloud trên device."""
    has_device_mcp = hasattr(conn, "mcp_client") and conn.mcp_client

    if has_device_mcp:
        if song_name and song_name != "random":
            hint = (
                f"Không có bài '{song_name}' trong thư mục nhạc local. "
                f"Hãy gọi tool self_zing_play với song_name=\"{song_name}\" "
                f"để phát từ Zing MP3 online."
            )
        else:
            hint = (
                "Không có nhạc local. "
                "Hãy gọi tool self_zing_play với song_name=\"nhạc không lời\" "
                "để phát nhạc online từ Zing MP3."
            )
        return ActionResponse(action=Action.REQLLM, result=hint, response=None)
    else:
        return ActionResponse(
            action=Action.RESPONSE,
            result="no_music",
            response="Hiện tại chưa có bài nhạc nào. Quý vị thử yêu cầu phát từ Zing MP3 hoặc SoundCloud nha!",
        )


def _log_done(conn, f):
    try:
        f.result()
        conn.logger.bind(tag=TAG).info("Phát nhạc xong")
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Lỗi phát nhạc: {e}")


def _extract_song_name(text):
    for keyword in ["phát nhạc", "bật nhạc", "nghe nhạc", "mở nhạc", "hát bài"]:
        if keyword in text.lower():
            parts = text.lower().split(keyword)
            if len(parts) > 1 and parts[1].strip():
                return parts[1].strip()
    return None


def _find_best_match(potential_song, music_files):
    best_match = None
    highest_ratio = 0
    for music_file in music_files:
        song_name = os.path.splitext(music_file)[0]
        ratio = difflib.SequenceMatcher(None, potential_song.lower(), song_name.lower()).ratio()
        if ratio > highest_ratio and ratio > 0.4:
            highest_ratio = ratio
            best_match = music_file
    return best_match


def get_music_files(music_dir, music_ext):
    music_dir = Path(music_dir)
    music_files = []
    if not music_dir.exists():
        return music_files, []
    music_file_names = []
    for file in music_dir.rglob("*"):
        if file.is_file() and file.suffix.lower() in music_ext:
            rel = str(file.relative_to(music_dir))
            music_files.append(rel)
            music_file_names.append(os.path.splitext(rel)[0])
    return music_files, music_file_names


def initialize_music_handler(conn: "ConnectionHandler"):
    global MUSIC_CACHE
    if not MUSIC_CACHE:
        plugins_config = conn.config.get("plugins", {})
        music_cfg = plugins_config.get("play_music", {})
        if isinstance(music_cfg, str):
            import json
            try:
                music_cfg = json.loads(music_cfg)
            except Exception:
                music_cfg = {}

        MUSIC_CACHE["music_dir"] = os.path.abspath(music_cfg.get("music_dir", "./music"))
        MUSIC_CACHE["music_ext"] = tuple(music_cfg.get("music_ext", (".mp3", ".wav", ".p3")))
        MUSIC_CACHE["refresh_time"] = music_cfg.get("refresh_time", 60)
        MUSIC_CACHE["music_files"], MUSIC_CACHE["music_file_names"] = get_music_files(
            MUSIC_CACHE["music_dir"], MUSIC_CACHE["music_ext"]
        )
        MUSIC_CACHE["scan_time"] = time.time()
    return MUSIC_CACHE


async def handle_music_command(conn: "ConnectionHandler", text):
    initialize_music_handler(conn)
    global MUSIC_CACHE

    clean_text = re.sub(r"[^\w\s]", "", text).strip()
    conn.logger.bind(tag=TAG).debug(f"Music command: {clean_text}")

    if os.path.exists(MUSIC_CACHE["music_dir"]):
        if time.time() - MUSIC_CACHE["scan_time"] > MUSIC_CACHE["refresh_time"]:
            MUSIC_CACHE["music_files"], MUSIC_CACHE["music_file_names"] = (
                get_music_files(MUSIC_CACHE["music_dir"], MUSIC_CACHE["music_ext"])
            )
            MUSIC_CACHE["scan_time"] = time.time()

        potential_song = _extract_song_name(clean_text)
        if potential_song:
            best_match = _find_best_match(potential_song, MUSIC_CACHE["music_files"])
            if best_match:
                conn.logger.bind(tag=TAG).info(f"Bài khớp nhất: {best_match}")
                await play_local_music(conn, specific_file=best_match)
                return True

    await play_local_music(conn)
    return True


def _get_random_play_prompt(song_name):
    clean_name = os.path.splitext(song_name)[0]
    prompts = [
        f"Đang phát bài {clean_name} cho quý vị nha",
        f"Mời quý vị thưởng thức bài {clean_name}",
        f"Bài tiếp theo là {clean_name} nhé",
        f"Cùng nghe bài {clean_name} nào quý vị ơi",
    ]
    return random.choice(prompts)


async def play_local_music(conn: "ConnectionHandler", specific_file=None):
    global MUSIC_CACHE
    try:
        if not os.path.exists(MUSIC_CACHE["music_dir"]):
            conn.logger.bind(tag=TAG).error(f"Thư mục nhạc không tồn tại: {MUSIC_CACHE['music_dir']}")
            return

        if specific_file:
            selected_music = specific_file
            music_path = os.path.join(MUSIC_CACHE["music_dir"], specific_file)
        else:
            if not MUSIC_CACHE["music_files"]:
                conn.logger.bind(tag=TAG).error("Không tìm thấy file nhạc nào")
                return
            selected_music = random.choice(MUSIC_CACHE["music_files"])
            music_path = os.path.join(MUSIC_CACHE["music_dir"], selected_music)

        if not os.path.exists(music_path):
            conn.logger.bind(tag=TAG).error(f"File nhạc không tồn tại: {music_path}")
            return

        text = _get_random_play_prompt(selected_music)
        await send_stt_message(conn, text)
        conn.dialogue.put(Message(role="assistant", content=text))

        if conn.intent_type == "intent_llm":
            conn.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=conn.sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                )
            )
        conn.tts.tts_text_queue.put(
            TTSMessageDTO(
                sentence_id=conn.sentence_id,
                sentence_type=SentenceType.MIDDLE,
                content_type=ContentType.TEXT,
                content_detail=text,
            )
        )
        conn.tts.tts_text_queue.put(
            TTSMessageDTO(
                sentence_id=conn.sentence_id,
                sentence_type=SentenceType.MIDDLE,
                content_type=ContentType.FILE,
                content_file=music_path,
            )
        )
        if conn.intent_type == "intent_llm":
            conn.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=conn.sentence_id,
                    sentence_type=SentenceType.LAST,
                    content_type=ContentType.ACTION,
                )
            )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Lỗi phát nhạc: {str(e)}")
        conn.logger.bind(tag=TAG).error(f"Chi tiết: {traceback.format_exc()}")
