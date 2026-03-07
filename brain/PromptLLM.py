import os

import requests
from dotenv import load_dotenv

load_dotenv()
host = os.getenv("OLLAMA_HOST")
port = os.getenv("OLLAMA_PORT", "11434")

generate_url = f"http://{host}:{port}/api/generate"
chat_url = f"http://{host}:{port}/api/chat"

def ask_qwen(prompt, model="qwen2.5:3b"): # cache que conviene mas con streaming: false
    """
    Envía un prompt a un modelo qwen para salida JSON estructurada.
    Usado para clasificación de intención y selección de jobs.
    Por defecto usa qwen2.5:3b (rápido), acepta un modelo distinto si se necesita mayor precisión.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(generate_url, json=payload)
    data = response.json()
    return data["response"]

def ask_chatty(prompt, history=None, system_prompt=None): # aqui puede ser mejor streaming: true
    """
    Envía un prompt a qwen2.5:7b-instruct (modelo conversacional).
    Usado para respuestas en lenguaje natural y mensajes de fallback.
    Acepta un historial opcional de mensajes previos de la sesión y un
    system prompt opcional para inyectar contexto externo.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages += (history or []) + [{"role": "user", "content": prompt}]

    payload = {
        "model": "lens",
        "messages": messages,
        "stream": False
    }

    response = requests.post(chat_url, json=payload)
    data = response.json()
    return data["message"]["content"]
