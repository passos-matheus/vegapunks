import asyncio

from typing import List
from llama_cpp import Llama, LlamaState

from modules.slm import (
    create_user_message,
    identify_mode,
    load_adapter_in_memory,
    initialize_adapters,
    active_adapter,
    desactive_adapters,
    create_system_message,
    process_generate,
    process_think,
    process_tool,
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
    )

    return VegapunkSatellite(
        name=params.name,
        memory=memory,
        knowledge=knowledge,
        skills=skills,
    )


def _load_memory_and_get_state(model: Llama, params: SatelliteParams):
    sys_msg = create_system_message(params.system_prompt)

    model.create_chat_completion(
        messages=[sys_msg],
        tools=params.tools,
        stream=False,
        max_tokens=1,
    )

    return model.save_state()


def _deploy_vegapunk(model: Llama, params: SatelliteParams) -> VegapunkSatellite:
    model.reset()

    adapter_c_pointer = load_adapter_in_memory(model.model, params.adapter_path, params.name)

    adapter_pointer_c_array, scale_c_float_array = initialize_adapters(model.ctx, [adapter_c_pointer])

    active_adapter(model.ctx, params.name, [(params.name, adapter_c_pointer)], adapter_pointer_c_array, scale_c_float_array, personalized_scale=1.0)

    memory_state = _load_memory_and_get_state(model, params)

    _, scale_c_array = desactive_adapters(
        model.ctx, [(params.name, adapter_c_pointer)], adapter_pointer_c_array, scale_c_float_array,
    )

    return _create_vegapunk_satelite(
        params, memory_state, adapter_c_pointer, scale_c_array
    )


def activate_vegapunk(punk_records: PunkRecords, target_name: str, scale: float = 1.0):
    model = punk_records.model

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
        personalized_scale=scale,
    )

    target = punk_records.satellites[target_name]

    model.load_state(target.memory.current_state)

    target.knowledge.is_active = True
    target.knowledge.current_scale = scale

    punk_records.current_active = target_name


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

def _send_to_tts(text, output_queue, loop):
    if output_queue is not None and loop is not None:
        asyncio.run_coroutine_threadsafe(output_queue.put(text), loop)
    else:
        print(text)


def _safe_tool_exec(fn, tool_args, punk_records):
    try:
        result = fn(tool_args, punk_records)
        print(result)
        return None, result
    
    except Exception as e:
        print(f'[tool_error] {e}')
        return str(e), None
    

def consult_satellite(punk_records: PunkRecords, user_message: str, output_queue=None, loop=None, _is_retry=False):

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

        if mode == 'tool':
            tool_data, extra_raw = process_tool(after_think, chunks)
            raw += extra_raw
            target.memory.messages.append({'role': 'assistant', 'content': raw})

            if tool_data is not None:
                tool_name = tool_data['name']
                tool_args = tool_data['arguments']
                tool_exec = target.skills.tools_exec.get(tool_name)

                if tool_exec:
                    before_text = _format_tool_feedback(tool_exec['before'], tool_args)
                    _send_to_tts(before_text, output_queue, loop)

                    error, result = _safe_tool_exec(tool_exec['fn'], tool_args, punk_records)

                    if error is None:
                        
                        after_text = _format_tool_feedback(tool_exec['after'], tool_args, result=result)

                        _send_to_tts(after_text, output_queue, loop)
                        
                        target.memory.messages.append({'role': 'tool', 'content': str(result)})

                    else:
                        
                        error_text = _format_tool_feedback(tool_exec['error'], tool_args)
                        
                        _send_to_tts(error_text, output_queue, loop)

                        target.memory.messages.append({'role': 'tool', 'content': f'error: {error}'})
                        target.memory.messages.append({'role': 'user', 'content': f'a tool retornou um erro: {error}'})

                        return 'error', tool_data
                else:
                    print(f'tool {tool_name} não encontrada em tools_exec, fazendo nada')

            return 'tool_call', tool_data

        else:
            _, extra_raw = process_generate(stripped, chunks, on_sentence=lambda text: _send_to_tts(text, output_queue, loop))
            raw += extra_raw
            cleaned = (after_think + extra_raw).strip()
            target.memory.messages.append({'role': 'assistant', 'content': raw})
            return 'message', cleaned

    target.memory.messages.append({'role': 'assistant', 'content': raw})
    return 'message', ''


async def reconsult_satellite(punk_records: PunkRecords, user_message: str, output_queue=None, loop=None):
    result_type, data = await loop.run_in_executor(
        None, consult_satellite, punk_records, user_message, output_queue, loop
    )

    if result_type != 'error':
        return result_type, data

    result_type, data = await loop.run_in_executor(
        None, lambda: consult_satellite(punk_records, '', output_queue, loop, _is_retry=True)
    )

    if result_type != 'error':
        return result_type, data

    target_name = punk_records.current_active
    reset_vegapunk(punk_records, target_name)
    _send_to_tts('realmente não consegui realizar essa ação', output_queue, loop)
    return 'error', None
