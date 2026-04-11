from collections import deque

import numpy as np
import sherpa_onnx

from pathlib import Path


# mover pra core num arquivos de constantes. 
SAMPLE_RATE = 16000
CHUNK_SIZE = 512 


BASE_DIR = Path(__file__).resolve().parent.parent



ASR_MODEL_DIR = str(BASE_DIR / "core/models/asr/")
VAD_MODEL = str(BASE_DIR / "core/models/vad/silero_vad.onnx")

END_OF_SPEECH_TIMEOUT = 1.0

HOTWORDS_FILE = str(BASE_DIR / "core/models/asr/hotwords.txt")


def create_transcription_model():

    return sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=f"{ASR_MODEL_DIR}/encoder.int8.onnx",
        decoder=f"{ASR_MODEL_DIR}/decoder.int8.onnx",
        joiner=f"{ASR_MODEL_DIR}/joiner.int8.onnx",
        tokens=f"{ASR_MODEL_DIR}/tokens.txt",
        model_type="nemo_transducer",
        modeling_unit="bpe",
        bpe_vocab=f"{ASR_MODEL_DIR}/bpe.vocab",
        num_threads=2,
        decoding_method="modified_beam_search",
        # hotwords_file=HOTWORDS_FILE,
        # hotwords_score=4.0,
    )


def create_voice_detection_model():
	c = sherpa_onnx.VadModelConfig()

	c.silero_vad.model = VAD_MODEL

	c.silero_vad.threshold = 0.5
	c.silero_vad.min_silence_duration = 0.4
	c.silero_vad.min_speech_duration = 0.20
	c.silero_vad.window_size = CHUNK_SIZE
	c.sample_rate = SAMPLE_RATE
	c.num_threads = 2
    
	return sherpa_onnx.VoiceActivityDetector(c, buffer_size_in_seconds=30)


def transcribe_speech_segment(transcription_model, speech_segment_samples):                                                                                                                                                                                                                                                                   
    seg = speech_segment_samples           

    print(f'speech de entrada: len={len(seg)}, dur={len(seg)/16000:.2f}s, min={seg.min():.4f}, max={seg.max():.4f}, dtype={seg.dtype}')            

    stream = transcription_model.create_stream()                                                                                                                                                                                                                                                                                              
    stream.accept_waveform(SAMPLE_RATE, speech_segment_samples)                                                                                                                                                                                                                                                                               
    transcription_model.decode_stream(stream)                                                                                                                                                                                                                                                                                                 
    return stream.result.text.strip()



def extract_speech_segment(audio_history, total_samples_fed, voice_detection_model, speech_segment_samples, use_padding=True):
    full_segment = None

    HISTORY_SECONDS = 30
    PADDING_SECONDS = 0.32
    PADDING_SAMPLES = int(PADDING_SECONDS * SAMPLE_RATE)

    chunk_start = total_samples_fed
    audio_history.append((chunk_start, speech_segment_samples))
    total_samples_fed += len(speech_segment_samples)

    cutoff = total_samples_fed - int(HISTORY_SECONDS * SAMPLE_RATE)

    while audio_history:
        oldest_start, oldest_samples = audio_history[0]
        if oldest_start + len(oldest_samples) < cutoff:
            audio_history.popleft()
        else:
            break

    voice_detection_model.accept_waveform(speech_segment_samples)

    while not voice_detection_model.empty():
        segment = voice_detection_model.front
        speech = np.array(segment.samples, dtype=np.float32)
        seg_start = segment.start

        voice_detection_model.pop()

        if not use_padding:
            return speech, total_samples_fed

        padding_start = max(0, seg_start - PADDING_SAMPLES)

        padding_chunks = []
        for (cs, cs_samples) in audio_history:
            ce = cs + len(cs_samples)
            overlap_begin = max(cs, padding_start)
            overlap_end = min(ce, seg_start)

            if overlap_begin < overlap_end:
                local_begin = overlap_begin - cs
                local_end = overlap_end - cs
                padding_chunks.append(cs_samples[local_begin:local_end])

        if padding_chunks:
            prefix = np.concatenate(padding_chunks)
            full_segment = np.concatenate([prefix, speech])
        else:
            full_segment = speech

        return full_segment, total_samples_fed

    return full_segment, total_samples_fed
