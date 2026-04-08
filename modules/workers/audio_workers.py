import asyncio


def audio_consumer_worker(stop_flag, frames_amount, _input_stream,  _output_queue, loop):

    while not stop_flag.is_set():
        
        data = _input_stream.read(frames_amount)
        
        asyncio.run_coroutine_threadsafe(_output_queue.put(data), loop)


async def audio_producer_worker(stop_flag, _input_queue, output_stream):
    
    while not stop_flag.is_set():
        
        audio_bytes = await _input_queue.get()
        output_stream.write(audio_bytes)
        
        
        

