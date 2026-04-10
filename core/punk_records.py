
import re
import json

 
from pathlib import Path
from typing import Any, List
from dataclasses import dataclass
from core.satellites import vegapunks
from llama_cpp import Llama, LlamaState
from modules.slm import create_user_message, identify_mode, load_adapter_in_memory, initialize_adapters, active_adapter, desactive_adapters, create_system_message, process_generate, process_think, process_tool
 
 
@dataclass
class SatelliteParams:
    name: str
    tools: Any
    adapter_path: Any
    system_prompt: str
    tools_feedbacks: Any
     

     

    
    
   

@dataclass
class SatelliteSkills:
    sys_prompt: str
    tools: str

@dataclass
class SatelliteMemory:
    
    sys_prompt_msg: dict
    messages: list[dict]

    base_state: LlamaState
    current_state: LlamaState
     



@dataclass
class SatelliteKnowledge:
    is_active: bool
    current_scale: float
    knowledge_c_pointer: Any
    

class SatelliteAppearance:
    pass

class SatellitePersonallity:
    pass

@dataclass
class VegapunkSatellite:
        name: str

        skills: SatelliteSkills
        memory: SatelliteMemory

        knowledge: SatelliteKnowledge



@dataclass
class PunkRecords:
    satellites: dict[str, VegapunkSatellite]       
    adapters_pointers_c_array: Any
    adapters_scales_c_float_array: Any
    current_active: str = None


def _create_vegapunk_satelite(params: SatelliteParams, memory_state: LlamaState, adapter_c_pointer: Any, scale_c_float_array: Any):

    skills = SatelliteSkills(
        sys_prompt=params.system_prompt,
        tools=params.tools
    )

    sys_msg = create_system_message(message=params.system_prompt)

    memory = SatelliteMemory(
        messages=[],
        sys_prompt_msg=sys_msg,
        base_state=memory_state,
        current_state=memory_state,
    )

    if scale_c_float_array[-1] > 0.0:
        raise Exception('criando um vegapunk já ativo!')

    knowledge = SatelliteKnowledge(
        is_active=False,
        knowledge_c_pointer=adapter_c_pointer,
        current_scale=scale_c_float_array[-1],
    )

    return VegapunkSatellite(
        name=params.name,

        memory=memory,
        knowledge=knowledge,
        skills=skills
    )

 
def _load_memory_and_get_state(model: Llama, params: SatelliteParams):
    sys_msg = create_system_message(params.system_prompt)
    
    print('chegou aqui')

    print(params)
    print(sys_msg)
    model.create_chat_completion(
        messages=[sys_msg],
        tools=params.tools,
        stream=False,
        max_tokens=1
    )

    return model.save_state()
 
def _deploy_vegapunk(model: Llama, params: SatelliteParams) -> VegapunkSatellite:
    model.reset()
    
    adapter_c_pointer = load_adapter_in_memory(model.model, params.adapter_path, params.name)
    
    adapter_pointer_c_array, scale_c_float_array = initialize_adapters(model.ctx, [adapter_c_pointer])

    active_adapter(model.ctx, params.name, [(params.name, adapter_c_pointer)], adapter_pointer_c_array, scale_c_float_array, personalized_scale=1.0)
    
    memory_state =_load_memory_and_get_state(model, params)

    _, scale_c_array = desactive_adapters(
        model.ctx, [(params.name, adapter_c_pointer)], adapter_pointer_c_array, scale_c_float_array,
    )

    return _create_vegapunk_satelite(
        params, memory_state, adapter_c_pointer, scale_c_array
    )

def activate_vegapunk(model: Llama, punk_records: PunkRecords, target_name: str, scale: float = 1.0):

    print(f'ativando o vegapunk {target_name}')

    if punk_records.current_active is not None:
        current = punk_records.satellites[punk_records.current_active]

        current.memory.current_state = model.save_state()
        current.knowledge.is_active = False
        
        current.knowledge.current_scale = 0.0

    name_pointer_tuples = [
        (name, sat.knowledge.knowledge_c_pointer)
        for name, sat in punk_records.satellites.items()
    ]

    model.reset()

    active_adapter(
        model.ctx,
        target_name,
        name_pointer_tuples,
        punk_records.adapters_pointers_c_array,
        punk_records.adapters_scales_c_float_array,
        personalized_scale=scale
    )

    target = punk_records.satellites[target_name]

    model.load_state(target.memory.current_state)

    target.knowledge.is_active = True
    target.knowledge.current_scale = scale

    punk_records.current_active = target_name

   
def reset_vegapunk(target_name: str, punk_records: PunkRecords):

    # aqui é pra limpar somente o contexto e o kv cache, não quero 'desativar'. 

    target = punk_records.satellites[target_name]

    target.memory.messages = []
    target.memory.current_state = target.memory.base_state

    print(f'{target_name} resetado, contexto e estado limpos.')    

 

 


def start_punk_records(model: Llama, adapters_path: str):
    punks_params = [
        SatelliteParams(
            name=sat_p['name'],
            tools=sat_p['skills']['tools'],
            system_prompt=sat_p['skills']['system_prompt'],
            tools_feedbacks=sat_p['skills']['tools_feedback'],
            adapter_path=f'{adapters_path}/{sat_p['adapter_diretory']}/{sat_p['adapter_name']}.gguf',
        ) for sat_p in vegapunks
    ]

    for p in punks_params:
        print(p)
        
    vegapunks_satellites: List[VegapunkSatellite] = [_deploy_vegapunk(model, vp) for vp in punks_params]

    print(f'punks {vegapunks_satellites}')

    adapters_c_pointer_array, adapters_scales_c_float_array = initialize_adapters(
            model.ctx, [p.knowledge.knowledge_c_pointer for p in vegapunks_satellites]
        )
    
    print(len(adapters_c_pointer_array))
    
    punk_records = PunkRecords(
        satellites={p.name: p for p in vegapunks_satellites},
        adapters_pointers_c_array=adapters_c_pointer_array,
        adapters_scales_c_float_array=adapters_scales_c_float_array
    )

    return punk_records 

 

def consult_satellite(model: Llama, punk_records, user_message: str):
    target = punk_records.satellites[punk_records.current_active]

    print(target)
    user_msg = create_user_message(user_message)
    
    target.memory.messages.append(user_msg)

    full_messages = [target.memory.sys_prompt_msg] + target.memory.messages

    chunks = model.create_chat_completion(
        messages=full_messages,
        tools=target.skills.tools or None,
        max_tokens=512,
        stream=True
    )

    raw = ""
    after_think = ""
    think_done = False

    for chunk in chunks:
        delta = chunk['choices'][0]['delta']
        if 'content' not in delta or not delta['content']:
            continue

        token = delta['content']
        raw += token

        if not think_done:
            
            if '</think>' in raw:
                think_done = True
                _, after_think = process_think(raw)

            continue

        after_think += token
        stripped = after_think.strip()

        if not stripped:
            continue

        mode = identify_mode(stripped)
        print(f'modo retornado pelo slm {mode}')

     
        if mode == 'tool':
            tool_data, extra_raw = process_tool(after_think, chunks)
            raw += extra_raw
            target.memory.messages.append({'role': 'assistant', 'content': raw})
            return 'tool_call', tool_data

        else:
            _, extra_raw = process_generate(stripped, chunks)
            raw += extra_raw
            cleaned = (after_think + extra_raw).strip()
            target.memory.messages.append({'role': 'assistant', 'content': raw})
            return 'message', cleaned

    target.memory.messages.append({'role': 'assistant', 'content': raw})
    return 'message', ''
 
