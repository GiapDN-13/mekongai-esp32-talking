"""
Voiceprint Recognition Microservice
====================================
FastAPI service providing speaker registration, identification, and management.
Uses CAM++ (3D-Speaker) for speaker embedding extraction and cosine similarity matching.
Model is loaded via speakerlab + ModelScope snapshot_download (no heavy pipeline needed).

Endpoints:
  POST   /voiceprint/register   — Register a speaker (speaker_id + WAV file)
  POST   /voiceprint/identify   — Identify speaker from audio
  DELETE /voiceprint/{id}        — Remove a speaker registration
  GET    /voiceprint/health      — Health check with API key validation
  GET    /voiceprint/list        — List registered speakers
"""

import os
import io
import json
import time
import pathlib
import logging
import threading
from collections import deque
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import torch
import torchaudio
from fastapi import FastAPI, File, Form, UploadFile, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("voiceprint")

DATA_DIR = Path(os.getenv("VOICEPRINT_DATA_DIR", "./data/voiceprints"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv("VOICEPRINT_API_KEY", "voiceprint-secret-key")

MODEL_ID = os.getenv(
    "VOICEPRINT_MODEL_ID", "iic/speech_campplus_sv_zh-cn_16k-common"
)
LOCAL_MODEL_DIR = Path(os.getenv("VOICEPRINT_MODEL_DIR", "./pretrained_models"))

EMBEDDINGS_FILE = DATA_DIR / "embeddings.json"

EMBEDDING_DIM = 192
MIN_AUDIO_SECONDS = 0.5
SAMPLE_RATE = 16000

# CAM++ model config (from 3D-Speaker infer_sv.py)
CAMPPLUS_COMMON = {
    "obj": "speakerlab.models.campplus.DTDNN.CAMPPlus",
    "args": {"feat_dim": 80, "embedding_size": 192},
}

MODEL_CONFIGS = {
    "iic/speech_campplus_sv_zh-cn_16k-common": {
        "revision": "v1.0.0",
        "model": CAMPPLUS_COMMON,
        "model_pt": "campplus_cn_common.bin",
    },
    "iic/speech_campplus_sv_en_voxceleb_16k": {
        "revision": "v1.0.2",
        "model": {
            "obj": "speakerlab.models.campplus.DTDNN.CAMPPlus",
            "args": {"feat_dim": 80, "embedding_size": 512},
        },
        "model_pt": "campplus_voxceleb.bin",
    },
    "iic/speech_campplus_sv_zh_en_16k-common_advanced": {
        "revision": "v1.0.0",
        "model": CAMPPLUS_COMMON,
        "model_pt": "campplus_cn_en_common.pt",
    },
}

app = FastAPI(title="Voiceprint Recognition Service", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_embedding_model = None
_feature_extractor = None
_device = None
_model_lock = threading.Lock()

speaker_db: dict = {}
db_lock = threading.Lock()

_identify_latencies = deque(maxlen=200)
_identify_scores = deque(maxlen=200)
_identify_hits = deque(maxlen=200)


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


def _load_model():
    """Download model from ModelScope and load weights into CAM++ via speakerlab."""
    global _embedding_model, _feature_extractor, _device

    if _embedding_model is not None:
        return

    with _model_lock:
        if _embedding_model is not None:
            return

        t0 = time.perf_counter()
        logger.info(f"Loading CAM++ model: {MODEL_ID} ...")

        assert MODEL_ID in MODEL_CONFIGS, (
            f"Unsupported model_id: {MODEL_ID}. "
            f"Supported: {list(MODEL_CONFIGS.keys())}"
        )
        conf = MODEL_CONFIGS[MODEL_ID]

        from modelscope.hub.snapshot_download import snapshot_download
        from speakerlab.utils.builder import dynamic_import
        from speakerlab.process.processor import FBank

        cache_dir = pathlib.Path(
            snapshot_download(MODEL_ID, revision=conf["revision"])
        )
        pretrained_path = cache_dir / conf["model_pt"]
        if not pretrained_path.exists():
            save_dir = LOCAL_MODEL_DIR / MODEL_ID.split("/")[1]
            save_dir.mkdir(parents=True, exist_ok=True)
            for src in cache_dir.glob("*"):
                dst = save_dir / src.name
                try:
                    dst.unlink()
                except FileNotFoundError:
                    pass
                dst.symlink_to(src)
            pretrained_path = save_dir / conf["model_pt"]

        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        model_cls = dynamic_import(conf["model"]["obj"])
        _embedding_model = model_cls(**conf["model"]["args"])
        state_dict = torch.load(pretrained_path, map_location="cpu")
        _embedding_model.load_state_dict(state_dict)
        _embedding_model.to(_device)
        _embedding_model.eval()

        _feature_extractor = FBank(80, sample_rate=SAMPLE_RATE, mean_nor=True)

        elapsed = (time.perf_counter() - t0) * 1000
        emb_dim = conf["model"]["args"]["embedding_size"]
        logger.info(
            f"[WARMUP] model=cam++ load_time_ms={elapsed:.0f} "
            f"device={_device} embedding_dim={emb_dim}"
        )


def _load_db():
    global speaker_db
    if EMBEDDINGS_FILE.exists():
        try:
            with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            speaker_db = {
                sid: {
                    "embedding": np.array(data["embedding"], dtype=np.float32),
                    "registered_at": data.get("registered_at", ""),
                }
                for sid, data in raw.items()
            }
            logger.info(f"Loaded {len(speaker_db)} speaker embeddings from disk")
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            speaker_db = {}
    else:
        speaker_db = {}


def _save_db():
    try:
        serializable = {
            sid: {
                "embedding": data["embedding"].tolist()
                if isinstance(data["embedding"], np.ndarray)
                else data["embedding"],
                "registered_at": data.get("registered_at", ""),
            }
            for sid, data in speaker_db.items()
        }
        with open(EMBEDDINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save embeddings: {e}")


def _validate_api_key(authorization: Optional[str] = None, key: Optional[str] = None):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif key:
        token = key
    if not token or token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _read_audio(file_bytes: bytes) -> torch.Tensor:
    """Read audio bytes and return torch tensor [1, T] at 16kHz mono."""
    audio_io = io.BytesIO(file_bytes)

    try:
        wav_np, sr = sf.read(audio_io, dtype="float32")
    except Exception:
        audio_io.seek(0)
        try:
            import librosa
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
                tmp.write(audio_io.read())
                tmp_path = tmp.name
            try:
                wav_np, sr = librosa.load(tmp_path, sr=SAMPLE_RATE, mono=True)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        except Exception as e2:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Error: {e2}",
            )

    if len(wav_np.shape) > 1:
        wav_np = wav_np.mean(axis=1)

    wav = torch.tensor(wav_np, dtype=torch.float32).unsqueeze(0)

    if sr != SAMPLE_RATE:
        wav = torchaudio.functional.resample(wav, sr, SAMPLE_RATE)

    return wav


def _compute_embedding(wav: torch.Tensor) -> np.ndarray:
    """Extract embedding from audio tensor [1, T] using CAM++."""
    _load_model()
    feat = _feature_extractor(wav).unsqueeze(0).to(_device)
    with torch.no_grad():
        embedding = _embedding_model(feat).detach().squeeze(0).cpu().numpy()
    return embedding


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


@app.on_event("startup")
async def startup():
    _load_db()
    logger.info("=" * 60)
    logger.info("  VOICEPRINT SERVICE v3.0 (CAM++ / 3D-Speaker)")
    logger.info(f"  Speakers loaded: {len(speaker_db)}")
    logger.info(f"  Data dir:        {DATA_DIR}")
    logger.info(f"  Model ID:        {MODEL_ID}")
    logger.info(f"  API Key:         {API_KEY[:8]}***")
    logger.info("=" * 60)
    logger.info("Pre-loading CAM++ model (first request will be fast)...")
    _load_model()
    logger.info("Model loaded and ready.")


@app.get("/voiceprint/health")
async def health_check(key: Optional[str] = Query(None)):
    _validate_api_key(key=key)
    model_loaded = _embedding_model is not None
    return JSONResponse({
        "status": "healthy",
        "model": "cam++",
        "model_loaded": model_loaded,
        "embedding_dim": EMBEDDING_DIM,
        "speakers_registered": len(speaker_db),
        "data_dir": str(DATA_DIR),
    })


@app.post("/voiceprint/extract-embedding")
async def extract_embedding(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    """Extract and return a speaker embedding vector without registering."""
    _validate_api_key(authorization=authorization)
    t0 = time.perf_counter()

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        wav = _read_audio(file_bytes)
    except Exception as e:
        logger.error(f"[EXTRACT] Audio read failed: {e}")
        raise

    audio_duration = wav.shape[1] / SAMPLE_RATE
    if audio_duration < MIN_AUDIO_SECONDS:
        raise HTTPException(
            status_code=400,
            detail=f"Audio too short ({audio_duration:.1f}s). Need at least {MIN_AUDIO_SECONDS}s.",
        )

    try:
        embedding = _compute_embedding(wav)
    except Exception as e:
        logger.error(f"[EXTRACT] Embedding extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Embedding extraction failed")

    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        f"[EXTRACT] embedding_dim={len(embedding)} "
        f"audio_duration_s={audio_duration:.1f} latency_ms={elapsed_ms:.1f}"
    )

    return JSONResponse({
        "embedding": embedding.tolist(),
        "embedding_dim": len(embedding),
        "audio_duration_s": round(audio_duration, 2),
    })


@app.post("/voiceprint/register")
async def register_speaker(
    speaker_id: str = Form(...),
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    _validate_api_key(authorization=authorization)
    t0 = time.perf_counter()

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        wav = _read_audio(file_bytes)
    except Exception as e:
        logger.error(f"[REGISTER] Audio read failed for {speaker_id}: {e}")
        raise

    audio_duration = wav.shape[1] / SAMPLE_RATE
    if audio_duration < MIN_AUDIO_SECONDS:
        raise HTTPException(
            status_code=400,
            detail=f"Audio too short ({audio_duration:.1f}s). Need at least {MIN_AUDIO_SECONDS}s.",
        )

    try:
        embedding = _compute_embedding(wav)
    except Exception as e:
        logger.error(f"[REGISTER] Embedding extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Embedding extraction failed")

    from datetime import datetime

    with db_lock:
        speaker_db[speaker_id] = {
            "embedding": embedding,
            "registered_at": datetime.now().isoformat(),
        }
        _save_db()

    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        f"[REGISTER] speaker_id={speaker_id} embedding_dim={len(embedding)} "
        f"audio_duration_s={audio_duration:.1f} latency_ms={elapsed_ms:.1f}"
    )

    return JSONResponse({
        "success": True,
        "speaker_id": speaker_id,
        "message": f"Speaker '{speaker_id}' registered successfully",
    })


@app.post("/voiceprint/identify")
async def identify_speaker(
    speaker_ids: str = Form(...),
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    _validate_api_key(authorization=authorization)
    t0 = time.perf_counter()

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        wav = _read_audio(file_bytes)
    except Exception as e:
        logger.error(f"[IDENTIFY] Audio read failed: {e}")
        raise

    audio_duration = wav.shape[1] / SAMPLE_RATE
    if audio_duration < MIN_AUDIO_SECONDS:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.warning(
            f"[ERROR] audio_too_short duration_s={audio_duration:.2f} "
            f"min_s={MIN_AUDIO_SECONDS} latency_ms={elapsed_ms:.1f}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Audio too short ({audio_duration:.1f}s < {MIN_AUDIO_SECONDS}s minimum)",
        )

    try:
        query_embedding = _compute_embedding(wav)
    except Exception as e:
        logger.error(f"[IDENTIFY] Embedding extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Embedding extraction failed")

    candidate_ids = [sid.strip() for sid in speaker_ids.split(",") if sid.strip()]

    best_speaker_id = None
    best_score = -1.0
    scores = {}

    with db_lock:
        for sid in candidate_ids:
            if sid not in speaker_db:
                continue
            ref_embedding = speaker_db[sid]["embedding"]
            if isinstance(ref_embedding, list):
                ref_embedding = np.array(ref_embedding, dtype=np.float32)
            score = _cosine_similarity(query_embedding, ref_embedding)
            scores[sid] = round(score, 4)
            if score > best_score:
                best_score = score
                best_speaker_id = sid

    elapsed_ms = (time.perf_counter() - t0) * 1000

    _identify_latencies.append(elapsed_ms)
    _identify_scores.append(best_score)

    candidates_str = ",".join(
        f"{k}:{v}" for k, v in sorted(scores.items(), key=lambda x: -x[1])
    )
    logger.info(
        f"[IDENTIFY] result={best_speaker_id or 'None'} score={best_score:.4f} "
        f"candidates=[{candidates_str}] "
        f"latency_ms={elapsed_ms:.1f} audio_duration_s={audio_duration:.1f}"
    )

    if len(_identify_latencies) % 50 == 0 and len(_identify_latencies) > 0:
        hit_rate = (
            sum(_identify_hits) / len(_identify_hits) * 100 if _identify_hits else 0
        )
        logger.info(
            f"[METRICS] n={len(_identify_latencies)} "
            f"latency_p50={_percentile(_identify_latencies, 50):.1f}ms "
            f"latency_p95={_percentile(_identify_latencies, 95):.1f}ms "
            f"score_p50={_percentile(_identify_scores, 50):.3f} "
            f"hit_rate={hit_rate:.1f}%"
        )

    return JSONResponse({
        "speaker_id": best_speaker_id,
        "score": round(best_score, 4),
        "all_scores": scores,
    })


@app.delete("/voiceprint/{speaker_id}")
async def delete_speaker(
    speaker_id: str,
    authorization: Optional[str] = Header(None),
):
    _validate_api_key(authorization=authorization)

    with db_lock:
        if speaker_id not in speaker_db:
            return JSONResponse({
                "success": True,
                "message": f"Speaker '{speaker_id}' not found (already removed)",
            })
        del speaker_db[speaker_id]
        _save_db()

    logger.info(f"[DELETE] speaker_id={speaker_id}")

    return JSONResponse({
        "success": True,
        "message": f"Speaker '{speaker_id}' deleted successfully",
    })


@app.get("/voiceprint/list")
async def list_speakers(
    authorization: Optional[str] = Header(None),
    key: Optional[str] = Query(None),
):
    _validate_api_key(authorization=authorization, key=key)

    speakers = []
    with db_lock:
        for sid, data in speaker_db.items():
            speakers.append({
                "speaker_id": sid,
                "registered_at": data.get("registered_at", ""),
                "embedding_dim": len(data["embedding"])
                if data.get("embedding") is not None
                else 0,
            })

    return JSONResponse({"speakers": speakers, "total": len(speakers)})


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("VOICEPRINT_PORT", "8100"))
    host = os.getenv("VOICEPRINT_HOST", "0.0.0.0")
    logger.info(f"Starting Voiceprint Service on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
