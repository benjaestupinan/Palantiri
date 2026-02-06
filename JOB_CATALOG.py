JOB_CATALOG = {
    "echo": {
        "job_id": "echo",
        "description": "Devuelve exactamente el mensaje entregado, sin modificaciones.",
        "parameters": {
            "message": {"type": "string", "description": "Texto a devolver tal cual."}
        },
    },

    "add_numbers": {
        "job_id": "add_numbers",
        "description": "Suma dos números reales y devuelve el resultado.",
        "parameters": {
            "a": {"type": "number", "description": "Primer número."},
            "b": {"type": "number", "description": "Segundo número."},
        },
    },

    "get_system_time": {
        "job_id": "get_system_time",
        "description": "Obtiene la fecha y hora actual del sistema.",
        "parameters": {},
    },
    
    "delay_job": {
        "job_id": "delay_job",
        "description": "Ejecuta otro job después de un retraso especificado.",
        "parameters": {"delay_seconds": {"type": "number"}, "job": {"type": "job"}},
    },
}
