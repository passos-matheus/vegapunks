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


def _default_device_index(pa: pyaudio.PyAudio, is_input: bool) -> int:
    host_info = pa.get_default_host_api_info()
    return host_info['defaultInputDevice'] if is_input else host_info['defaultOutputDevice']


def resolve_device_index(pa: pyaudio.PyAudio, value, is_input: bool):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        pass

    needle = str(value).lower()
    channel_key = 'maxInputChannels' if is_input else 'maxOutputChannels'
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info[channel_key] > 0 and needle in info['name'].lower():
            return i

    raise ValueError(f'nenhum device de {"entrada" if is_input else "saída"} com "{value}" no nome')


def pick_supported_rate(pa: pyaudio.PyAudio, is_input: bool, device_index=None, candidates=RATE_CANDIDATES) -> int:
    resolved_index = device_index if device_index is not None else _default_device_index(pa, is_input)

    for rate in candidates:
        try:
            probe_kwargs = dict(
                format=format,
                channels=channels,
                rate=rate,
                frames_per_buffer=1024,
            )
            if is_input:
                probe_kwargs['input'] = True
                probe_kwargs['input_device_index'] = resolved_index
            else:
                probe_kwargs['output'] = True
                probe_kwargs['output_device_index'] = resolved_index

            probe_stream = pa.open(**probe_kwargs)
            probe_stream.close()
            print(f'[audio] {"input" if is_input else "output"} rate escolhida: {rate} Hz (device {resolved_index})')
            return rate
        except Exception:
            continue

    print(f'[audio] nenhuma taxa suportada encontrada, caindo no default 16000')
    return 16000


def audio_consumer_worker(so_audio_resources: pyaudio.PyAudio, stop_flag, number_of_frames_to_be_read, audio_bytes_queue, loop, input_rate: int = asr_rate, input_device_index=None):
    open_kwargs = dict(
        format=format,
        channels=channels,
        rate=input_rate,
        frames_per_buffer=number_of_frames_to_be_read,
        input=True,
    )
    if input_device_index is not None:
        open_kwargs['input_device_index'] = input_device_index

    try:
        _audio_bytes_input_stream = so_audio_resources.open(**open_kwargs)
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


async def audio_producer_worker(so_audio_resources: pyaudio.PyAudio, stop_flag, _sentences_queue, tts_model, output_rate: int = asr_rate, output_device_index=None):
    open_kwargs = dict(
        format=format,
        channels=channels,
        rate=output_rate,
        frames_per_buffer=frames_amount,
        output=True,
    )
    if output_device_index is not None:
        open_kwargs['output_device_index'] = output_device_index

    try:
        loop = asyncio.get_running_loop()
        _audio_output_stream = so_audio_resources.open(**open_kwargs)
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
