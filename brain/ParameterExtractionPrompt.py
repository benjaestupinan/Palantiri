from .JOB_CATALOG import JOB_CATALOG


def get_parameter_extraction_prompt(goal_job, prerequisite_result, catalog=None):
    """
    Dado el resultado de un job prerequisito, extrae los parámetros
    necesarios para completar el job objetivo.
    """
    if catalog is None:
        catalog = JOB_CATALOG

    job_schema = catalog.get(goal_job["job_id"], {}).get("parameters", {})

    msg = f"""
    Eres un componente interno del sistema.
    No eres un chatbot ni un asistente conversacional.

    Tu única función es extraer parámetros de un resultado para completar otro job.

    JOB QUE NECESITA PARÁMETROS:
    job_id: {goal_job["job_id"]}
    parámetros actuales: {goal_job["parameters"]}

    ESQUEMA DE PARÁMETROS DEL JOB (nombres y descripciones exactas):
    {job_schema}

    RESULTADO DEL JOB PREREQUISITO:
    {prerequisite_result}

    REGLAS ABSOLUTAS:
    - Responde EXCLUSIVAMENTE con un objeto JSON válido.
    - NO escribas texto fuera del JSON.
    - Usa EXACTAMENTE los nombres de parámetros definidos en el esquema.
    - Solo incluye parámetros que puedas obtener o construir a partir del resultado.
    - Usá las descripciones del esquema para entender el formato esperado de cada parámetro.
    - No inventes valores.

    FORMATO OBLIGATORIO:
    {{
      "parameters": {{}}
    }}
    """
    return msg
