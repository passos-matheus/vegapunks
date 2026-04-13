import time
import asyncio
import numpy as np
import pyaudio


from modules.tts import sintetize_speech_segment, resample_audio


format = pyaudio.paFloat32
channels = 1
asr_rate = 16000
frames_amount = 1024

RATE_CANDIDATES = (16000, 48000, 44100)


def pick_supported_rate(pa: pyaudio.PyAudio, is_input: bool, candidates=RATE_CANDIDATES) -> int:
    host_info = pa.get_default_host_api_info()
    device_index = host_info['defaultInputDevice'] if is_input else host_info['defaultOutputDevice']

    for rate in candidates:
        try:
            kwargs = {'rate': rate, 'input_format' if is_input else 'output_format': format}
            if is_input:
                kwargs['input_device'] = device_index
                kwargs['input_channels'] = channels
            else:
                kwargs['output_device'] = device_index
                kwargs['output_channels'] = channels

            if pa.is_format_supported(**kwargs):
                print(f'[audio] {"input" if is_input else "output"} rate escolhida: {rate} Hz')
                return rate
        except ValueError:
            continue

    print(f'[audio] nenhuma taxa suportada encontrada, caindo no default 16000')
    return 16000


def audio_consumer_worker(so_audio_resources: pyaudio.PyAudio, stop_flag, number_of_frames_to_be_read, audio_bytes_queue, loop, input_rate: int = asr_rate):
    try:
        _audio_bytes_input_stream = so_audio_resources.open(
            format=format,
            channels=channels,
            rate=input_rate,
            frames_per_buffer=number_of_frames_to_be_read,
            input=True
        )

    except:
        raise

    needs_resample = input_rate != asr_rate

    while not stop_flag.is_set():
        try:
            audio_bytes = _audio_bytes_input_stream.read(number_of_frames_to_be_read)

            if needs_resample:
                samples = np.frombuffer(audio_bytes, dtype=np.float32)
                resampled = resample_audio(samples, input_rate, asr_rate)
                audio_bytes = resampled.astype(np.float32).tobytes()

            asyncio.run_coroutine_threadsafe(
                audio_bytes_queue.put(audio_bytes), loop
            )

            continue

        except OSError:
            print('stream de input cancelado manualmente')
            break


async def audio_producer_worker(so_audio_resources: pyaudio.PyAudio, stop_flag, _sentences_queue, tts_model, output_rate: int = asr_rate):
    try:
        loop = asyncio.get_running_loop()

        _audio_output_stream = so_audio_resources.open(
            format=format,
            channels=channels,
            rate=output_rate,
            frames_per_buffer=frames_amount,
            output=True
        )

    except:
        raise

    while not stop_flag.is_set():
        try:
            item = await _sentences_queue.get()

            if isinstance(item, tuple):
                sentence, voice_params = item
            else:
                sentence, voice_params = item, None

            print(f'[tts sentence] {sentence}')

            t0 = time.perf_counter()
            audio_sentence = await loop.run_in_executor(
                None, sintetize_speech_segment, tts_model, sentence, output_rate, voice_params
            )
            print(f'[timer] tts synth: {(time.perf_counter() - t0)*1000:.0f}ms | "{sentence[:40]}"')

            await loop.run_in_executor(None, _audio_output_stream.write, audio_sentence.tobytes())

        except OSError:
            print('stream de output cancelado manualmente')
            break

        except asyncio.CancelledError:
            print('producer_worker cancelado manualmente.')
            break
