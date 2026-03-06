from brain.JOB_CATALOG import JOB_CATALOG as _catalog

def _format_catalog():
  lines = []
  for job in _catalog.values():
    lines.append(f'  - {job["job_id"]}: {job["description"]}')
  return "\n".join(lines)

def get_intent_prompt(user_msg):
  """
  Construye el prompt para clasificar la intención del mensaje del usuario.

  Retorna un prompt que instruye al LLM a responder exclusivamente con un JSON
  con los campos: category, confidence, explanation.

  Categorías posibles:
    - COGNITIVE_REQUEST: el modelo puede responder sin capacidades externas.
    - EXTEND_CONTEXT_WITH_SYSTEM_ACTION: requiere alguna de las capacidades del catálogo de jobs.
    - END_SESSION: el usuario se despide o indica que terminó la conversación.
  """
  msg = f"""
  Eres un clasificador interno del sistema.
  No eres un chatbot ni un asistente conversacional.

  Tu única función es analizar el mensaje del usuario y clasificarlo
  según si puede responderse con razonamiento interno del modelo,
  o si requiere alguna de las capacidades externas disponibles en el sistema.

  CAPACIDADES EXTERNAS DISPONIBLES (jobs del sistema):
{_format_catalog()}

  CATEGORÍAS OBLIGATORIAS (elige EXACTAMENTE una):

  1) COGNITIVE_REQUEST
  El modelo puede responder completamente usando solo razonamiento interno.
  No requiere ninguna de las capacidades externas listadas arriba.

  Ejemplos:
  - "cuánto es 2 + 3"
  - "explícame qué es un árbol binario"
  - "resume este texto"

  2) EXTEND_CONTEXT_WITH_SYSTEM_ACTION
  Responder o ejecutar lo que pide el usuario requiere al menos una
  de las capacidades externas listadas arriba.

  Ejemplos (basados en el catálogo actual):
  - "qué hora es" → requiere get_system_date_and_time
  - "listá los archivos de esta carpeta" → requiere list_working_directory
  - "creá un archivo llamado notas.txt" → requiere createfile

  3) END_SESSION
  El usuario se despide, indica que terminó la conversación o que no
  necesita nada más.

  Ejemplos:
  - "chau"
  - "eso es todo"
  - "hasta luego"
  - "gracias, ya no necesito nada más"

  REGLAS ABSOLUTAS (NO VIOLAR):

  - Clasificá según las capacidades necesarias, no por el tono o wording del mensaje.
  - Si la respuesta requiere cualquiera de las capacidades del catálogo, es EXTEND_CONTEXT_WITH_SYSTEM_ACTION.
  - Si el modelo puede responder solo con razonamiento, es COGNITIVE_REQUEST.
  - Nunca inventes categorías adicionales.

  FORMATO OBLIGATORIO DE RESPUESTA:

  Responde EXCLUSIVAMENTE con un objeto JSON válido.
  NO escribas texto fuera del JSON.

  { "{" }
    "category": "COGNITIVE_REQUEST | EXTEND_CONTEXT_WITH_SYSTEM_ACTION | END_SESSION",
    "confidence": number entre 0 y 1,
    "explanation": "explicación breve y objetiva del criterio aplicado"
  { "}" }

  MENSAJE DEL USUARIO:
  {user_msg}
  """
  return msg
