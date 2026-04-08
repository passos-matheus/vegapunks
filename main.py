from collections import deque
import os
import threading
import asyncio
import time
import pyaudio

import numpy as np

frames_amount = 1024

from modules.workers.audio_workers import audio_consumer_worker, audio_producer_worker
from modules.stt import create_voice_detection_model, create_transcription_model, transcribe_speech_segment
from modules.audio import normalize_to_bytes, normalize_to_float_array




async def main():
    mode = os.getenv('PIPELINE_MODE', 'echo')


    if mode is not None and mode == 'echo':
        await run_in_echo_mode()


async def run_in_echo_mode():
    loop = asyncio.get_running_loop()

    so_audio_resources = pyaudio.PyAudio()
    stop_audio_workers_flag = threading.Event()
    
    audio_input_queue = asyncio.Queue()
    audio_output_queue = asyncio.Queue()

    try:


        audio_consumer_thread = threading.Thread(
            target=audio_consumer_worker,
            args=(so_audio_resources, stop_audio_workers_flag, frames_amount, audio_input_queue, loop,)
        )

        audio_producer_task = asyncio.create_task(
            audio_producer_worker(
                so_audio_resources,
                stop_audio_workers_flag, 
                audio_output_queue
            )
        )

        audio_consumer_thread.start()

        await echo_mode_pipeline(
            stop_flag=stop_audio_workers_flag,
            audio_input_queue=audio_input_queue,
            audio_output_queue=audio_output_queue
        )

    except asyncio.CancelledError:
        print('realmente deu cancelled error')

    finally:
        if so_audio_resources is not None: 
            so_audio_resources.terminate()

        audio_producer_task.cancel()

async def echo_mode_pipeline(stop_flag, audio_input_queue, audio_output_queue):
    transcription_model = create_transcription_model()
    voice_detection_model = create_voice_detection_model()

    pre_speech_detected_buffer = deque(maxlen=10)

    while not stop_flag.is_set():

        try: 
            audio_bytes = await audio_input_queue.get()
            normalized_to_float_array = normalize_to_float_array(audio_bytes)

            pre_speech_detected_buffer.append(normalized_to_float_array)
            voice_detection_model.accept_waveform(normalized_to_float_array)

            while not voice_detection_model.empty():

                segment = voice_detection_model.front
                voice_detection_model.pop()
             
                prefix = np.concatenate(list(pre_speech_detected_buffer))
                full_segment = np.concatenate([prefix, np.array(segment.samples, dtype=np.float32)])

                pre_speech_detected_buffer.clear()
                             
                normalized_speech_segment = normalize_to_bytes(full_segment)

                print('tocando')
                
                await audio_output_queue.put(normalized_speech_segment)
                
                print('transcrevendo')

                transcription = transcribe_speech_segment(
                    speech_segment_samples=full_segment, 
                    transcription_model=transcription_model
                )

                print(transcription)

                continue
        except:
            raise
    
        

async def execute_in_echo_vad_mode():
    # stream de entrada - fila de entrada - vad - fila de saída - stream de saída
    # ouvir só os segmentos de áudio que o VAD está enviando pra perceber se há cortes ou se eles estão vindo certos
    
    pass

async def echo():
    # conseguir escutar como minha fala está chegando através do VAD, ler como ela está sendo transcrita pelo stt, e ouvir como a transcrição está sendo sintetizada pelo STT
    # 
    pass


if __name__ == "__main__":
    asyncio.run(main())
    

    


    



