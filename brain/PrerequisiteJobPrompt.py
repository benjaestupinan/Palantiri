from .JOB_CATALOG import JOB_CATALOG


def get_prerequisite_job_prompt(goal_job, execution_error, user_msg, catalog=None):
    """
    Dado un job que falló por falta de parámetros, selecciona el job
    que debe ejecutarse primero para obtener los datos necesarios.
    """
    if catalog is None:
        catalog = JOB_CATALOG

    msg = f"""
    Eres un componente interno del sistema.
    No eres un chatbot ni un asistente conversacional.

    Un job falló porque le faltan datos. Tu única función es seleccionar
    qué job ejecutar primero para obtener esos datos.

    JOB QUE FALLÓ:
    job_id: {goal_job["job_id"]}
    parámetros actuales: {goal_job["parameters"]}
    error: {execution_error}

    MENSAJE ORIGINAL DEL USUARIO:
    {user_msg}

    JOB_IDS VÁLIDOS (lista exhaustiva y definitiva):
    {list(catalog.keys())}

    CATÁLOGO DISPONIBLE:
    {catalog}

    REGLAS ABSOLUTAS:
    - Responde EXCLUSIVAMENTE con un objeto JSON válido.
    - NO escribas texto fuera del JSON.
    - El job_id debe ser EXACTAMENTE uno de los job_ids válidos o null.
    - Solo incluye parámetros que puedas obtener directamente del mensaje del usuario.
    - Si no existe un job que pueda resolver el problema, retorna job_id = null.

    FORMATO OBLIGATORIO:
    {{
      "job_id": string | null,
      "parameters": object,
      "confidence": number,
      "explanation": string
    }}
    """
    return msg
