from client.input import get_input, get_feedback
from client.output import play_audio
from client.server import send_message, send_feedback


def main():
    session_id = None
    while True:
        message = get_input()
        session_id, text, audio, flow_id = send_message(session_id, message)
        print(f"lens: {text}")
        play_audio(audio)
        ok = get_feedback()
        send_feedback(flow_id, ok)


if __name__ == "__main__":
    main()
