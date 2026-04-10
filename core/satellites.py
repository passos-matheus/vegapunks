
edson_system_prompt = 'você só fala português e consulta a previsão do tempo.'
edson_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Retorna a previsão do tempo para uma cidade específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nome da cidade, ex: 'São Paulo'"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

edson_tools_feedback = {
    'name': 'get_weather',
    'before': 'consultando a previsão do tempo em {C}, aguardade um instante!',
    'after': 'a previsão do tempo em {C} é {R}'
}

shaka_system_prompt = 'você só fala português e consulta a previsão do tempo.'
shaka_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Retorna a previsão do tempo para uma cidade específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nome da cidade, ex: 'São Paulo'"
                    }
                },
                "required": ["city"]
            }
        }
    }
]
shaka_tools_feedback = {
    'name': 'get_weather',
    'before': 'consultando a previsão do tempo em {C}, aguardade um instante!',
    'after': 'a previsão do tempo em {C} é {R}'
}


pythagoras_system_prompt = 'você só fala português e consulta a previsão do tempo.'
pythagoras_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Retorna a previsão do tempo para uma cidade específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nome da cidade, ex: 'São Paulo'"
                    }
                },
                "required": ["city"]
            }
        }
    }
]
pythagoras_tools_feedback = {
    'name': 'get_weather',
    'before': 'consultando a previsão do tempo em {C}, aguardade um instante!',
    'after': 'a previsão do tempo em {C} é {R}'
}



edson = {
    'name': 'edson',
    'adapter_name': 'edson',
    'adapter_diretory': 'edson',
    'skills': {
        'system_prompt': edson_system_prompt,
        'tools': edson_tools,
        'tools_feedback': edson_tools_feedback
    }
}

shaka = {
    'name': 'shaka',
    'adapter_name': 'shaka',
    'adapter_diretory': 'shaka',
    'skills': {
        'system_prompt': shaka_system_prompt,
        'tools': shaka_tools,
        'tools_feedback': shaka_tools_feedback
    }
}

pythagoras = {
    'name': 'pythagoras',
    'adapter_name': 'pythagoras',
    'adapter_diretory': 'pythagoras',
    'skills': {
        'system_prompt': pythagoras_system_prompt,
        'tools': pythagoras_tools,
        'tools_feedback': pythagoras_tools_feedback
    }
}

vegapunks = [edson, shaka, pythagoras]
