import re
import os
import json
import ctypes
import hashlib


from pathlib import Path
from llama_cpp import llama_set_adapters_lora, llama_adapter_lora_init, Llama



BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = str(BASE_DIR / "core/models/slm/qwen-3-0.6B")

ADAPTERS_DIR = f"{MODEL_DIR}/lora_adapters"
MODEL_PATH = f"{MODEL_DIR}/Qwen3-0.6B-Q8_0.gguf"

N_CTX = int(os.environ.get("SLM_N_CTX", 2048))
_n_threads_raw = os.environ.get("SLM_N_THREADS")
N_THREADS = int(_n_threads_raw) if _n_threads_raw else None
_n_threads_batch_raw = os.environ.get("SLM_N_THREADS_BATCH")
N_THREADS_BATCH = int(_n_threads_batch_raw) if _n_threads_batch_raw else None
N_BATCH = int(os.environ.get("SLM_N_BATCH", 512))
N_UBATCH = int(os.environ.get("SLM_N_UBATCH", 512))
USE_MMAP = os.environ.get("SLM_USE_MMAP", "false").lower() == "true"
USE_MLOCK = os.environ.get("SLM_USE_MLOCK", "false").lower() == "true"
VERBOSE = os.environ.get("SLM_VERBOSE", "false").lower() == "true"


def create_generation_model(path: str = MODEL_PATH):
    return Llama(
        model_path=path,
        n_ctx=N_CTX,
        n_batch=N_BATCH,
        n_ubatch=N_UBATCH,
        n_threads=N_THREADS,
        n_threads_batch=N_THREADS_BATCH,
        use_mmap=USE_MMAP,
        use_mlock=USE_MLOCK,
        verbose=VERBOSE,
    )

def generate(messages: list, model: Llama, strean: bool = True):
    return model.create_chat_completion(messages=messages, stream=strean, max_tokens=256)

def process_think(raw: str):

    _, think_and_rest = raw.split('<think>', 1) if '<think>' in raw else ('', raw)

    think_content, after_think = think_and_rest.split('</think>', 1) if '</think>' in think_and_rest else (think_and_rest, '')
    think_content = think_content.strip()

    if think_content:
        print(f'aaaaaaaaaa modelo não desativou o thinking: {think_content}')

    return think_content, after_think


TOOL_CALL_OPEN = '<tool_call>'
TOOL_CALL_CLOSE = '</tool_call>'
_SENTENCE_RE = re.compile(r'.*[,\.!\?\;:\n]')
_TOOL_CALL_RE = re.compile(r'<tool_call>\s*(.*?)\s*</tool_call>', re.DOTALL)


def _iter_content_tokens(chunks):
    for chunk in chunks:
        delta = chunk['choices'][0]['delta']
        content = delta.get('content') if 'content' in delta else None
        if content:
            yield content


def _flush_sentences(buffer, on_sentence):
    while True:
        match = _SENTENCE_RE.search(buffer)
        if not match:
            return buffer
        on_sentence(match.group())
        buffer = buffer[match.end():]


def _partition_at_tool_prefix(buffer):
    i = 0
    while True:
        lt = buffer.find('<', i)
        if lt < 0:
            return buffer, ''
        tail = buffer[lt:]
        if TOOL_CALL_OPEN.startswith(tail[:len(TOOL_CALL_OPEN)]):
            return buffer[:lt], tail
        i = lt + 1


def _extract_tool_call_json(buffer):
    match = _TOOL_CALL_RE.search(buffer)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f'[tool_call] json inválido: {e} | raw: {match.group(1)!r}')
        return None


def _drain_until_tool_close(buffer, token_iter, raw):
    while TOOL_CALL_CLOSE not in buffer:
        try:
            token = next(token_iter)
        except StopIteration:
            break
        raw += token
        buffer += token

    tool_data = _extract_tool_call_json(buffer)
    if tool_data is not None:
        print(f'[tool_call]: {tool_data}')
    else:
        print(f'detectou modo tool mas não encontrou <tool_call>: {buffer.strip()}')

    return tool_data, raw


