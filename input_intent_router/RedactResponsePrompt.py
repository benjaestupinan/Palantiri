import re

def get_response_message_prompt(user_input, execution_result):
    """
    Construye un prompt limpio para el modelo chatty
    a partir del input del usuario y el resultado del executor.
    """

    # --- Parse determinístico ---
    failed_match = re.search(r"Failed:\s*(true|false)", execution_result, re.IGNORECASE)
    message_match = re.search(r"Message:\s*(.+)", execution_result)
    output_match = re.search(r"Output:\s*(.+)", execution_result)

    failed = failed_match.group(1).lower() == "true" if failed_match else True
    message = message_match.group(1).strip() if message_match else ""
    output = output_match.group(1).strip() if output_match else ""

    # --- Construcción del prompt controlado ---
    if not failed:
        prompt = f"""
Eres un asistente que debe responder en lenguaje natural al usuario.

El usuario preguntó:
\"{user_input}\"

La ejecución fue exitosa.
Resultado obtenido:
\"{output}\"

Responde de forma clara y directa.
No inventes información.
No menciones detalles técnicos internos.
"""
    else:
        prompt = f"""
Eres un asistente que debe explicar errores en lenguaje natural.

El usuario pidió:
\"{user_input}\"

La ejecución falló.
Mensaje técnico:
\"{message}\"

Output de la ejecución:
\"{output}\"

Explica el error de forma clara.
No inventes información.
No menciones estructuras internas ni detalles técnicos irrelevantes.
"""

    return prompt.strip()

#
# res = """
# +++ Execution +++
# Failed: True
# Message: TypeError
# Output: TypeError raised arround line 148
# +++++++++++++++++
# """
#
# print(build_chatty_prompt("¿Me podrías dar la hora?", res))

