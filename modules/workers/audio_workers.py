import asyncio
import collections
import numpy as np


from modules.stt import create_voice_detection_model


def audio_consumer_worker(stop_flag, frames_amount, _input_stream,  _output_queue, loop):
    vad = create_voice_detection_model()	

    pre_buffer = collections.deque(maxlen=10) 

    while not stop_flag.is_set():

        try: 
            samples = _input_stream.read(frames_amount)
            normalized_to_float_array = normalize_to_float_array(samples)

            pre_buffer.append(normalized_to_float_array)
            vad.accept_waveform(normalized_to_float_array)

            while not vad.empty():
                segment = vad.front
                vad.pop()
             
                prefix = np.concatenate(list(pre_buffer))
                full_segment = np.concatenate([prefix, np.array(segment.samples, dtype=np.float32)])

                pre_buffer.clear()
                
                normalized_speech_segment = normalize_to_bytes(full_segment)
                asyncio.run_coroutine_threadsafe(_output_queue.put(normalized_speech_segment), loop)


        except OSError:
            print('stream de input cancelado manualmente')
            break            

async def audio_producer_worker(stop_flag, _input_queue, output_stream):
    
    while not stop_flag.is_set():
        try:        
            audio_bytes = await _input_queue.get()
            output_stream.write(audio_bytes)
            
        except OSError:
            print('stream de output cancelado manualmente')
            break
            
        except asyncio.CancelledError:
            print('producer_worker cancelado manualmente.')
            break 
        

def normalize_to_float_array(audio_bytes):
    return np.frombuffer(audio_bytes, dtype=np.float32)

def normalize_to_bytes(speech_segment):
    return speech_segment.tobytes()

