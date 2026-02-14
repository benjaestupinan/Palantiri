import os

import requests
from dotenv import load_dotenv

load_dotenv()
host = os.getenv("OLLAMA_HOST")
port = os.getenv("OLLAMA_PORT", "11434")

url = f"http://{host}:{port}/api/generate"

def ask_qwen(prompt): # cache que conviene mas con streaming: false
    payload = {
        "model": "qwen2.5:3b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=payload)
    data = response.json()
    return data["response"]
    
def ask_chatty(prompt): # aqui puede ser mejor streaming: true
    payload = {
        "model": "qwen2.5:7b-instruct",
        "prompt": prompt,
        "stream": False # Cambiar a True en algun futuro, ahora no lo pude implementar :(
    }

    response = requests.post(url, json=payload)
    data = response.json()
    return data["response"]
