from core.punk_records.dataclasses import VegapunkPresentation


STUDIES = [
    'Arquitetura de Redes',
    'Tilling',
    'Linguagens formais e automatos',
    'álgebra linear',
]


def list_studies(args, punk_records):
    return ', '.join(STUDIES)


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
            "name": "list_studies",
            "description": "Lista os últimos estudos do usuário.",
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
    'list_studies': {
        'fn': list_studies,
        'before': 'deixa eu olhar os últimos estudos...',
        'after': 'seus últimos estudos foram: {result}',
        'error': 'não consegui buscar os últimos estudos',
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
    'Você é focado em estudos: ajuda o usuário a lembrar e revisar o que ele tem estudado. '
    'Pode listar os últimos estudos e delegar para outros assistentes: shaka (planejamento) e pythagoras (revisões). '
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
    'adapter_scale': 0.1,
}
