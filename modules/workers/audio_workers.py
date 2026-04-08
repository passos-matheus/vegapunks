import asyncio


def audio_consumer_worker(stop_flag, frames_amount, _input_stream,  _output_queue, loop):

    while not stop_flag.is_set():
        _fut = None

        try: 
            data = _input_stream.read(frames_amount)
            _fut = asyncio.run_coroutine_threadsafe(_output_queue.put(data), loop)
        
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
        
