import numpy as np
import sherpa_onnx

from pathlib import Path
 

SPEED = 1.0

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = str(BASE_DIR / "core/models/tts/vits-piper-pt_BR-faber-medium")

MODEL_PATH = f"{MODEL_DIR}/pt_BR-faber-medium.onnx"
TOKENS_PATH = f"{MODEL_DIR}/tokens.txt"
DATA_DIR = f"{MODEL_DIR}/espeak-ng-data"


def create_speech_synthesis_model():
    config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=MODEL_PATH, tokens=TOKENS_PATH, data_dir=DATA_DIR,
            ),
            provider="cpu", num_threads=2,
        )
    )
    
    return sherpa_onnx.OfflineTts(config)


def sintetize_speech_segment(sintetize_spech_model, speech_segment: str):

    audio = sintetize_spech_model.generate(
        speech_segment, speed=SPEED
    )
    samples = np.array(audio.samples, dtype=np.float32)
    
    return samples

