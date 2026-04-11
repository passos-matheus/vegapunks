import os
import time
import pyaudio
import asyncio
import threading
import numpy as np


from pathlib import Path
from collections import deque
from dataclasses import asdict
from modules.face import start_face, send_face
from modules.slm import create_generation_model
from modules.tts import create_speech_synthesis_model
from core.punk_records.satellites import vegapunks as vp_configs
from modules.wakeword import create_wakeword_model, detect_wakeword_in_speech_segment
from modules.workers.audio_workers import audio_consumer_worker, audio_producer_worker
from core.punk_records import start_punk_records, reconsult_satellite, activate_vegapunk
from modules.stt import create_voice_detection_model, create_transcription_model, transcribe_speech_segment, extract_speech_segment



frames_amount = 1024

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = str(BASE_DIR / "core/models/slm/qwen-3-0.6B")

ADAPTERS_DIR = f"{MODEL_DIR}/lora_adapters"

VEGAPUNK_MODE = os.environ.get("VEGAPUNK_MODE", "normal")
VAD_USE_PADDING = os.environ.get("VAD_USE_PADDING", "true").lower() == "true"


def _create_audio_resources():
    so = pyaudio.PyAudio()
    stop_flag = threading.Event()
    audio_input_queue = asyncio.Queue(maxsize=100)
    tts_output_queue = asyncio.Queue(maxsize=20)
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


def _extract_segment(audio_bytes, audio_history, total_samples_fed, voice_detection_model, use_padding=True):
    samples = np.frombuffer(audio_bytes, dtype=np.float32)
    segment, new_total = extract_speech_segment(
        audio_history=audio_history,
        total_samples_fed=total_samples_fed,
        voice_detection_model=voice_detection_model,
        speech_segment_samples=samples,
        use_padding=use_padding,
    )
    return segment, new_total


async def _pipeline_loop(
        stop_flag,
        audio_input_queue, tts_output_queue, loop,
        voice_detection_model, wakeword_model, transcription_model, punk_records=None, use_padding=True
    ):

    is_wakeword_active = False
    total_samples_fed = 0
    audio_history = deque()

    while not stop_flag.is_set():
        try:
            audio_bytes = await audio_input_queue.get()

            t0 = time.perf_counter()
            speech_segment, total_samples_fed = _extract_segment(
                audio_bytes, audio_history, total_samples_fed, voice_detection_model,
                use_padding=use_padding,
            )

            if speech_segment is None:
                continue

            t_vad = time.perf_counter()
            dur = len(speech_segment) / 16000
            print(f'[timer] vad: {(t_vad - t0)*1000:.0f}ms | segmento: {dur:.2f}s')

            if not is_wakeword_active:
                t1 = time.perf_counter()
                is_wakeword_active = await loop.run_in_executor(
                    None, detect_wakeword_in_speech_segment, wakeword_model, speech_segment
                )
                print(f'[timer] wakeword: {(time.perf_counter() - t1)*1000:.0f}ms')

                if not is_wakeword_active:
                    continue

                print('wakeword detectadaa')
                send_face(punk_records.face_queue if punk_records else None, "state", "listening")
                await tts_output_queue.put('E aí, mestre!')
                continue

            t2 = time.perf_counter()
            transcription = await loop.run_in_executor(
                None, transcribe_speech_segment, transcription_model, speech_segment
            )
            print(f'[timer] stt: {(time.perf_counter() - t2)*1000:.0f}ms')

            print(f'transcrição: {transcription}')

            if punk_records is not None:
                send_face(punk_records.face_queue, "state", "thinking")
                t3 = time.perf_counter()
                await reconsult_satellite(punk_records, transcription, output_queue=tts_output_queue, loop=loop)
                print(f'[timer] slm: {(time.perf_counter() - t3)*1000:.0f}ms')
                send_face(punk_records.face_queue, "state", "listening")

                if punk_records.shutdown_event.is_set():
                    punk_records.shutdown_event.clear()
                    is_wakeword_active = False
                    send_face(punk_records.face_queue, "state", "sleeping")
                    print('shutdown ativado, aguardando wakeword...')
                    continue
            else:
                await tts_output_queue.put(transcription)

        except:
            raise


async def run_punk_records():
    loop = asyncio.get_running_loop()
    so, stop_flag, audio_input_queue, tts_output_queue = _create_audio_resources()

    wakeword_model, transcription_model, voice_detection_model, tts_model = _create_models()
    punk_records = _create_punk_records()

    face_queue = start_face()
    punk_records.face_queue = face_queue
    appearances = {cfg['name']: asdict(cfg['appearance']) for cfg in vp_configs}
    send_face(face_queue, "appearances", appearances)
    send_face(face_queue, "mode", punk_records.current_active)
    send_face(face_queue, "state", "sleeping")

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
        send_face(punk_records.face_queue, "quit", None)
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
            use_padding=VAD_USE_PADDING,
        )
    except asyncio.CancelledError:
        print('cancelado.')
    finally:
        so.terminate()
        producer_task.cancel()


if __name__ == "__main__":
    if VEGAPUNK_MODE == "test":
        asyncio.run(run_punk_records_in_test_mode())
    else:
        asyncio.run(run_punk_records())
