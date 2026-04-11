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
                        "enum": ["edson", "pythagoras"],
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
        'after': 'a previsão do tempo é {result}',
        'error': 'não consegui consultar o tempo em {city}, deixa eu tentar de ovo',
    },
    'switch_satellite': {
        'fn': switch_satellite,
        'before': 'trocando para {target}!',
        'after': 'pronto, agora você está falando com {target}.',
        'error': 'não consegui trocar para {target}, deixa eu tentar de novo.',
    },
}

system_prompt = (
    'Você é o Shaka, fala somente português brasileiro. '
    'Você pode consultar a previsão do tempo e delegar para outros assistentes: edson e pythagoras. '
    'Nunca tente delegar para si mesmo.'
)

config = {
    'name': 'shaka',
    'adapter_directory': 'shaka',
    'adapter_name': 'shaka',
    'system_prompt': system_prompt,
    'tools': tools,
    'tools_exec': tools_exec,
}
