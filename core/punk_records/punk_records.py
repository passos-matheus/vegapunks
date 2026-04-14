import asyncio
import pickle

from pathlib import Path
from typing import List
from modules.face import send_face
from llama_cpp import Llama, LlamaState

from modules.slm import (
    create_user_message,
    load_adapter_in_memory,
    initialize_adapters,
    active_adapter,
    desactive_adapters,
    create_system_message,
    compute_state_hash,
    process_stream,
)

from core.punk_records.dataclasses import (
    SatelliteParams,
    SatelliteSkills,
    SatelliteMemory,
    SatelliteKnowledge,
    VegapunkSatellite,
    PunkRecords,
)

from core.punk_records.satellites import vegapunks


def _create_vegapunk_satelite(params: SatelliteParams, memory_state: LlamaState, adapter_c_pointer, scale_c_float_array):

    skills = SatelliteSkills(
        sys_prompt=params.system_prompt,
        tools=params.tools,
        tools_exec=params.tools_exec,
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
        configured_scale=params.adapter_scale,
    )

    return VegapunkSatellite(
        name=params.name,
        memory=memory,
        knowledge=knowledge,
        skills=skills,
        presentation=params.appearance,
    )


def _load_memory_and_get_state(model: Llama, params: SatelliteParams):
    cache_dir = Path(params.adapter_path).parent
    cache_path = cache_dir / f"cached_base_state_{params.name}.pkl"
    current_hash = compute_state_hash(params.adapter_path, params.system_prompt, params.tools)

    if cache_path.exists():
        with open(cache_path, 'rb') as f:
            cache_data = pickle.load(f)

        if cache_data['hash'] == current_hash:
            print(f'{params.name}: base state carregado do cache')
            return cache_data['state']

        print(f'{params.name}: hash mudou, regenerando cache...')

    sys_msg = create_system_message(params.system_prompt)

    model.create_chat_completion(
        messages=[sys_msg],
        tools=params.tools,
        stream=False,
        max_tokens=1,
    )

    state = model.save_state()

    with open(cache_path, 'wb') as f:
        pickle.dump({'hash': current_hash, 'state': state}, f)

    print(f'{params.name}: base state salvo em cache ({cache_path.name})')
    return state


def _deploy_vegapunk(model: Llama, params: SatelliteParams) -> VegapunkSatellite:
    model.reset()

    adapter_c_pointer = load_adapter_in_memory(model.model, params.adapter_path, params.name)

    adapter_pointer_c_array, scale_c_float_array = initialize_adapters(model.ctx, [adapter_c_pointer])

    active_adapter(model.ctx, params.name, [(params.name, adapter_c_pointer)], adapter_pointer_c_array, scale_c_float_array, personalized_scale=params.adapter_scale)

    memory_state = _load_memory_and_get_state(model, params)

    _, scale_c_array = desactive_adapters(
        model.ctx, [(params.name, adapter_c_pointer)], adapter_pointer_c_array, scale_c_float_array,
    )

    return _create_vegapunk_satelite(
        params, memory_state, adapter_c_pointer, scale_c_array
    )


def activate_vegapunk(punk_records: PunkRecords, target_name: str, scale: float = None):
    if target_name not in punk_records.satellites:
        raise Exception(f'vegapunk {target_name} não existe')

    model = punk_records.model

    if scale is None:
        scale = punk_records.satellites[target_name].knowledge.configured_scale

    print(f'ativando o vegapunk {target_name} (scale={scale})')

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
        personalized_scale=scale,
    )

    target = punk_records.satellites[target_name]

    model.load_state(target.memory.current_state)

    target.knowledge.is_active = True
    target.knowledge.current_scale = scale

    punk_records.current_active = target_name

    if punk_records.face_queue is not None:
        send_face(punk_records.face_queue, "mode", target_name)


def reset_vegapunk(punk_records: PunkRecords, target_name: str):
    target = punk_records.satellites[target_name]

    target.memory.messages = []
    target.memory.current_state = target.memory.base_state

    print(f'{target_name} resetado, contexto e estado limpos.')


def start_punk_records(model: Llama, adapters_path: str):
    punks_params = [
        SatelliteParams(
            name=cfg['name'],
            tools=cfg['tools'],
            tools_exec=cfg['tools_exec'],
            system_prompt=cfg['system_prompt'],
            adapter_path=f"{adapters_path}/{cfg['adapter_directory']}/{cfg['adapter_name']}.gguf",
            appearance=cfg.get('appearance'),
            adapter_scale=cfg.get('adapter_scale', 1.0),
        ) for cfg in vegapunks
    ]

    vegapunks_satellites: List[VegapunkSatellite] = [_deploy_vegapunk(model, vp) for vp in punks_params]

    adapters_c_pointer_array, adapters_scales_c_float_array = initialize_adapters(
        model.ctx, [p.knowledge.knowledge_c_pointer for p in vegapunks_satellites]
    )

    punk_records = PunkRecords(
        model=model,
        satellites={p.name: p for p in vegapunks_satellites},
        adapters_pointers_c_array=adapters_c_pointer_array,
        adapters_scales_c_float_array=adapters_scales_c_float_array,
    )

    return punk_records


