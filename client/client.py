from client.input import get_input
from client.output import play_audio
from client.server import send_message


def main():
    session_id = None
    while True:
        message = get_input()
        session_id, text, audio = send_message(session_id, message)
        print(f"lens: {text}")
        play_audio(audio)
        if session_id is None:
            session_id = None  # sesión terminada, la próxima crea una nueva


if __name__ == "__main__":
    main()