def process_stream(chunks, on_sentence):
    token_iter = _iter_content_tokens(chunks)
    raw = ''
    after_think = ''
    think_done = False

    for token in token_iter:
        raw += token
        if '</think>' in raw:
            _, after_think = process_think(raw)
            think_done = True
            break

    if not think_done:
        return 'message', None, raw

    buffer = after_think

    while not buffer.lstrip():
        try:
            token = next(token_iter)
        except StopIteration:
            return 'message', None, raw
        raw += token
        buffer += token

    if buffer.lstrip().startswith('<'):
        tool_data, raw = _drain_until_tool_close(buffer, token_iter, raw)
        return 'tool', tool_data, raw

    while True:
        if TOOL_CALL_OPEN in buffer:
            print('[warn] modelo preambulou antes de <tool_call>, executando tool mesmo assim')
            tool_data, raw = _drain_until_tool_close(buffer, token_iter, raw)
            return 'tool', tool_data, raw

        safe, held = _partition_at_tool_prefix(buffer)
        buffer = _flush_sentences(safe, on_sentence) + held

        try:
            token = next(token_iter)
        except StopIteration:
            break
        raw += token
        buffer += token

    if buffer.strip():
        on_sentence(buffer)
    return 'message', None, raw


def desactive_adapters(ctx, name_pointer_tuple_list, adapters, scales):
    _count = len(scales)

    for i in range(0, _count):
        scales[i] = 0.0

    code = llama_set_adapters_lora(ctx, adapters, _count, scales)

    if code != 0:
        raise Exception('Erro ao desativar adapters')

    desactived_adapters = [name for name, _ in name_pointer_tuple_list]

    print(f'Desativandos adapters: {desactived_adapters}.')
    return desactived_adapters, scales


def active_adapter(ctx, target_adapter, name_pointer_tuple_list, adapters, scales, personalized_scale = 1.0):
    _count = len(scales)
    actived_adapter = None
 
    for i in range(0, _count):
        if target_adapter == name_pointer_tuple_list[i][0]:
            actived_adapter = target_adapter
            scales[i] = personalized_scale

            continue 
        
        scales[i] = 0.0

    if actived_adapter is None:
        raise Exception('adapter target não ta na lista')

    code = llama_set_adapters_lora(ctx, adapters, _count, scales)

    if code != 0:
        raise Exception('deu ruim tbm')

    print(f'Adapter {actived_adapter} ativado! Scale: {personalized_scale}')
    return actived_adapter, personalized_scale

def initialize_adapters(ctx, adapters_c_pointers):
    _adapters_count = len(adapters_c_pointers)

    print(len(adapters_c_pointers))
    print(adapters_c_pointers[-1])

    _void_c_float_scales_array = _create_pure_C_array(ctypes.c_float, _adapters_count)
    _void_c_adapters_pointer_array = _create_pure_C_array(type(adapters_c_pointers[-1]), _adapters_count)


    _scales_c_float_array = _void_c_float_scales_array(*([0.0] * _adapters_count))
    _adapter_pointers_c_array = _void_c_adapters_pointer_array(*[adapter_p for adapter_p in adapters_c_pointers])

    code = llama_set_adapters_lora(ctx, _adapter_pointers_c_array, _adapters_count, _scales_c_float_array)

    if code != 0:
        raise Exception('deu ruim')
    
    return _adapter_pointers_c_array, _scales_c_float_array 

def load_adapter_in_memory(model, adapter_path, adapter_name):
    pointer = llama_adapter_lora_init(model, adapter_path.encode('utf-8'))
    
    if pointer is None:
        raise ValueError(f"Falha ao carregar adapter: {adapter_path}")
    
    print(f'{adapter_name} carregado com sucesso em memória.')
    print(pointer)

    return pointer
    
def _create_pure_C_array(_type, size):
    return _type * size

def create_user_message(message: str):
    return {'role': 'user', 'content': message + '/no_think'}

def create_system_message(message: str):
    return {'role': 'system', 'content': message}


def compute_state_hash(adapter_path, system_prompt, tools):
    payload = f"{adapter_path}|{system_prompt}|{json.dumps(tools, sort_keys=True)}"
    return hashlib.sha256(payload.encode()).hexdigest()

