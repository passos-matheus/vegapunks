

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llama_cpp import Llama, LlamaState

from modules.slm import create_generation_model, _load_adapter_in_memory, _initialize_adapters, active_adapter, desactive_adapters

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
class SatelliteKnowledge:
    state: LlamaState
    adapter_pointer: Any

class SatelliteAppearance:
    pass

class SatellitePersonallity:
    pass

@dataclass
class VegapunkSatellite:
        name: str
        skills: SatelliteSkills
        knowledge: SatelliteKnowledge

        appearance = None
        personallity = None


@dataclass
class VegapunkSatellitesManager:
    satellites: dict[str, VegapunkSatellite]       
    

 
slm = create_generation_model()

def warmup_agent(model: Llama, params: SatelliteParams):
    model.reset()
    
    adapter_pointer = _load_adapter_in_memory(model.model, params.adapter_path, params.name)
    adapter_tuple = [(params.name, adapter_pointer)]
 
    adapter_pointer_c_array, scale_c_float_array =_initialize_adapters(model.ctx, adapter_tuple)
    print('aaaaaaaaaa')
    actived_adapter, current_actived_adapter_scale = active_adapter(model.ctx, params.name, adapter_tuple, adapter_pointer_c_array, scale_c_float_array, personalized_scale=1.0)
    print('aaaaaaaaaa')
   
    print(actived_adapter)
    print(current_actived_adapter_scale)

    print('deu certo os adapters!')

    tokens = model.tokenize(text=params.system_prompt.encode())
    print(f"tokens: {len(tokens)}, n_ctx: {model.n_ctx()}")
 
    print('bbbbbbbbbbbb')

    model.eval(tokens)
 
    state = model.save_state()
 

    skills = SatelliteSkills(
        sys_prompt=params.system_prompt,
        tools=params.tools
    )

    know = SatelliteKnowledge(
        state=state,
        adapter_pointer=adapter_pointer
    )

    satellite = VegapunkSatellite(
        name=params.name,
        knowledge=know,
        skills=skills
    )

    desactived_adapters = desactive_adapters(
        model.ctx, adapter_tuple, adapter_pointer_c_array, scale_c_float_array,
    )

    print(desactived_adapters)

    return satellite

   

    

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

vegapunk_1 = warmup_agent(slm, _params)
vegapunk_2 = warmup_agent(slm, _params_2)
vegapunk_3 = warmup_agent(slm, _params_3)

print(vegapunk_1.knowledge.state.n_tokens)
print(vegapunk_2.knowledge.state.n_tokens)
print(vegapunk_3.knowledge.state.n_tokens)


vps = {
    'punk1': vegapunk_1,
    'punk2': vegapunk_2,
    'punk3': vegapunk_3
}

manager = VegapunkSatellitesManager(satellites=vps)

print(manager.satellites['punk1'].name)

# TO-DO amanhã, criar as funções pra trocar de vegapunk, manter scales atuais de cada um na classe manager pra saber qual ta ativo, criar função de inicializar todos.
