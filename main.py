import threading
import asyncio
import time
import pyaudio


from modules.audio import capture_audio_input_and_produce_audio_output



async def main():

    capture_and_produce_audio = asyncio.create_task(
            capture_audio_input_and_produce_audio_output(mode='echo')
    )

    try:
        await capture_and_produce_audio
    
    finally:
        print('finalizando tasks e threads pendentes')
        capture_and_produce_audio.cancel()



if __name__ == "__main__":
    asyncio.run(main())
    

    


    



