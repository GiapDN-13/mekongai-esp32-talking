import os
import asyncio
import time
import aiohttp
import requests
import numpy as np
from collections import deque
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Tuple, List
from config.logger import setup_logging
from core.utils.cache.manager import cache_manager
from core.utils.cache.config import CacheType

TAG = __name__
logger = setup_logging()

_VP_LAT_MS = deque(maxlen=200)
_VP_SCORES = deque(maxlen=200)
_VP_HITS = deque(maxlen=200)


def _percentile(values, p: float) -> float:
    if not values:
        return 0.0
    arr = sorted(values)
    n = len(arr)
    if n == 1:
        return float(arr[0])
    rank = (p / 100.0) * (n - 1)
    lo = int(rank)
    hi = min(lo + 1, n - 1)
    frac = rank - lo
    return float(arr[lo] * (1.0 - frac) + arr[hi] * frac)


class VoiceprintProvider:

    def __init__(self, config: dict):
        self.original_url = config.get("url", "")
        self.speakers = config.get("speakers", [])
        self.speaker_map = self._parse_speakers()
        self.similarity_threshold = float(config.get("similarity_threshold", 0.45))

        self.api_url = None
        self.api_key = None
        self.speaker_ids = []

        if not self.original_url:
            logger.bind(tag=TAG).warning("Voiceprint URL not configured; voiceprint disabled")
            self.enabled = False
        else:
            parsed_url = urlparse(self.original_url)
            self._base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            query_params = parse_qs(parsed_url.query)
            self.api_key = query_params.get('key', [''])[0]

            if not self.api_key:
                self.api_key = os.environ.get("VOICEPRINT_API_KEY", "voiceprint-secret-key")
                logger.bind(tag=TAG).info(
                    "No key in URL; using env/default API key for local voiceprint service"
                )

            self.api_url = f"{self._base_url}/voiceprint/identify"

            for speaker_str in self.speakers:
                try:
                    parts = speaker_str.split(",", 2)
                    if len(parts) >= 1:
                        self.speaker_ids.append(parts[0].strip())
                except Exception:
                    continue

            if not self.speaker_ids:
                if self._check_server_health():
                    self.enabled = True
                    logger.bind(tag=TAG).info(
                        f"Voiceprint enabled (no speakers yet, enrollment mode): API={self.api_url}"
                    )
                else:
                    self.enabled = False
                    logger.bind(tag=TAG).warning("Voiceprint server unavailable; disabled")
            else:
                if self._check_server_health():
                    self.enabled = True
                    logger.bind(tag=TAG).info(
                        f"Voiceprint enabled: API={self.api_url}, "
                        f"speakers={len(self.speaker_ids)}, "
                        f"threshold={self.similarity_threshold}"
                    )
                else:
                    self.enabled = False
                    logger.bind(tag=TAG).warning(f"Voiceprint server unavailable; disabled")

    def _parse_speakers(self) -> Dict[str, Dict[str, str]]:
        speaker_map = {}
        for speaker_str in self.speakers:
            try:
                parts = speaker_str.split(",", 2)
                if len(parts) >= 3:
                    sid, name, desc = parts[0].strip(), parts[1].strip(), parts[2].strip()
                    speaker_map[sid] = {"name": name, "description": desc}
            except Exception as e:
                logger.bind(tag=TAG).warning(f"Failed to parse speaker config: {speaker_str}: {e}")
        return speaker_map

    def _check_server_health(self) -> bool:
        if not self._base_url or not self.api_key:
            return False

        cache_key = f"{self._base_url}:{self.api_key}"
        cached_result = cache_manager.get(CacheType.VOICEPRINT_HEALTH, cache_key)
        if cached_result is not None:
            return cached_result

        try:
            health_url = f"{self._base_url}/voiceprint/health?key={self.api_key}"
            t0 = time.perf_counter()
            response = requests.get(health_url, timeout=3)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            if response.status_code == 200:
                result = response.json()
                is_healthy = result.get("status") == "healthy"
                logger.bind(tag=TAG).info(
                    f"[VP_HEALTH] status={'ok' if is_healthy else 'unhealthy'} "
                    f"response_ms={elapsed_ms:.1f} "
                    f"model={result.get('model', '?')} "
                    f"speakers_registered={result.get('speakers_registered', '?')}"
                )
            else:
                logger.bind(tag=TAG).warning(f"[VP_HEALTH] HTTP {response.status_code}")
                is_healthy = False

        except requests.exceptions.ConnectTimeout:
            logger.bind(tag=TAG).warning("[VP_HEALTH] connection timed out")
            is_healthy = False
        except requests.exceptions.ConnectionError:
            logger.bind(tag=TAG).warning("[VP_HEALTH] connection refused")
            is_healthy = False
        except Exception as e:
            logger.bind(tag=TAG).warning(f"[VP_HEALTH] error: {e}")
            is_healthy = False

        cache_manager.set(CacheType.VOICEPRINT_HEALTH, cache_key, is_healthy)
        return is_healthy

    async def identify_speaker(
        self, audio_data: bytes, session_id: str
    ) -> Optional[Tuple[str, float]]:
        """Identify speaker. Returns (speaker_name, confidence_score) or None."""
        if not self.enabled or not self.api_url or not self.api_key:
            return None

        t0 = time.monotonic()

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json',
            }

            data = aiohttp.FormData()
            data.add_field('speaker_ids', ','.join(self.speaker_ids))
            data.add_field('file', audio_data, filename='audio.wav', content_type='audio/wav')

            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.api_url, headers=headers, data=data) as response:

                    elapsed_ms = (time.monotonic() - t0) * 1000

                    if response.status != 200:
                        body = await response.text()
                        logger.bind(tag=TAG).error(
                            f"[VP_ERROR] session={session_id} HTTP {response.status} "
                            f"body={body[:200]} latency_ms={elapsed_ms:.1f}"
                        )
                        return None

                    result = await response.json()
                    speaker_id = result.get("speaker_id")
                    score = result.get("score", 0)
                    all_scores = result.get("all_scores", {})

                    _VP_LAT_MS.append(elapsed_ms)
                    _VP_SCORES.append(score)

                    if score < self.similarity_threshold:
                        _VP_HITS.append(0)
                        logger.bind(tag=TAG).info(
                            f"[VP] session={session_id} speaker=Stranger "
                            f"confidence={score:.3f} below_threshold={self.similarity_threshold} "
                            f"latency_ms={elapsed_ms:.1f}"
                        )
                        self._log_rolling_metrics()
                        return ("Người lạ", score)

                    if speaker_id and speaker_id in self.speaker_map:
                        name = self.speaker_map[speaker_id]["name"]
                        _VP_HITS.append(1)
                        logger.bind(tag=TAG).info(
                            f"[VP] session={session_id} speaker={name} "
                            f"confidence={score:.3f} "
                            f"latency_ms={elapsed_ms:.1f}"
                        )
                        self._log_rolling_metrics()
                        return (name, score)
                    else:
                        _VP_HITS.append(0)
                        logger.bind(tag=TAG).warning(
                            f"[VP] session={session_id} speaker_id={speaker_id} "
                            f"not_in_config confidence={score:.3f} "
                            f"latency_ms={elapsed_ms:.1f}"
                        )
                        self._log_rolling_metrics()
                        return ("Người lạ", score)

        except asyncio.TimeoutError:
            elapsed_ms = (time.monotonic() - t0) * 1000
            logger.bind(tag=TAG).error(
                f"[VP_ERROR] session={session_id} error=Timeout latency_ms={elapsed_ms:.1f}"
            )
            return None
        except Exception as e:
            elapsed_ms = (time.monotonic() - t0) * 1000
            logger.bind(tag=TAG).error(
                f"[VP_ERROR] session={session_id} error={type(e).__name__}:{e} "
                f"latency_ms={elapsed_ms:.1f}"
            )
            return None

    def _log_rolling_metrics(self):
        if len(_VP_LAT_MS) > 0 and len(_VP_LAT_MS) % 50 == 0:
            hit_rate = sum(_VP_HITS) / len(_VP_HITS) * 100 if _VP_HITS else 0
            logger.bind(tag=TAG).info(
                f"[VP_METRICS] n={len(_VP_LAT_MS)} "
                f"latency_p50={_percentile(_VP_LAT_MS, 50):.1f}ms "
                f"latency_p95={_percentile(_VP_LAT_MS, 95):.1f}ms "
                f"score_p50={_percentile(_VP_SCORES, 50):.3f} "
                f"score_p95={_percentile(_VP_SCORES, 95):.3f} "
                f"hit_rate={hit_rate:.1f}%"
            )

    async def register_speaker(self, speaker_id: str, name: str, wav_data: bytes) -> bool:
        """Register a new speaker via the voiceprint microservice."""
        if not self._base_url or not self.api_key:
            return False

        try:
            register_url = f"{self._base_url}/voiceprint/register"

            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = aiohttp.FormData()
            data.add_field("speaker_id", speaker_id)
            data.add_field("file", wav_data, filename="enroll.wav", content_type="audio/wav")

            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(register_url, headers=headers, data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.bind(tag=TAG).info(
                            f"[VP_REGISTER] speaker={speaker_id} name={name} status=ok"
                        )
                        return True
                    else:
                        body = await resp.text()
                        logger.bind(tag=TAG).error(
                            f"[VP_REGISTER] speaker={speaker_id} HTTP {resp.status}: {body}"
                        )
                        return False
        except Exception as e:
            logger.bind(tag=TAG).error(f"[VP_REGISTER] error: {e}")
            return False

    def add_speaker(self, speaker_id: str, name: str, description: str):
        """Add a speaker to the in-memory speaker map and ID list (after successful registration)."""
        self.speaker_map[speaker_id] = {"name": name, "description": description}
        if speaker_id not in self.speaker_ids:
            self.speaker_ids.append(speaker_id)
        self.speakers.append(f"{speaker_id},{name},{description}")
        self.enabled = True
        logger.bind(tag=TAG).info(f"[VP_ADD] speaker={speaker_id} name={name} total={len(self.speaker_ids)}")

    # ── TTS Echo Detection ──────────────────────────────────────────

    async def extract_embedding(self, wav_data: bytes) -> Optional[np.ndarray]:
        """Call voiceprint service to extract an embedding vector from audio."""
        if not self._base_url or not self.api_key:
            return None

        try:
            url = f"{self._base_url}/voiceprint/extract-embedding"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = aiohttp.FormData()
            data.add_field("file", wav_data, filename="audio.wav", content_type="audio/wav")

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, data=data) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.bind(tag=TAG).error(f"[VP_EXTRACT] HTTP {resp.status}: {body[:200]}")
                        return None
                    result = await resp.json()
                    emb_list = result.get("embedding")
                    if emb_list:
                        return np.array(emb_list, dtype=np.float32)
                    return None
        except Exception as e:
            logger.bind(tag=TAG).error(f"[VP_EXTRACT] error: {e}")
            return None

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two embedding vectors."""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    async def is_tts_echo(
        self, wav_data: bytes, tts_embedding: np.ndarray, echo_threshold: float = 0.55
    ) -> Tuple[bool, float]:
        """Check whether audio is TTS echo by comparing against TTS embedding.

        Returns (is_echo, similarity_score).
        """
        mic_embedding = await self.extract_embedding(wav_data)
        if mic_embedding is None:
            return False, 0.0

        score = self.cosine_similarity(mic_embedding, tts_embedding)
        is_echo = score >= echo_threshold
        logger.bind(tag=TAG).debug(
            f"[ECHO_CHECK] similarity={score:.3f} threshold={echo_threshold} "
            f"is_echo={is_echo}"
        )
        return is_echo, score
