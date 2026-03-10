def get_parameter_extraction_prompt(goal_job, prerequisite_result):
    """
    Dado el resultado de un job prerequisito, extrae los parámetros
    necesarios para completar el job objetivo.
    """
    msg = f"""
    Eres un componente interno del sistema.
    No eres un chatbot ni un asistente conversacional.

    Tu única función es extraer parámetros de un resultado para completar otro job.

    JOB QUE NECESITA PARÁMETROS:
    job_id: {goal_job["job_id"]}
    parámetros actuales: {goal_job["parameters"]}

    RESULTADO DEL JOB PREREQUISITO:
    {prerequisite_result}

    REGLAS ABSOLUTAS:
    - Responde EXCLUSIVAMENTE con un objeto JSON válido.
    - NO escribas texto fuera del JSON.
    - Solo incluye parámetros que puedas extraer directamente del resultado.
    - No inventes valores.

    FORMATO OBLIGATORIO:
    {{
      "parameters": {{}}
    }}
    """
    return msg
