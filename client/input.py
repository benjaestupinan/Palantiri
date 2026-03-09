def get_input() -> str:
    return input("msg: ")


def get_feedback() -> bool:
    while True:
        answer = input("¿funcionó? (yes/no): ").strip().lower()
        if answer in ("yes", "no"):
            return answer == "yes"
