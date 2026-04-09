import ctypes 
import _ctypes
 
 

import llama_cpp
from llama_cpp import llama_set_adapters_lora, llama_adapter_lora_init

def create_user_message(message: str):
    

    return {'role': 'user', 'content': message + '/no_think'}


slm = llama_cpp.Llama(
    model_path='slm/Qwen3-0.6B-Q8_0.gguf',
    n_ctx=2048,
    verbose=False,
)

messages = [
    {'role': 'system', 'content': 'Você é um assistente que só fala português brasileiro, siga a instruções corretamente.'}
]




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
   
    print(f'{adapter_name} carregado com sucesso em memória.')
    print(pointer)

    return pointer
    
def _create_pure_C_array(_type, size):
    return _type * size
   
 

adapter_a = _load_adapter_in_memory(slm.model, 'adapter_v8/adapter_v8.gguf', 'planner')
adapter_b = _load_adapter_in_memory(slm.model, 'adapter_b/adapter_b.gguf', 'cópia do planner 1')
adapter_c = _load_adapter_in_memory(slm.model, 'adapter_c/adapter_c.gguf', 'cópia do planner 2')

adapters_pointer_python_list = [
    ('adapter_a', adapter_a), 
    ('adapter_b', adapter_b), 
    ('adapter_c', adapter_c)
]

adapters_pointers_c_array, scales_c_float_array =_initialize_adapters(slm.ctx, adapters_pointer_python_list)

actived_adapter, current_actived_adapter_scale = active_adapter(slm.ctx, 'adapter_a', adapters_pointer_python_list, adapters_pointers_c_array, scales_c_float_array, personalized_scale=0.5)
print(f'adapter ativo: {actived_adapter}, scale: {current_actived_adapter_scale}')

messages.append(create_user_message('Preciso marcar uma call dez horas"'))

test_inference_with_adapter = slm.create_chat_completion(messages=messages, max_tokens=100, stream=False)
print(f'teste da inferência com o {active_adapter}, com scale {current_actived_adapter_scale}, resultado:{test_inference_with_adapter}')

messages.pop()
slm.reset()


actived_adapter, current_actived_adapter_scale = active_adapter(slm.ctx, 'adapter_b', adapters_pointer_python_list, adapters_pointers_c_array, scales_c_float_array, personalized_scale=0.1)
print(f'adapter ativo: {actived_adapter}, scale: {current_actived_adapter_scale}')

messages.append(create_user_message('Preciso marcar uma call dez horas"'))

test_inference_with_adapter = slm.create_chat_completion(messages=messages, max_tokens=100, stream=False)
print(f'teste da inferência com o {active_adapter}, com scale {current_actived_adapter_scale}, resultado:{test_inference_with_adapter}')

messages.pop()
slm.reset()


actived_adapter, current_actived_adapter_scale = active_adapter(slm.ctx, 'adapter_c', adapters_pointer_python_list, adapters_pointers_c_array, scales_c_float_array, personalized_scale=1.0)
print(f'adapter ativo: {actived_adapter}, scale: {current_actived_adapter_scale}')

messages.append(create_user_message('Preciso marcar uma call dez horas"'))

test_inference_with_adapter = slm.create_chat_completion(messages=messages, max_tokens=100, stream=False)
print(f'teste da inferência com o {active_adapter}, com scale {current_actived_adapter_scale}, resultado:{test_inference_with_adapter}')

messages.pop()
slm.reset()

actived_adapter, current_actived_adapter_scale =active_adapter(slm.ctx, 'adapter_a', adapters_pointer_python_list, adapters_pointers_c_array, scales_c_float_array, personalized_scale=0.7)
print(f'adapter ativo: {actived_adapter}, scale: {current_actived_adapter_scale}')

messages.append(create_user_message('Preciso marcar uma call dez horas"'))

test_inference_with_adapter = slm.create_chat_completion(messages=messages, max_tokens=100, stream=False)
print(f'teste da inferência com o {active_adapter}, com scale {current_actived_adapter_scale}, resultado:{test_inference_with_adapter}')

