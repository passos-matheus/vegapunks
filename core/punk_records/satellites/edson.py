def get_weather(args):
    city = args['city']
    return f"25°C em {city}"


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
    }
]

tools_exec = {
    'get_weather': {
        'fn': get_weather,
        'before': 'consultando a previsão do tempo em {city}, aguarde um instante!',
        'after': 'a previsão do tempo em {city} é {result}',
    }
}

system_prompt = 'você só fala português e consulta a previsão do tempo.'

config = {
    'name': 'edson',
    'adapter_directory': 'edson',
    'adapter_name': 'edson',
    'system_prompt': system_prompt,
    'tools': tools,
    'tools_exec': tools_exec,
}
