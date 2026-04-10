import ctypes 
import _ctypes
from pathlib import Path
 
 

import llama_cpp
from llama_cpp import llama_set_adapters_lora, llama_adapter_lora_init

def create_user_message(message: str):
    

    return {'role': 'user', 'content': message + '/no_think'}


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = str(BASE_DIR / "core/models/slm/qwen-3-0.6B")

ADAPTERS_DIR = f"{MODEL_DIR}/lora_adapters"
MODEL_PATH = f"{MODEL_DIR}/Qwen3-0.6B-Q8_0.gguf"

messages = [
    {'role': 'system', 'content': 'Você é um assistente que só fala português brasileiro, siga a instruções corretamente.'}
]



def create_generation_model(path: str = MODEL_PATH, n_ctx: int = 2048):
    
    return llama_cpp.Llama(
    model_path=path,
    n_ctx=n_ctx,
    verbose=False,
)


def desactive_adapters(ctx, name_pointer_tuple_list, adapters, scales):
    _count = len(scales)

    for i in range(0, _count):
        scales[i] = 0.0

    code = llama_set_adapters_lora(ctx, adapters, _count, scales)

    if code != 0:
        raise Exception('Erro ao desativar adapters')

    desactived_adapters = [name for name, _ in name_pointer_tuple_list]

    return desactived_adapters

 

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

    return actived_adapter, personalized_scale

def _initialize_adapters(ctx, adapters):
    _adapters_count = len(adapters)

    _void_c_float_scales_array = _create_pure_C_array(ctypes.c_float, _adapters_count)
    _void_c_adapters_pointer_array = _create_pure_C_array(type(adapters[-1][-1]), _adapters_count)


    _scales_c_float_array = _void_c_float_scales_array(*([0.0] * _adapters_count))
    _adapter_pointers_c_array = _void_c_adapters_pointer_array(*[adapter_p for _, adapter_p in adapters])

    code = llama_set_adapters_lora(ctx, _adapter_pointers_c_array, _adapters_count, _scales_c_float_array)

    if code != 0:
        raise 'deu ruim'
    
    return _adapter_pointers_c_array, _scales_c_float_array 

def _load_adapter_in_memory(model, adapter_path, adapter_name):
    pointer = llama_adapter_lora_init(model, adapter_path.encode('utf-8'))
    
    if pointer is None:
        raise ValueError(f"Falha ao carregar adapter: {adapter_path}")
    
    print(f'{adapter_name} carregado com sucesso em memória.')
    print(pointer)

    return pointer
    
def _create_pure_C_array(_type, size):
    return _type * size


#    
#  
# 
# # adapter_a = _load_adapter_in_memory(slm.model, f'{ADAPTERS_DIR}/adapter_v8/adapter_v8.gguf', 'planner')
# adapter_b = _load_adapter_in_memory(slm.model, f'{ADAPTERS_DIR}/adapter_b/adapter_b.gguf', 'cópia do planner 1')
# adapter_c = _load_adapter_in_memory(slm.model, f'{ADAPTERS_DIR}/adapter_c/adapter_c.gguf', 'cópia do planner 2')
# 
# 
# adapters_pointer_python_list = [
#     ('adapter_a', adapter_a), 
#     ('adapter_b', adapter_b), 
#     ('adapter_c', adapter_c)
# ]
# 
# 
# _init_state = slm.save_state()
# 
# kv_cache_adapters = {
#     'adapter_a': {
#         'state': _init_state,
#         'messages': [{'role': 'system', 'content': 'Você é um assistente que só fala português brasileiro, siga a instruções corretamente.'}]
#     },
#     'adapter_b': {
#         'state': _init_state,
#         'messages': [{'role': 'system', 'content': 'Você é um assistente que só fala português brasileiro, siga a instruções corretamente.'}]
#     },
#     'adapter_c': {
#         'state': _init_state,
#         'messages': [{'role': 'system', 'content': 'Você é um assistente que só fala português brasileiro, siga a instruções corretamente.'}]
#     },
# }
# 
# adapters_pointers_c_array, scales_c_float_array =_initialize_adapters(slm.ctx, adapters_pointer_python_list)
# 
# actived_adapter, current_actived_adapter_scale = active_adapter(slm.ctx, 'adapter_a', adapters_pointer_python_list, adapters_pointers_c_array, scales_c_float_array, personalized_scale=1.0)
# print(f'adapter ativo: {actived_adapter}, scale: {current_actived_adapter_scale}')
# 
# kv_cache_adapters['adapter_a']['messages'].append(create_user_message('Qual a capital de minas gerais?'))
# 
# test_inference_with_adapter = slm.create_chat_completion(messages=kv_cache_adapters['adapter_a']['messages'], max_tokens=100, stream=False)
# 
# print(f'teste da inferência com o {active_adapter}, com scale {current_actived_adapter_scale}, resultado:{test_inference_with_adapter}')
# 
# kv_cache_adapters['adapter_a']['state'] = slm.save_state()
# 
# print(_init_state.n_tokens)
# print(kv_cache_adapters['adapter_a']['state'].n_tokens)
# 
# slm.reset()
#  
# 
# 
# print(kv_cache_adapters['adapter_a']['state'].n_tokens)
# slm.load_state(kv_cache_adapters['adapter_a']['state'])
# actived_adapter, current_actived_adapter_scale = active_adapter(slm.ctx, 'adapter_a', adapters_pointer_python_list, adapters_pointers_c_array, scales_c_float_array, personalized_scale=1.0)
# print(f'adapter ativo: {actived_adapter}, scale: {current_actived_adapter_scale}')
# 
# kv_cache_adapters['adapter_a']['messages'].append(create_user_message('diga apenas exatamente o nome do estado e repita exatamente a minha última pergunta'))
# 
# test_inference_with_adapter = slm.create_chat_completion(messages=kv_cache_adapters['adapter_a']['messages'], max_tokens=100, stream=False)
# 
# print(f'teste da inferência com o {active_adapter}, com scale {current_actived_adapter_scale}, resultado:{test_inference_with_adapter}')
# 
# kv_cache_adapters['adapter_a']['state'] = slm.save_state()
# 
# 
# print(kv_cache_adapters['adapter_a']['state'].n_tokens)
# 
# slm.reset()
#  
#  
#     
# 
#  
# 
