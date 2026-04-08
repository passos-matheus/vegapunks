import pyaudio
import asyncio
import threading

from typing import Optional

from modules.workers.audio_workers import audio_consumer_worker, audio_producer_worker

async def execute_in_echo_mode():
    pass

async def execute_in_default_mode():
    so_resources = None
    
    consumer_audio_input_stream = None
    producer_audio_output_stream = None

    try:
        format = pyaudio.paFloat32
        channels = 1
        rate = 16000
        frames_amount = 1024
        
        loop = asyncio.get_event_loop()
        so_audio_resources = pyaudio.PyAudio()

        consumer_audio_input_stream = so_audio_resources.open(format=format, channels=channels, rate=rate, frames_per_buffer=frames_amount, input=True)
        stream_consumed_audio_output_queue = asyncio.Queue()

        producer_audio_input_queue = asyncio.Queue()
        producer_audio_output_stream = so_audio_resources.open(format=format, channels=channels, rate=rate, frames_per_buffer=frames_amount, output=True)

        stop_audio_workers_flag = threading.Event()

        audio_consumer_thread = threading.Thread(
                 target=audio_consumer_worker,
                 args=(stop_audio_workers_flag, frames_amount, consumer_audio_input_stream, stream_consumed_audio_output_queue, loop,)
             )

        
        audio_producer_task = asyncio.create_task(
                    audio_producer_worker(stop_audio_workers_flag, stream_consumed_audio_output_queue, producer_audio_output_stream,)
                )

        audio_consumer_thread.start()
        await audio_producer_task

    except:
        pass
    finally: 
        stop_audio_workers_flag.set()
        
        if consumer_audio_input_stream is not None:
            consumer_audio_input_stream.stop_stream()
            consumer_audio_input_stream.close()

        if producer_audio_output_stream is not None:
            producer_audio_output_stream.stop_stream()
            producer_audio_output_stream.close()

        if so_resources is not None:
            so_resources.terminate()

        loop = asyncio.get_running_loop()
        await asyncio.wait_for(loop.run_in_executor(None, audio_consumer_thread.join, 2), 3)
        print('encerrou tudo certinhoo') 


async def capture_audio_input_and_produce_audio_output(mode: Optional[str] = 'default'):
    
    if mode is not None and mode == "default":
        return await execute_in_default_mode()

    if mode is not None and mode == "echo":
        return await execute_in_echo_mode()

    return await execute_in_default_mode()




