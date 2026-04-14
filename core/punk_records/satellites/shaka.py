from core.punk_records.dataclasses import VegapunkPresentation


PENDING = [
    'estudar tilling',
    'aprender a fazer tilling na mão',
    'revisar álgebra',
    'Revisar redes',
]


def list_pending(args, punk_records):
    return ', '.join(PENDING)


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
            "name": "list_pending",
            "description": "Lista o que está pendente no planejamento do usuário.",
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
                        "enum": ["edson", "pythagoras"],
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
    'list_pending': {
        'fn': list_pending,
        'before': 'vou verificar o que está pendente...',
        'after': 'suas pendências são: {result}',
        'error': 'não consegui buscar as pendências',
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
    'Você é o Shaka, fala somente português brasileiro. '
    'Você é focado em planejamento: ajuda o usuário a saber o que ele tem pendente e o que fazer em seguida. '
    'Pode listar pendências e delegar para outros assistentes: edson (estudos) e pythagoras (revisões). '
    'Nunca tente delegar para si mesmo. '
    'Você pode limpar seu contexto de conversa e desligar quando solicitado. '
    'Quando for chamar uma ferramenta, emita <tool_call> imediatamente, sem explicar ou justificar antes.'
)

appearance = VegapunkPresentation(
    eyelid_color=(100, 150, 255),
    mouth_color=(0, 0, 0),
    eye_width=150,
    eye_height=150,
    eye_distance=110,
    eye_y_offset=-75,
    iris_radius=14,
    base_eyelid=45,
    has_mouth=False,
    voice_pitch_semitones=3.0,
    voice_speed=1.05,
)

config = {
    'name': 'shaka',
    'adapter_directory': 'shaka',
    'adapter_name': 'shaka',
    'system_prompt': system_prompt,
    'tools': tools,
    'tools_exec': tools_exec,
    'appearance': appearance,
    'adapter_scale': 0.1,
}
