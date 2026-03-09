import os

import requests
from dotenv import load_dotenv

load_dotenv()

_HOST = os.getenv("PIPELINE_HOST")
_PORT = os.getenv("PIPELINE_PORT", "8084")
_BASE_URL = f"http://{_HOST}:{_PORT}"


def send_message(session_id: str | None, message: str) -> tuple[str | None, str, str]:
    """Returns (session_id, text, audio_b64)."""
    response = requests.post(f"{_BASE_URL}/message", json={
        "session_id": session_id,
        "message": message,
    })
    response.raise_for_status()
    data = response.json()
    return data["session_id"], data["text"], data["audio"]
