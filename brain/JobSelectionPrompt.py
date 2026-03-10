from .JOB_CATALOG import JOB_CATALOG


def _format_job_ids(catalog):
  lines = []
  for i, job_id in enumerate(catalog.keys(), 1):
    lines.append(f"  {i}. {job_id}")
  return "\n".join(lines)


def get_job_selection_prompt(user_msg, catalog=None):
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

  Tu única función es analizar el mensaje del usuario y seleccionar
  UN job de la lista anterior.

  REGLAS ABSOLUTAS (NO VIOLAR):
  - Responde EXCLUSIVAMENTE con un objeto JSON válido.
  - NO escribas texto fuera del JSON.
  - El campo job_id DEBE ser uno de los job_ids de la lista de arriba, EXACTAMENTE como aparece.
  - NO inventes job_ids. NO uses job_ids "similares" o "aproximados".
  - Si el job_id que necesitarías no está en la lista, retorna job_id = null.

  CRITERIO GENERAL DE SELECCIÓN:
  Un job puede ser seleccionado SOLO si:
  - el mensaje expresa explícitamente una acción
  - el resultado solicitado puede obtenerse con uno o más jobs del catálogo
  - los parámetros requeridos pueden obtenerse del mensaje O pueden ser resueltos
    por otro job del catálogo (el sistema resolverá los parámetros faltantes automáticamente)

  IMPORTANTE: si la acción es clara pero faltan parámetros que otro job podría proveer
  (por ejemplo, un ID o URI que requiere una búsqueda previa), seleccioná el job igualmente
  con los parámetros disponibles y dejá los faltantes vacíos.

  TIPOS DE JOBS:
  - Jobs primitivos: ejecutan una acción directa.
  - Jobs compuestos: reciben como parámetro otro job válido del catálogo.

  REGLAS PARA JOBS COMPUESTOS:
  - Un job compuesto SOLO puede seleccionarse si:
    - el mensaje expresa explícitamente una relación temporal, condicional o secuencial
      (ej: "en 10 minutos", "después de", "si ocurre X")
    - el job interno es seleccionable de forma independiente
    - el job interno tiene todos sus parámetros completos
  - NO construyas jobs compuestos si la relación no está explícita.
  - NO anides jobs más allá de lo definido en el catálogo.

  EXCEPCIÓN DE INFERENCIA CONTROLADA (PERMITIDA):
  El modelo PUEDE convertir expresiones temporales a segundos SOLO si:
  - el mensaje contiene explícitamente un valor numérico y una unidad temporal
  - las unidades permitidas son ÚNICAMENTE: segundos, minutos u horas
  - la conversión es directa y no ambigua
  - NO se permiten expresiones vagas (ej: "un rato", "más tarde", "cuando puedas")

  Fuera de esta excepción, NO realices inferencias ni transformaciones implícitas.

  FORMAS VÁLIDAS DE SOLICITUD:
  - Imperativo directo (ej: "apaga la luz", "pon una alarma a las 7")
  - Petición cortés (ej: "podrías decirme la hora?", "podrías apagar la luz?")
  - Pregunta directa con objetivo accionable (ej: "qué hora es", "cuánta memoria RAM hay disponible")

  NO SELECCIONES JOBS ANTE:
  - mensajes conversacionales
  - preguntas hipotéticas ("qué pasaría si...")
  - solicitudes ambiguas o exploratorias

  FORMATO OBLIGATORIO DE RESPUESTA:

  {"{"}
    "job_id": string | null,
    "parameters": object,
    "confidence": number,
    "explanation": string
  {"}"}

  DEFINICIONES ESTRICTAS:
  - job_id:
    - Debe ser EXACTAMENTE uno de los job_ids de la lista o null.
  - parameters:
    - Solo parámetros definidos para ese job en el catálogo.
    - Si el job no requiere parámetros, usar {"{"}{"}"}.
  - confidence:
    - 0.0–0.3 → mensaje sin acción
    - 0.4–0.6 → acción parcialmente definida
    - 0.7–1.0 → acción clara
    - Este valor es solo informativo.
  - explanation:
    - Máximo una frase corta.
    - Describir únicamente el criterio aplicado.

  CATÁLOGO DE JOBS DISPONIBLES (descripciones y parámetros):
  {catalog}

  EJEMPLOS DE SELECCIÓN CORRECTA:

  Usuario: "qué hora es"
  Respuesta: {{"job_id": "get_system_date_and_time", "parameters": {{}}, "confidence": 0.95, "explanation": "pregunta directa sobre hora del sistema"}}

  Usuario: "lee el archivo /home/user/notas.txt"
  Respuesta: {{"job_id": "readfile", "parameters": {{"path": "/home/user/notas.txt"}}, "confidence": 0.98, "explanation": "acción explícita de lectura con path completo"}}

  Usuario: "explícame el archivo /home/user/main.py"
  Respuesta: {{"job_id": "readfile", "parameters": {{"path": "/home/user/main.py"}}, "confidence": 0.95, "explanation": "para explicar el archivo es necesario leerlo primero"}}

  Usuario: "resume el contenido de /home/user/notas.txt"
  Respuesta: {{"job_id": "readfile", "parameters": {{"path": "/home/user/notas.txt"}}, "confidence": 0.95, "explanation": "para resumir el archivo es necesario leerlo primero"}}

  Usuario: "crea un archivo llamado ideas.txt en el escritorio"
  Respuesta: {{"job_id": "createfile", "parameters": {{"path": "/home/user/Desktop/ideas.txt"}}, "confidence": 0.85, "explanation": "acción explícita de creación con nombre y ubicación inferida"}}

  Usuario: "en test.txt reemplaza 'testo' por 'texto'"
  Respuesta: {{"job_id": "editfile", "parameters": {{"path": "test.txt", "edits": [{{"old_string": "testo", "new_string": "texto"}}]}}, "confidence": 0.97, "explanation": "acción explícita de edición con old_string y new_string claros"}}

  Usuario: "lista los archivos de la carpeta proyectos"
  Respuesta: {{"job_id": "list_working_directory", "parameters": {{"path": "proyectos"}}, "confidence": 0.95, "explanation": "acción explícita de listado con path indicado"}}

  Usuario: "qué te dije sobre Docker?"
  Respuesta: {{"job_id": "search_memory", "parameters": {{"query": "Docker"}}, "confidence": 0.93, "explanation": "pregunta explícita sobre conversaciones pasadas con tema claro"}}

  Usuario: "recuerdas lo que hablamos la última vez?"
  Respuesta: {{"job_id": "get_recent_context", "parameters": {{}}, "confidence": 0.95, "explanation": "pregunta explícita sobre conversación anterior sin tema específico"}}

  Usuario: "podrías explicarme cómo funciona docker?"
  Respuesta: {{"job_id": null, "parameters": {{}}, "confidence": 0.1, "explanation": "pregunta de conocimiento general, no requiere job"}}

  MENSAJE DEL USUARIO:
  {user_msg}

  ============================================================
  RECORDATORIO FINAL — JOB_IDS VÁLIDOS:
  (el job_id de tu respuesta DEBE ser exactamente uno de estos o null)

{_format_job_ids(catalog)}

  ============================================================
  """
  return msg
