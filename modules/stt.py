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
        hotwords_file=HOTWORDS_FILE,
        hotwords_score=4.0,
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
    print('entrou aqui')
    stream  = transcription_model.create_stream()
    
    print('entrou aqui')
    stream.accept_waveform(SAMPLE_RATE, speech_segment_samples)
    print('entrou aqui')
    transcription_model.decode_stream(stream)
    print('entrou aqui')
    return stream.result.text.strip()

