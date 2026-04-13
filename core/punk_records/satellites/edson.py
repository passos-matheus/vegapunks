from core.punk_records.dataclasses import VegapunkPresentation


def get_weather(args, punk_records):
    city = args['city']
    return f"25 graus celsius em {city}"


def switch_satellite(args, punk_records):
    from core.punk_records.punk_records import activate_vegapunk
    target = args['target']
    activate_vegapunk(punk_records, target)
    return f'trocado para {target}'


def clear_context(args, punk_records):
    from core.punk_records.punk_records import reset_vegapunk
    name = punk_records.current_active
    reset_vegapunk(punk_records, name)
    return f'contexto de {name} limpo'


def shutdown(args, punk_records):
    punk_records.shutdown_event.set()
    return 'desligando'


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
                        "enum": ["shaka", "pythagoras"],
                        "description": "Nome do assistente para delegar."
                    }
                },
                "required": ["target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_context",
            "description": "Limpa o contexto e histórico da conversa atual, resetando o assistente.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown",
            "description": "Desativa o assistente até ser chamado novamente pela palavra de ativação.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
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
    'clear_context': {
        'fn': clear_context,
        'before': 'limpando meu contexto...',
        'after': 'pronto, contexto limpo! como posso ajudar?',
        'error': 'não consegui limpar o contexto',
    },
    'shutdown': {
        'fn': shutdown,
        'before': 'desligando...',
        'after': 'até mais, mestre!',
        'error': 'não consegui desligar',
    },
}

system_prompt = (
    'Você é o Edson, fala somente português brasileiro. '
    'Você pode consultar a previsão do tempo e delegar para outros assistentes: shaka e pythagoras. '
    'Nunca tente delegar para si mesmo. '
    'Você pode limpar seu contexto de conversa e desligar quando solicitado.'
)

appearance = VegapunkPresentation(
    eyelid_color=(50, 205, 50),
    mouth_color=(255, 200, 0),
    eye_width=90,
    eye_height=100,
    eye_distance=160,
    eye_y_offset=-100,
    iris_radius=18,
    base_eyelid=0,
    has_mouth=True,
    voice_pitch_semitones=0.0,
    voice_speed=1.0,
)

config = {
    'name': 'edson',
    'adapter_directory': 'edson',
    'adapter_name': 'edson',
    'system_prompt': system_prompt,
    'tools': tools,
    'tools_exec': tools_exec,
    'appearance': appearance,
}
