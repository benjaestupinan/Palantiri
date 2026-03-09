from brain.JOB_CATALOG import JOB_CATALOG as _catalog

_HIDDEN_FROM_INTENT_CLASSIFIER = {"search_memory", "get_recent_context"}

def _format_catalog():
  lines = []
  for job in _catalog.values():
    if job["job_id"] not in _HIDDEN_FROM_INTENT_CLASSIFIER:
      lines.append(f'  - {job["job_id"]} [{job.get("category", "")}]: {job["description"]}')
  return "\n".join(lines)

def _get_categories():
  return {job.get("category") for job in _catalog.values() if job.get("category")}

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
  según si puede responderse con razonamiento interno del modelo, o si se puede resolver
  con ayuda de alguno de los jobs del sistema.

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
  - "dame ideas para pautas de consultas nutricionales"
  - "cómo puedo mejorar mi rutina de ejercicios"
  - "qué es la hipertensión"
  - "escribime un correo formal"

  2) EXTEND_CONTEXT_WITH_SYSTEM_ACTION
  El usuario solicita algo que SOLO puede resolverse ejecutando uno de los jobs
  del catálogo. El match con el job debe ser directo y explícito.

  Ejemplos:
  - "qué hora es" → get_system_date_and_time
  - "lista los archivos de esta carpeta" → list_working_directory
  - "crea un archivo llamado notas.txt" → createfile
  - "explícame el archivo /home/user/main.py" → readfile (para poder explicarlo necesita leerlo primero)
  - "resume el contenido de notas.txt" → readfile (para resumir necesita leer el archivo)
  - "¿qué dijimos la última vez?" → get_recent_context
  - "¿te hablé alguna vez sobre X?" → search_memory

  IMPORTANTE: search_memory y get_recent_context SOLO aplican cuando el usuario
  pregunta EXPLÍCITAMENTE por conversaciones o memoria pasada, nunca de forma especulativa.

  3) END_SESSION
  El usuario se despide, indica que terminó la conversación o que no
  necesita nada más.

  Ejemplos:
  - "chau"
  - "eso es todo"
  - "hasta luego"
  - "gracias, ya no necesito nada más"

  REGLAS ABSOLUTAS (NO VIOLAR):

  - El match con un job debe ser DIRECTO y EXPLÍCITO. Si hay duda, es COGNITIVE_REQUEST.
  - Si el modelo puede responder con razonamiento interno, es COGNITIVE_REQUEST aunque
    hipotéticamente un job pudiera aportar algo.
  - Nunca inventes categorías adicionales.

  FORMATO OBLIGATORIO DE RESPUESTA:

  Responde EXCLUSIVAMENTE con un objeto JSON válido.
  NO escribas texto fuera del JSON.

  { "{" }
    "category": "COGNITIVE_REQUEST | EXTEND_CONTEXT_WITH_SYSTEM_ACTION | END_SESSION",
    "job_category": "categoría del job requerido | null",
    "confidence": number entre 0 y 1,
    "explanation": "explicación breve y objetiva del criterio aplicado"
  { "}" }

  REGLAS PARA job_category:
  - Solo se completa cuando category es EXTEND_CONTEXT_WITH_SYSTEM_ACTION.
  - Debe ser EXACTAMENTE una de las categorías disponibles: {_get_categories()}
  - En cualquier otro caso, job_category debe ser null.

  MENSAJE DEL USUARIO:
  {user_msg}
  """
  return msg
