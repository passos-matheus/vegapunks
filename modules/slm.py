import ctypes 
 
import json
from pathlib import Path
import re 
from llama_cpp import llama_set_adapters_lora, llama_adapter_lora_init, Llama


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = str(BASE_DIR / "core/models/slm/qwen-3-0.6B")

ADAPTERS_DIR = f"{MODEL_DIR}/lora_adapters"
MODEL_PATH = f"{MODEL_DIR}/Qwen3-0.6B-Q8_0.gguf"

 
def create_generation_model(path: str = MODEL_PATH, n_ctx: int = 2048):
    return Llama(
    model_path=path,
    n_ctx=n_ctx,
    verbose=False,
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


# podia ser um if, mas vou deixar aqui caso eu mude a lógca mais pra frente.
def identify_mode(first_content: str):
    return 'tool' if first_content.startswith('<') else 'text'



def process_tool(initial_buffer: str, remaining_chunks):
    extra_raw = ""
    
    buffer = initial_buffer

    for chunk in remaining_chunks:
        delta = chunk['choices'][0]['delta']
        print(delta)

        if 'content' in delta and delta['content']:
            extra_raw += delta['content']
            buffer += delta['content']

    cleaned = buffer.strip()
    tool_match = re.search(r'<tool_call>\s*(.*?)\s*</tool_call>', cleaned, re.DOTALL)

    if tool_match:
        tool_data = json.loads(tool_match.group(1))
        print(f'[tool_call]: {tool_data}')
        return tool_data, extra_raw

    print(f'detectou modo tool mas não encontrou <tool_call>: {cleaned}')
    
    return None, extra_raw


def process_generate(initial_buffer: str, remaining_chunks, on_sentence=print):
    extra_raw = ""

    buffer = initial_buffer

    for chunk in remaining_chunks:

        delta = chunk['choices'][0]['delta']

        if 'content' in delta and delta['content']:
            token = delta['content']
            extra_raw += token
            buffer += token

            match = re.search(r'.*[,\.!\?\;:\n]', buffer)

            if match:
                on_sentence(match.group())
                buffer = buffer[match.end():]

    if buffer:
        on_sentence(buffer)

    full_text = initial_buffer + extra_raw
    return full_text, extra_raw


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

