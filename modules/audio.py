import numpy as np
import pyaudio
import asyncio
import threading

from typing import Optional
from modules.workers.audio_workers import audio_consumer_worker, audio_producer_worker


format = pyaudio.paFloat32
channels = 1
rate = 16000
frames_amount = 1024



 

async def _clean(
        stop_flag: threading.Event,
        input_stream: Optional = None,
        output_stream: Optional = None, 
        consumer_thread: Optional = None,
        producer_task: Optional = None
 ):
        stop_flag.set()
        
        if input_stream:
             print('fechando o stream pra fazer a thread de input falhar e sair do read')
             input_stream.stop_stream()        
             input_stream.close()

        if producer_task:
            print('matando a task da producer')
        
            producer_task.cancel()

            try: 
                await producer_task
            except asyncio.CancelledError:
                pass

            print('terminou de cancelar a task')
        
        else:
            print(type(producer_task))
        if output_stream:
            print('matando o output stream')
            output_stream.stop_stream()
            output_stream.close()

        if consumer_thread:
            print('matando a thread')
            consumer_thread.join(timeout=1)
            print('matou a thread')


async def capture_audio_input_and_produce_audio_output(mode: Optional[str] = 'default'):
    so_audio_resources = None
    
    consumer_audio_input_stream = None
    producer_audio_output_stream = None

    audio_consumer_thread = None
    audio_producer_task = None

    stop_audio_workers_flag = threading.Event()
   
    try:
        loop = asyncio.get_running_loop()

        so_audio_resources = pyaudio.PyAudio()

        stream_consumed_audio_output_queue = asyncio.Queue()
        consumer_audio_input_stream = so_audio_resources.open(format=format, channels=channels, rate=rate, frames_per_buffer=frames_amount, input=True)

        producer_audio_input_queue = asyncio.Queue()
        producer_audio_output_stream = so_audio_resources.open(format=format, channels=channels, rate=rate, frames_per_buffer=frames_amount, output=True)

        audio_consumer_thread = threading.Thread(
                 target=audio_consumer_worker,
                 args=(stop_audio_workers_flag, frames_amount, consumer_audio_input_stream, stream_consumed_audio_output_queue, loop,)
             )
        
        audio_producer_task = asyncio.create_task(
                    audio_producer_worker(
                        stop_audio_workers_flag, 
                        stream_consumed_audio_output_queue if mode == 'echo' else producer_audio_input_queue,
                        producer_audio_output_stream,
                    )
                )

        audio_consumer_thread.start()
        await audio_producer_task

    except asyncio.CancelledError:
        print('realmente deu cancelled error')

    finally:
        await _clean(
            stop_flag=stop_audio_workers_flag,
            producer_task=audio_producer_task,
            consumer_thread=audio_consumer_thread, 
            input_stream=consumer_audio_input_stream,
            output_stream=producer_audio_output_stream,
         )

        if so_audio_resources is not None: 
            so_audio_resources.terminate()


