import time
import wave
import os
import sys
import io
from config.logger import setup_logging
from typing import Optional, Tuple, List
from core.providers.asr.dto.dto import InterfaceType
from core.providers.asr.base import ASRProviderBase

import numpy as np
import sherpa_onnx

TAG = __name__
logger = setup_logging()


class CaptureOutput:
    def __enter__(self):
        self._output = io.StringIO()
        self._original_stdout = sys.stdout
        sys.stdout = self._output

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self._original_stdout
        self.output = self._output.getvalue()
        self._output.close()
        if self.output:
            logger.bind(tag=TAG).info(self.output.strip())


class ASRProvider(ASRProviderBase):
    def __init__(self, config: dict, delete_audio_file: bool):
        super().__init__()
        self.interface_type = InterfaceType.LOCAL
        self.model_dir = config.get("model_dir")
        self.output_dir = config.get("output_dir")
        self.delete_audio_file = delete_audio_file

        os.makedirs(self.output_dir, exist_ok=True)

        encoder_path = os.path.join(self.model_dir, "encoder-epoch-20-avg-10.int8.onnx")
        decoder_path = os.path.join(self.model_dir, "decoder-epoch-20-avg-10.int8.onnx")
        joiner_path = os.path.join(self.model_dir, "joiner-epoch-20-avg-10.int8.onnx")
        tokens_path = os.path.join(self.model_dir, "config.json")

        for path in [encoder_path, decoder_path, joiner_path, tokens_path]:
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Model file not found: {path}")

        with CaptureOutput():
            self.model = sherpa_onnx.OfflineRecognizer.from_transducer(
                encoder=encoder_path,
                decoder=decoder_path,
                joiner=joiner_path,
                tokens=tokens_path,
                num_threads=int(config.get("num_threads", 2)),
                sample_rate=16000,
                feature_dim=80,
                decoding_method="greedy_search",
            )

        logger.bind(tag=TAG).info(
            f"Zipformer-VI transducer loaded from {self.model_dir}"
        )

    def read_wave(self, wave_filename: str) -> Tuple[np.ndarray, int]:
        with wave.open(wave_filename) as f:
            assert f.getnchannels() == 1, f.getnchannels()
            assert f.getsampwidth() == 2, f.getsampwidth()
            num_samples = f.getnframes()
            samples = f.readframes(num_samples)
            samples_int16 = np.frombuffer(samples, dtype=np.int16)
            samples_float32 = samples_int16.astype(np.float32)
            samples_float32 = samples_float32 / 32768
            return samples_float32, f.getframerate()

    def requires_file(self) -> bool:
        return True

    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str, audio_format="opus", artifacts=None
    ) -> Tuple[Optional[str], Optional[str]]:
        file_path = None
        try:
            if artifacts is None:
                return "", None
            file_path = artifacts.file_path

            start_time = time.time()
            s = self.model.create_stream()
            samples, sample_rate = self.read_wave(file_path)
            s.accept_waveform(sample_rate, samples)
            self.model.decode_stream(s)
            text = s.result.text
            logger.bind(tag=TAG).debug(
                f"ASR elapsed: {time.time() - start_time:.3f}s | text: {text}"
            )

            return text, file_path

        except Exception as e:
            logger.bind(tag=TAG).error(f"Speech recognition failed: {e}", exc_info=True)
            return "", file_path
