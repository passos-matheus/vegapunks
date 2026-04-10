import asyncio
import pyaudio
import collections
import numpy as np

from modules.stt import create_voice_detection_model, create_transcription_model, transcribe_speech_segment
from modules.tts import sintetize_speech_segment

format = pyaudio.paFloat32
channels = 1
rate = 16000
frames_amount = 1024


def audio_consumer_worker(so_audio_resources: pyaudio.PyAudio, stop_flag, number_of_frames_to_be_read, audio_bytes_queue, loop):
    try:
        _audio_bytes_input_stream = so_audio_resources.open(
            format=format, 
            channels=channels, 
            rate=rate, 
            frames_per_buffer=number_of_frames_to_be_read, 
            input=True
        )

    except:
        raise
        
    while not stop_flag.is_set():


        try: 
            audio_bytes = _audio_bytes_input_stream.read(number_of_frames_to_be_read)
           
            asyncio.run_coroutine_threadsafe(
                audio_bytes_queue.put(audio_bytes), loop
            )

            continue

        except OSError:
            print('stream de input cancelado manualmente')
            break        


async def audio_producer_worker(so_audio_resources: pyaudio.PyAudio, stop_flag, _sentences_queue, tts_model):
    try:
        loop = asyncio.get_running_loop()

        _audio_output_stream = so_audio_resources.open(
            format=format, 
            channels=channels, 
            rate=rate, 
            frames_per_buffer=frames_amount, 
            output=True
        )

    except:
        raise
        
    while not stop_flag.is_set():
        try:        
            sentence = await _sentences_queue.get()
            print(f'[tts sentence] {sentence}')

            audio_sentence = await loop.run_in_executor(None, sintetize_speech_segment, tts_model, sentence)

            _audio_output_stream.write(audio_sentence.tobytes())
            
        except OSError:
            print('stream de output cancelado manualmente')
            break
            
        except asyncio.CancelledError:
            print('producer_worker cancelado manualmente.')
            break 
 


