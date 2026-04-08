import threading
import asyncio
import time
import pyaudio


from modules.audio import capture_audio_input_and_produce_audio_output



async def main():

    capture_and_produce_audio = asyncio.create_task(
            capture_audio_input_and_produce_audio_output(mode='echo_vad')
    )

    try:
        await capture_and_produce_audio
    
    finally:
        print('finalizando tasks e threads pendentes')
        capture_and_produce_audio.cancel()



async def execute_in_echo_mode():
    pass

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
    

    


    



