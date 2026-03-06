import os

import requests
from dotenv import load_dotenv

load_dotenv()

MEMORY_HOST = os.getenv("MEMORY_HOST")
MEMORY_PORT = os.getenv("MEMORY_PORT", "8082")
BASE_URL = f"http://{MEMORY_HOST}:{MEMORY_PORT}"


def create_session() -> str | None:
    try:
        response = requests.post(f"{BASE_URL}/session", timeout=3)
        response.raise_for_status()
        return response.json()["session_id"]
    except Exception as e:
        print(f"[memory] create_session failed: {e}")
        return None


def save_message(session_id: str, role: str, content: str):
    try:
        requests.post(
            f"{BASE_URL}/message",
            json={"session_id": session_id, "role": role, "content": content},
            timeout=3,
        )
    except Exception as e:
        print(f"[memory] save_message failed: {e}")


def get_history(session_id: str, n: int = 10) -> list[dict]:
    try:
        response = requests.get(
            f"{BASE_URL}/session/{session_id}/messages",
            params={"n": n},
            timeout=3,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[memory] get_history failed: {e}")
        return []


def search(query: str, limit: int = 5) -> list[dict]:
    try:
        response = requests.get(
            f"{BASE_URL}/search",
            params={"q": query, "limit": limit},
            timeout=3,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[memory] search failed: {e}")
        return []
