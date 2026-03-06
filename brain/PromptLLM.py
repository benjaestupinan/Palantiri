import os

import requests
from dotenv import load_dotenv

load_dotenv()
host = os.getenv("OLLAMA_HOST")
port = os.getenv("OLLAMA_PORT", "11434")

generate_url = f"http://{host}:{port}/api/generate"
chat_url = f"http://{host}:{port}/api/chat"

def ask_qwen(prompt): # cache que conviene mas con streaming: false
    """
    Envía un prompt a qwen2.5:3b (modelo pequeño y rápido).
    Usado para clasificación de intención y selección de jobs (salida JSON estructurada).
    """
    payload = {
        "model": "qwen2.5:3b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(generate_url, json=payload)
    data = response.json()
    return data["response"]

def ask_chatty(prompt, history=None): # aqui puede ser mejor streaming: true
    """
    Envía un prompt a qwen2.5:7b-instruct (modelo conversacional).
    Usado para respuestas en lenguaje natural y mensajes de fallback.
    Acepta un historial opcional de mensajes previos de la sesión.
    """
    messages = (history or []) + [{"role": "user", "content": prompt}]
    payload = {
        "model": "qwen2.5:7b-instruct",
        "messages": messages,
        "stream": False
    }

    response = requests.post(chat_url, json=payload)
    data = response.json()
    return data["message"]["content"]
