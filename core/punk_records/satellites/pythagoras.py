def get_weather(args, punk_records):
    city = args['city']
    return f"25 graus celsius em {city}"


def switch_satellite(args, punk_records):
    from core.punk_records.punk_records import activate_vegapunk
    target = args['target']
    activate_vegapunk(punk_records, target)
    return f'trocado para {target}'


tools = [
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
    },
    {
        "type": "function",
        "function": {
            "name": "switch_satellite",
            "description": "Delega a conversa para outro assistente vegapunk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "enum": ["edson", "shaka"],
                        "description": "Nome do assistente para delegar."
                    }
                },
                "required": ["target"]
            }
        }
    }
]

tools_exec = {
    'get_weather': {
        'fn': get_weather,
        'before': 'consultando a previsão do tempo em {city}, aguarde um instante!',
        'after': 'a previsão do tempo em {city} é {result}',
        'error': 'não consegui consultar o tempo em {city}',
    },
    'switch_satellite': {
        'fn': switch_satellite,
        'before': 'trocando para {target}!',
        'after': 'pronto, agora você está falando com {target}.',
        'error': 'não consegui trocar para {target}',
    },
}

system_prompt = (
    'Você é o Pythagoras, fala somente português brasileiro. '
    'Você pode consultar a previsão do tempo e delegar para outros assistentes: edson e shaka. '
    'Nunca tente delegar para si mesmo.'
)

config = {
    'name': 'pythagoras',
    'adapter_directory': 'pythagoras',
    'adapter_name': 'pythagoras',
    'system_prompt': system_prompt,
    'tools': tools,
    'tools_exec': tools_exec,
}
