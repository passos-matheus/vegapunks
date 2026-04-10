import os
import asyncio
import pyaudio
import threading
import numpy as np
 

from pathlib import Path
from collections import deque
from modules.slm import create_generation_model
from modules.audio import normalize_to_bytes, normalize_to_float_array
from modules.tts import create_speech_synthesis_model, sintetize_speech_segment
from modules.wakeword import create_wakeword_model, detect_wakeword_in_speech_segment
from core.punk_records import start_punk_records, consult_satellite, activate_vegapunk
from modules.workers.audio_workers import audio_consumer_worker, audio_producer_worker
from modules.stt import create_voice_detection_model, create_transcription_model, transcribe_speech_segment, extract_speech_segment

frames_amount = 1024


BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = str(BASE_DIR / "core/models/slm/qwen-3-0.6B")

ADAPTERS_DIR = f"{MODEL_DIR}/lora_adapters"
MODEL_PATH = f"{MODEL_DIR}/Qwen3-0.6B-Q8_0.gguf"




async def main():
    mode = os.getenv('PIPELINE_MODE', 'default')

    if mode is not None and mode == 'default':
        await run_in_default_mode()

    if mode is not None and mode == 'echo':
        await run_in_echo_mode()







async def run_in_default_mode():
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
    
 
async def default_mode_pipeline(stop_flag, audio_input_queue, audio_output_queue):
    is_wakeword_said = False

    total_samples_fed = 0
    audio_history = deque()
    
    generation_model = create_generation_model()
    wakeword_model = create_wakeword_model()
    transcription_model = create_transcription_model()
    voice_detection_model = create_voice_detection_model()
    speech_synthesis_model = create_speech_synthesis_model()

    punk_records = start_punk_records(

    )
 

    while not stop_flag.is_set():

        try: 
            audio_bytes = await audio_input_queue.get()
            normalized_to_float_array = normalize_to_float_array(audio_bytes)

            speech_segment, total_samples_fed = extract_speech_segment(
                audio_history=audio_history,
                total_samples_fed=total_samples_fed,
                voice_detection_model=voice_detection_model, 
                speech_segment_samples=normalized_to_float_array
            )

            if speech_segment is None:
                continue

            is_waked = detect_wakeword_in_speech_segment(wakeword_model, speech_segment)

            if is_waked:
                print(f'resultado do wakeword: {is_waked}')
                is_wakeword_said = True

            
            if is_wakeword_said:
                print('transcrevendo')

                transcription = transcribe_speech_segment(
                    speech_segment_samples=speech_segment, 
                    transcription_model=transcription_model
                )

                print(transcription)

                print('gerandoo')


                print('sintetizandoo')

                float_32_audio_samples = sintetize_speech_segment(speech_synthesis_model, transcription)
                
                print('tocandooo')
                await audio_output_queue.put(float_32_audio_samples.tobytes())


        except:
            raise
    

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
    is_wakeword_said = False

    total_samples_fed = 0
    audio_history = deque()
    
    wakeword_model = create_wakeword_model()
    transcription_model = create_transcription_model()
    voice_detection_model = create_voice_detection_model()
    speech_synthesis_model = create_speech_synthesis_model()

    while not stop_flag.is_set():

        try: 
            audio_bytes = await audio_input_queue.get()
            normalized_to_float_array = normalize_to_float_array(audio_bytes)

            speech_segment, total_samples_fed = extract_speech_segment(
                audio_history=audio_history,
                total_samples_fed=total_samples_fed,
                voice_detection_model=voice_detection_model, 
                speech_segment_samples=normalized_to_float_array
            )

            if speech_segment is None:
                continue

            print('tocando')
            
            await audio_output_queue.put(speech_segment.tobytes())

            print('testando se ativa o wakeword')

            is_waked = detect_wakeword_in_speech_segment(wakeword_model, speech_segment)

            if is_waked:
                print(f'resultado do wakeword: {is_waked}')
                is_wakeword_said = not is_wakeword_said

            
            if is_wakeword_said:
                print('transcrevendo')

                transcription = transcribe_speech_segment(
                    speech_segment_samples=speech_segment, 
                    transcription_model=transcription_model
                )

                print(transcription)

                print('sintetizandoo')

                float_32_audio_samples = sintetize_speech_segment(speech_synthesis_model, transcription)
                
                print('tocandooo')
                await audio_output_queue.put(float_32_audio_samples.tobytes())


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
    #asyncio.run(main())

    model = create_generation_model()
    punk_records = start_punk_records(model, ADAPTERS_DIR)
    activate_vegapunk(punk_records, target_name='edson')


    t = consult_satellite(punk_records, 'Quala a previsão do tempo para são paulo?')
    print(t)


    



