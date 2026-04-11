import threading
from dataclasses import dataclass, field
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
class VegapunkPresentation:
    eyelid_color: tuple
    mouth_color: tuple
    eye_width: float
    eye_height: float
    eye_distance: float
    eye_y_offset: float
    iris_radius: float
    base_eyelid: float
    has_mouth: bool
    eye_color: tuple = (255, 255, 255)
    iris_color: tuple = (0, 0, 0)
    background_color: tuple = (10, 10, 10)
    voice_id: str = None


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
    shutdown_event: threading.Event = field(default_factory=threading.Event)
    face_queue: Any = None
