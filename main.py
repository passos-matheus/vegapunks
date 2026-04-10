import asyncio
import pyaudio
import threading

from pathlib import Path
from collections import deque
from modules.slm import create_generation_model
from modules.audio import normalize_to_float_array
from modules.tts import create_speech_synthesis_model
from modules.wakeword import create_wakeword_model, detect_wakeword_in_speech_segment
from core.punk_records import start_punk_records, consult_satellite, activate_vegapunk
from modules.workers.audio_workers import audio_consumer_worker, audio_producer_worker
from modules.stt import create_voice_detection_model, create_transcription_model, transcribe_speech_segment, extract_speech_segment

frames_amount = 1024

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = str(BASE_DIR / "core/models/slm/qwen-3-0.6B")
ADAPTERS_DIR = f"{MODEL_DIR}/lora_adapters"


def _create_audio_resources():
    so = pyaudio.PyAudio()
    stop_flag = threading.Event()
    audio_input_queue = asyncio.Queue()
    tts_output_queue = asyncio.Queue()
    return so, stop_flag, audio_input_queue, tts_output_queue


def _start_audio_consumer(so, stop_flag, audio_input_queue, loop):
    thread = threading.Thread(
        target=audio_consumer_worker,
        args=(so, stop_flag, frames_amount, audio_input_queue, loop),
    )
    thread.start()
    return thread


def _start_audio_producer(so, stop_flag, tts_output_queue, tts_model):
    task = asyncio.create_task(
        audio_producer_worker(so, stop_flag, tts_output_queue, tts_model)
    )
    return task


def _create_models():
    wakeword_model = create_wakeword_model()
    transcription_model = create_transcription_model()
    voice_detection_model = create_voice_detection_model()
    tts_model = create_speech_synthesis_model()
    return wakeword_model, transcription_model, voice_detection_model, tts_model


def _create_punk_records():
    slm = create_generation_model()
    punk_records = start_punk_records(slm, ADAPTERS_DIR)
    activate_vegapunk(punk_records, target_name='edson')
    return punk_records


def _extract_segment(audio_bytes, audio_history, total_samples_fed, voice_detection_model):
    samples = normalize_to_float_array(audio_bytes)
    segment, new_total = extract_speech_segment(
        audio_history=audio_history,
        total_samples_fed=total_samples_fed,
        voice_detection_model=voice_detection_model,
        speech_segment_samples=samples,
    )
    return segment, new_total


async def _pipeline_loop(stop_flag, audio_input_queue, tts_output_queue, loop,
                         voice_detection_model, wakeword_model, transcription_model,
                         punk_records=None):
    is_wakeword_active = False
    total_samples_fed = 0
    audio_history = deque()

    while not stop_flag.is_set():
        try:
            audio_bytes = await audio_input_queue.get()

            speech_segment, total_samples_fed = _extract_segment(
                audio_bytes, audio_history, total_samples_fed, voice_detection_model,
            )

            if speech_segment is None:
                continue

            is_waked = detect_wakeword_in_speech_segment(wakeword_model, speech_segment)

            if is_waked:
                print(f'wakeword detectado!')
                is_wakeword_active = not is_wakeword_active

            if not is_wakeword_active:
                continue

            transcription = transcribe_speech_segment(
                speech_segment_samples=speech_segment,
                transcription_model=transcription_model,
            )

            print(f'transcrição: {transcription}')

            if punk_records is not None:
                consult_satellite(punk_records, transcription, output_queue=tts_output_queue, loop=loop)
            else:
                await tts_output_queue.put(transcription)

        except:
            raise


async def run_punk_records():
    loop = asyncio.get_running_loop()
    so, stop_flag, audio_input_queue, tts_output_queue = _create_audio_resources()

    wakeword_model, transcription_model, voice_detection_model, tts_model = _create_models()
    punk_records = _create_punk_records()

    producer_task = _start_audio_producer(so, stop_flag, tts_output_queue, tts_model)
    _start_audio_consumer(so, stop_flag, audio_input_queue, loop)

    try:
        await _pipeline_loop(
            stop_flag, audio_input_queue, tts_output_queue, loop,
            voice_detection_model, wakeword_model, transcription_model,
            punk_records=punk_records,
        )
    except asyncio.CancelledError:
        print('cancelado.')
    finally:
        so.terminate()
        producer_task.cancel()


async def run_punk_records_in_test_mode():
    loop = asyncio.get_running_loop()
    so, stop_flag, audio_input_queue, tts_output_queue = _create_audio_resources()

    wakeword_model, transcription_model, voice_detection_model, tts_model = _create_models()

    producer_task = _start_audio_producer(so, stop_flag, tts_output_queue, tts_model)
    _start_audio_consumer(so, stop_flag, audio_input_queue, loop)

    try:
        await _pipeline_loop(
            stop_flag, audio_input_queue, tts_output_queue, loop,
            voice_detection_model, wakeword_model, transcription_model,
            punk_records=None,
        )
    except asyncio.CancelledError:
        print('cancelado.')
    finally:
        so.terminate()
        producer_task.cancel()


if __name__ == "__main__":
    asyncio.run(run_punk_records())
