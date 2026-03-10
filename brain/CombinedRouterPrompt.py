from .JOB_CATALOG import JOB_CATALOG


def _format_job_ids(catalog):
    lines = []
    for i, job_id in enumerate(catalog.keys(), 1):
        lines.append(f"  {i}. {job_id}")
    return "\n".join(lines)


def get_combined_prompt(user_msg, catalog=None):
    if catalog is None:
        catalog = JOB_CATALOG

    msg = f"""
  Eres un componente interno del sistema.
  No eres un chatbot ni un asistente conversacional.

  ============================================================
  LISTA COMPLETA Y DEFINITIVA DE JOB_IDS PERMITIDOS:
  (solo estos existen, ningún otro es válido)

{_format_job_ids(catalog)}

  ============================================================

  Tu función es analizar el mensaje del usuario, clasificar su intención,
  y si requiere un job del sistema, seleccionarlo directamente.

  CATEGORÍAS OBLIGATORIAS (elige EXACTAMENTE una):

  1) COGNITIVE_REQUEST
  El modelo puede responder completamente con razonamiento interno.
  No requiere ninguna capacidad externa.
  → job_id debe ser null.

  Ejemplos: "cuánto es 2 + 3", "explícame qué es Docker", "escribime un correo formal"

  2) EXTEND_CONTEXT_WITH_SYSTEM_ACTION
  El usuario solicita algo que SOLO puede resolverse ejecutando un job del catálogo.
  El match con el job debe ser directo y explícito.
  → job_id debe ser uno de la lista de arriba.

  Ejemplos:
  - "qué hora es" → get_system_date_and_time
  - "lista los archivos de esta carpeta" → list_working_directory
  - "ponme X en spotify" → spotify_playMusic
  - "explícame el archivo /home/user/main.py" → readfile
  - "qué dijimos la última vez?" → get_recent_context
  - "qué te dije sobre X?" → search_memory

  IMPORTANTE: search_memory y get_recent_context SOLO aplican cuando el usuario
  pregunta EXPLÍCITAMENTE por conversaciones o memoria pasada.

  3) END_SESSION
  El usuario se despide o indica que terminó.
  → job_id debe ser null.

  Ejemplos: "chau", "eso es todo", "hasta luego", "gracias, ya no necesito nada más"

  REGLAS ABSOLUTAS (NO VIOLAR):
  - Responde EXCLUSIVAMENTE con un objeto JSON válido.
  - NO escribas texto fuera del JSON.
  - Si la categoría es COGNITIVE_REQUEST o END_SESSION: job_id = null, parameters = {{}}.
  - Si la categoría es EXTEND_CONTEXT_WITH_SYSTEM_ACTION: el job_id DEBE ser exactamente
    uno de los job_ids de la lista. NO inventes job_ids.
  - Si ningún job del catálogo resuelve la solicitud: usar COGNITIVE_REQUEST con job_id = null.
  - Si el modelo puede responder con razonamiento interno, es COGNITIVE_REQUEST aunque
    hipotéticamente un job pudiera aportar algo.

  REGLAS PARA SELECCIÓN DE JOB (cuando category = EXTEND_CONTEXT_WITH_SYSTEM_ACTION):
  - Solo parámetros definidos para ese job en el catálogo.
  - Si la acción es clara pero faltan parámetros que otro job podría proveer,
    seleccioná el job igualmente con los parámetros disponibles y dejá los faltantes vacíos.
    (el sistema resolverá los parámetros faltantes automáticamente)
  - EXCEPCIÓN TEMPORAL: podés convertir expresiones como "en 5 minutos" a segundos (300)
    solo si el valor y la unidad son explícitos y la conversión es directa.

  CATÁLOGO DE JOBS (descripciones y parámetros):
  {catalog}

  FORMATO OBLIGATORIO DE RESPUESTA:

  {"{"}
    "category": "COGNITIVE_REQUEST | EXTEND_CONTEXT_WITH_SYSTEM_ACTION | END_SESSION",
    "job_id": string | null,
    "parameters": object,
    "confidence": number,
    "explanation": string
  {"}"}

  EJEMPLOS:

  Usuario: "qué hora es"
  Respuesta: {{"category": "EXTEND_CONTEXT_WITH_SYSTEM_ACTION", "job_id": "get_system_date_and_time", "parameters": {{}}, "confidence": 0.95, "explanation": "pregunta directa sobre hora del sistema"}}

  Usuario: "ponme domination de pantera en spotify"
  Respuesta: {{"category": "EXTEND_CONTEXT_WITH_SYSTEM_ACTION", "job_id": "spotify_playMusic", "parameters": {{"query": "Domination Pantera"}}, "confidence": 0.95, "explanation": "acción explícita de reproducir canción en Spotify"}}

  Usuario: "explícame qué es un árbol binario"
  Respuesta: {{"category": "COGNITIVE_REQUEST", "job_id": null, "parameters": {{}}, "confidence": 0.95, "explanation": "pregunta de conocimiento general, responde el modelo"}}

  Usuario: "chau"
  Respuesta: {{"category": "END_SESSION", "job_id": null, "parameters": {{}}, "confidence": 0.99, "explanation": "despedida explícita"}}

  MENSAJE DEL USUARIO:
  {user_msg}

  ============================================================
  RECORDATORIO FINAL — JOB_IDS VÁLIDOS:
  (el job_id de tu respuesta DEBE ser exactamente uno de estos o null)

{_format_job_ids(catalog)}

  ============================================================
  """
    return msg
