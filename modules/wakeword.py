from pathlib import Path
import numpy as np
from openwakeword.model import Model


 
THRESHOLD = 0.5
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1280  

MODEL_NAME = "hey_edson_wakeword_model"        
BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = str(BASE_DIR / "core/models/wakeword")

MODEL_PATH = f"{MODEL_DIR}/hey_edson_wakeword_model.onnx"



def create_wakeword_model():
   return Model(wakeword_model_paths=[MODEL_PATH])
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                            
def detect_wakeword_in_speech_segment(model, speech_segment: np.ndarray) -> bool:                                                                                                                                                                                                                                                             
    buffer = speech_segment.copy()                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                                            
    while len(buffer) >= CHUNK_SAMPLES:                                                                                                                                                                                                                                                                                                       
        chunk = (buffer[:CHUNK_SAMPLES] * 32767).astype(np.int16)           

        result = model.predict(chunk)                                                                                                                                                                                                                                                                                                         
        
        if result[MODEL_NAME] >= THRESHOLD:                                                                                                                                                                                                                                                                                                   
            return True                                                                                                                                                                                                                                                                                                                       
        
        buffer = buffer[CHUNK_SAMPLES:]                                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                            
    return False   

