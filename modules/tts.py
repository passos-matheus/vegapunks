import numpy as np
import sherpa_onnx


from math import gcd           
from pathlib import Path
from scipy.signal import resample_poly                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
                         

SPEED = 1.0

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = str(BASE_DIR / "core/models/tts/vits-piper-pt_BR-faber-medium")

MODEL_PATH = f"{MODEL_DIR}/pt_BR-faber-medium.onnx"
TOKENS_PATH = f"{MODEL_DIR}/tokens.txt"
DATA_DIR = f"{MODEL_DIR}/espeak-ng-data"
                                                                                                                                                                                                                                                                                                              
                                                                                                                                                                                                                                                                                                                                            
def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:                                                                                                                                                                                                                                            
    if orig_sr == target_sr:                                                                                                                                                                                                                                                                                                                  
        return audio                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                            
    g = gcd(orig_sr, target_sr)                                                                                                                                                                                                                                                                                                               
    up = target_sr // g                                                                                                                                                                                                                                                                                                                       
    down = orig_sr // g                                                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                            
    resampled = resample_poly(audio, up, down)                                                                                                                                                                                                                                                                                                
    return resampled.astype(audio.dtype)         


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
                                                                                                                                                                                                                                                        
    resampled = resample_audio(samples, audio.sample_rate)                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                                                
    return resampled                                                       