messages.pop()
slm.reset()

actived_adapter, current_actived_adapter_scale =active_adapter(slm.ctx, 'adapter_a', adapters_pointer_python_list, adapters_pointers_c_array, scales_c_float_array, personalized_scale=0.0)
print(f'adapter ativo: {actived_adapter}, scale: {current_actived_adapter_scale}')

messages.append(create_user_message('Marca uma call dez horas"'))

test_inference_with_adapter = slm.create_chat_completion(messages=messages, max_tokens=100, stream=False)
print(f'teste da inferência com o {active_adapter}, com scale {current_actived_adapter_scale}, resultado:{test_inference_with_adapter}')

messages.pop()
slm.reset()


## logs do resultado

# llama_context: n_ctx_seq (2048) < n_ctx_train (40960) -- the full capacity of the model will not be utilized
# planner carregado com sucesso em memória.
# <llama_cpp.llama_cpp.LP_c_void_p object at 0x77559a4e3cd0>
# cópia do planner 1 carregado com sucesso em memória.
# <llama_cpp.llama_cpp.LP_c_void_p object at 0x7755988308d0>
# cópia do planner 2 carregado com sucesso em memória.
# <llama_cpp.llama_cpp.LP_c_void_p object at 0x7755988318d0>
# adapter ativo: adapter_a, scale: 0.5
# teste da inferência com o <function active_adapter at 0x77559882e3e0>, com scale 0.5, resultado:{'id': 'chatcmpl-9dd50c29-712d-4b98-ba53-82fcdd0f6335', 'object': 'chat.completion', 'created': 1775774732, 'model': 'slm/Qwen3-0.6B-Q8_0.gguf', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '<think>\n\n</think>\n\nClaro! Aí está a chamada: **Call 10 horas**.'}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 47, 'completion_tokens': 22, 'total_tokens': 69}}
# adapter ativo: adapter_b, scale: 0.1
# teste da inferência com o <function active_adapter at 0x77559882e3e0>, com scale 0.1, resultado:{'id': 'chatcmpl-7f1156f9-be2c-46a1-b7d9-a5beba17d449', 'object': 'chat.completion', 'created': 1775774738, 'model': 'slm/Qwen3-0.6B-Q8_0.gguf', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '<think>\n\n</think>\n\nCall dezenas.'}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 47, 'completion_tokens': 9, 'total_tokens': 56}}
# adapter ativo: adapter_c, scale: 1.0
# teste da inferência com o <function active_adapter at 0x77559882e3e0>, com scale 1.0, resultado:{'id': 'chatcmpl-db389622-227a-4107-8c32-94d8cda7b936', 'object': 'chat.completion', 'created': 1775774742, 'model': 'slm/Qwen3-0.6B-Q8_0.gguf', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '<think>\n\n</think>\n\nNão, não faço isso. Posso ajudar com call ou notificações.'}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 47, 'completion_tokens': 22, 'total_tokens': 69}}
# adapter ativo: adapter_a, scale: 0.7
# teste da inferência com o <function active_adapter at 0x77559882e3e0>, com scale 0.7, resultado:{'id': 'chatcmpl-404fdc48-46b9-435e-9447-4ccdb42b5709', 'object': 'chat.completion', 'created': 1775774748, 'model': 'slm/Qwen3-0.6B-Q8_0.gguf', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '<think>\n\n</think>\n\nCall de dez horas.'}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 47, 'completion_tokens': 9, 'total_tokens': 56}}
# adapter ativo: adapter_a, scale: 0.0
# teste da inferência com o <function active_adapter at 0x77559882e3e0>, com scale 0.0, resultado:{'id': 'chatcmpl-3f83a9e8-8081-482b-adba-9be3e85dec4e', 'object': 'chat.completion', 'created': 1775774754, 'model': 'slm/Qwen3-0.6B-Q8_0.gguf', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '<think>\n\n</think>\n\nClaro! A marca da chamada é **"Call"**.'}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 47, 'completion_tokens': 19, 'total_tokens': 66}}







 
 
    

 