def _format_tool_feedback(template, tool_args, result=None):
    format_args = {**tool_args}
    if result is not None:
        format_args['result'] = result
    return template.format(**format_args)

def _voice_params_for(punk_records):
    if punk_records is None or punk_records.current_active is None:
        return None

    target = punk_records.satellites.get(punk_records.current_active)
    if target is None or target.presentation is None:
        return None

    return {
        'pitch': target.presentation.voice_pitch_semitones,
        'speed': target.presentation.voice_speed,
    }


def _send_to_tts(text, output_queue, loop, punk_records=None, face_queue=None):
    if output_queue is not None and loop is not None:
        voice_params = _voice_params_for(punk_records)
        asyncio.run_coroutine_threadsafe(output_queue.put((text, voice_params)), loop)
    else:
        print(text)
    if face_queue is not None:
        send_face(face_queue, "state", "speaking")


def _safe_tool_exec(fn, tool_args, punk_records):
    try:
        result = fn(tool_args, punk_records)
        print(result)
        return None, result
    
    except Exception as e:
        print(f'[tool_error] {e}')
        return str(e), None
    

def consult_satellite(punk_records: PunkRecords, user_message: str, output_queue=None, loop=None, _is_retry=False):
    print(f'mensagem recebida: {user_message}')

    if output_queue is None or loop is None:
        raise Exception('output queue ou loop n enviado!')

    model = punk_records.model
    target = punk_records.satellites[punk_records.current_active]

    if not _is_retry:
        user_msg = create_user_message(user_message)
        target.memory.messages.append(user_msg)

    full_messages = [target.memory.sys_prompt_msg] + target.memory.messages

    chunks = model.create_chat_completion(
        messages=full_messages,
        tools=target.skills.tools or None,
        max_tokens=512,
        stream=True,
    )

    on_sentence = lambda text: _send_to_tts(
        text, output_queue, loop,
        punk_records=punk_records, face_queue=punk_records.face_queue,
    )

    mode, tool_data, raw = process_stream(chunks, on_sentence)
    target.memory.messages.append({'role': 'assistant', 'content': raw})

    if mode != 'tool':
        return 'message', raw.strip()

    if tool_data is None:
        return 'tool_call', None

    tool_name = tool_data['name']
    tool_args = tool_data['arguments']
    tool_exec = target.skills.tools_exec.get(tool_name)

    if not tool_exec:
        print(f'tool {tool_name} não encontrada em tools_exec, fazendo nada')
        return 'tool_call', tool_data

    before_text = _format_tool_feedback(tool_exec['before'], tool_args)
    _send_to_tts(before_text, output_queue, loop, punk_records=punk_records, face_queue=punk_records.face_queue)

    error, result = _safe_tool_exec(tool_exec['fn'], tool_args, punk_records)

    if error is None:
        after_text = _format_tool_feedback(tool_exec['after'], tool_args, result=result)
        _send_to_tts(after_text, output_queue, loop, punk_records=punk_records, face_queue=punk_records.face_queue)
        reset_vegapunk(punk_records, punk_records.current_active)
        return 'tool_call', tool_data

    error_text = _format_tool_feedback(tool_exec['error'], tool_args)
    _send_to_tts(error_text, output_queue, loop, punk_records=punk_records, face_queue=punk_records.face_queue)

    target.memory.messages.append({'role': 'tool', 'content': f'error: {error}'})
    target.memory.messages.append({'role': 'user', 'content': f'a tool retornou um erro: {error}'})

    return 'error', tool_data


async def reconsult_satellite(punk_records: PunkRecords, user_message: str, output_queue=None, loop=None):
    result_type, data = await loop.run_in_executor(
        None, consult_satellite, punk_records, user_message, output_queue, loop
    )

    if result_type != 'error':
        return result_type, data

    result_type, data = await loop.run_in_executor(
        None, lambda: consult_satellite(punk_records, 'verifique os parâmetros e tente de novo, confirme com o usuário se eles estão corretos de fato.', output_queue, loop, _is_retry=True)
    )

    if result_type != 'error':
        return result_type, data

    target_name = punk_records.current_active
    reset_vegapunk(punk_records, target_name)
    _send_to_tts('realmente não consegui realizar essa ação', output_queue, loop, punk_records=punk_records, face_queue=punk_records.face_queue)
    return 'error', None
