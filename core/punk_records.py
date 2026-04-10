

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from llama_cpp import Llama, LlamaState

from modules.slm import create_generation_model, load_adapter_in_memory, initialize_adapters, active_adapter, desactive_adapters

@dataclass
class SatelliteParams:
    name: str
    tools: Any
    adapter_path: Any
    system_prompt: str
     

     

    
    
   

@dataclass
class SatelliteSkills:
    sys_prompt: str
    tools: str

@dataclass
class SatelliteMemory:
    state: LlamaState



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

 
slm = create_generation_model()


def _create_vegapunk_satelite(params, memory_state, adapter_c_pointer, scale_c_float_array):

    skills = SatelliteSkills(
        sys_prompt=params.system_prompt,
        tools=params.tools
    )

    memory = SatelliteMemory(
        state=memory_state
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

 
def _load_memory_and_get_state(model, sys_prompt):
    tokens = model.tokenize(text=sys_prompt.encode())
    model.eval(tokens)

    return model.save_state()
 
def _deploy_vegapunk(model: Llama, params: SatelliteParams) -> VegapunkSatellite:
    model.reset()
    
    adapter_c_pointer = load_adapter_in_memory(model.model, params.adapter_path, params.name)
    
    adapter_pointer_c_array, scale_c_float_array = initialize_adapters(model.ctx, [adapter_c_pointer])

    active_adapter(model.ctx, params.name, [(params.name, adapter_c_pointer)], adapter_pointer_c_array, scale_c_float_array, personalized_scale=1.0)
    
    memory_state =_load_memory_and_get_state(model, params.system_prompt)

    _, scale_c_array = desactive_adapters(
        model.ctx, [(params.name, adapter_c_pointer)], adapter_pointer_c_array, scale_c_float_array,
    )

    return _create_vegapunk_satelite(
        params, memory_state, adapter_c_pointer, scale_c_array
    )

   
def start_punk_records(model: Llama, vegapunks: List[SatelliteParams]):
    punks: List[VegapunkSatellite] = []

    for vp in vegapunks:
        punks.append(_deploy_vegapunk(model, vp))

    print(f'punks')
    adapters_c_pointer_array, adapters_scales_c_float_array = initialize_adapters(
            model.ctx, [p.knowledge.knowledge_c_pointer for p in punks]
        )
    
    print(len(adapters_c_pointer_array))
    
    punk_records = PunkRecords(
        satellites={p.name: p for p in punks},
        adapters_pointers_c_array=adapters_c_pointer_array,
        adapters_scales_c_float_array=adapters_scales_c_float_array
    )

    return punk_records


def _load_skills():
    pass


def _load_knowledge():
    pass


def startup_satelite(model, sattelite):



    pass

def switch_to_satellite():
   
    _load_skills()
    _load_knowledge()
    # _load_personallity() usar pra voz.
    

def delegate_to_satellite():
    
    # usar pra que o manager / shaka possa enviar uma tarefa pra um sateline específico sem eu precisar especificar. 
    
    
    pass


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = str(BASE_DIR / "models/slm/qwen-3-0.6B")

ADAPTERS_DIR = f"{MODEL_DIR}/lora_adapters"
MODEL_PATH = f"{MODEL_DIR}/Qwen3-0.6B-Q8_0.gguf"

_params = SatelliteParams('adapter_b', tools='', adapter_path=f'{ADAPTERS_DIR}/adapter_b/adapter_b.gguf', system_prompt='Você é o Edson, e fala somente português brasileiro!')
_params_2 = SatelliteParams('adapter_c', tools='', adapter_path=f'{ADAPTERS_DIR}/adapter_c/adapter_c.gguf', system_prompt='Você é o Pythagoras, e fala somente português brasileiro! Você é focado em planejar.')
_params_3 = SatelliteParams('adapter_a', tools='', adapter_path=f'{ADAPTERS_DIR}/adapter_v8/adapter_v8.gguf', system_prompt='Você é o shaka, e fala somente português brasileiro! Você é focado em estudos e pesquisar e também gosta muito de matemática.')

punk_recors = start_punk_records(slm, [_params, _params_2, _params_3])

print(punk_recors)

# TO-DO amanhã, criar as funções pra trocar de vegapunk manter scales atuais de cada um na classe manager pra saber qual ta ativo, criar função de inicializar todos.
