import re

def get_response_message_prompt(user_input, execution_result):
    """
    Construye un prompt para el modelo chatty a partir del input del usuario
    y el resultado exitoso del executor.
    Solo se llama cuando la ejecución fue exitosa (HTTP 200).
    """

    output_match = re.search(r"Output:\s*(.+)", execution_result)
    output = output_match.group(1).strip() if output_match else execution_result.strip()

    prompt = f"""
Eres un asistente que responde en lenguaje natural al usuario.

El usuario preguntó:
\"{user_input}\"

La ejecución fue exitosa. El resultado obtenido es:
\"{output}\"

Responde de forma clara y directa usando ese resultado.
No inventes información.
No menciones detalles técnicos internos.
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

