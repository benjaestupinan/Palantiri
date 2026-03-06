def get_memory_context_prompt(search_results: list[dict]) -> str | None:
    if not search_results:
        return None

    lines = ["La siguiente información proviene de conversaciones anteriores con el usuario.",
             "Podés usarla como contexto para enriquecer tu respuesta.\n"]

    for result in search_results:
        date = result.get("created_at", "")[:10]
        role = "Usuario" if result["role"] == "user" else "Asistente"
        lines.append(f"[{date}] {role}: {result['content']}")

    return "\n".join(lines)
