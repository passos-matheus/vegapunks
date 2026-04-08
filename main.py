import threading
import asyncio
import time
import pyaudio

from modules.workers.audio_workers import audio_consumer_worker, audio_producer_worker


    


async def main():
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
if __name__ == "__main__":
    asyncio.run(main())
    

    


    



