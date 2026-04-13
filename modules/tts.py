import os
import numpy as np
import sherpa_onnx


from math import gcd
from pathlib import Path
from scipy.signal import resample_poly


SPEED = float(os.environ.get("TTS_SPEED", 1.0))
TTS_NUM_THREADS = int(os.environ.get("TTS_NUM_THREADS", 2))

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = str(BASE_DIR / "core/models/tts/vits-piper-pt_BR-faber-medium")

MODEL_PATH = f"{MODEL_DIR}/pt_BR-faber-medium.onnx"
TOKENS_PATH = f"{MODEL_DIR}/tokens.txt"
DATA_DIR = f"{MODEL_DIR}/espeak-ng-data"
                                                                                                                                                                                                                                                                                                              
                                                                                                                                                                                                                                                                                                                                            
def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio

    g = gcd(orig_sr, target_sr)
    up = target_sr // g
    down = orig_sr // g

    resampled = resample_poly(audio, up, down)
    return resampled.astype(audio.dtype)


def pitch_shift(samples: np.ndarray, semitones: float) -> np.ndarray:
    if semitones == 0.0:
        return samples

    ratio = 2.0 ** (semitones / 12.0)
    up = max(1, int(round(10000 / ratio)))
    down = 10000

    shifted = resample_poly(samples, up, down)
    return shifted.astype(samples.dtype)


def create_speech_synthesis_model():
    config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=MODEL_PATH, tokens=TOKENS_PATH, data_dir=DATA_DIR,
            ),
            provider="cpu", num_threads=TTS_NUM_THREADS,
        )
    )

    return sherpa_onnx.OfflineTts(config)


def sintetize_speech_segment(sintetize_spech_model, speech_segment: str, target_sr: int = 16000, voice_params: dict = None):
    speed = SPEED
    pitch = 0.0

    if voice_params is not None:
        speed = voice_params.get('speed', SPEED)
        pitch = voice_params.get('pitch', 0.0)

    audio = sintetize_spech_model.generate(speech_segment, speed=speed)

    samples = np.array(audio.samples, dtype=np.float32)
    resampled = resample_audio(samples, audio.sample_rate, target_sr)
    shifted = pitch_shift(resampled, pitch)

    return shifted

