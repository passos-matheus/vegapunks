import threading
import asyncio
import time
import pyaudio


from modules.audio import capture_audio_input_and_produce_audio_output


    


async def main():
    await asyncio.wait_for(capture_audio_input_and_produce_audio_output(), 15)
    print('esperou certo!')

if __name__ == "__main__":
    asyncio.run(main())
    

    


    



