from dataclasses import dataclass
from typing import Any
from llama_cpp import Llama, LlamaState


@dataclass
class SatelliteParams:
    name: str
    tools: Any
    tools_exec: dict
    adapter_path: str
    system_prompt: str


@dataclass
class SatelliteSkills:
    sys_prompt: str
    tools: Any
    tools_exec: dict


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


@dataclass
class VegapunkSatellite:
    name: str
    skills: SatelliteSkills
    memory: SatelliteMemory
    knowledge: SatelliteKnowledge


@dataclass
class PunkRecords:
    model: Llama
    satellites: dict[str, VegapunkSatellite]
    adapters_pointers_c_array: Any
    adapters_scales_c_float_array: Any
    current_active: str = None
