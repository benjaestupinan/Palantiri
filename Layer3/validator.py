import os
import sys

# Añade la carpeta raíz del proyecto a sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from JOB_CATALOG import JOB_CATALOG


# Recursive function to validate format of given job
# @params:
# job: json object that represents a job in the catalog
#   {
#     job_id: string,
#     description: sring,
#     parameters: {
#       name: value
#         .
#         .
#         .
#       }
#    }
# @returns: boolean, str
# wheter a job has valid format or not, and a message
def validate_job(job):
    job_id = job["job_id"]
    given_params = job["parameters"]
    
    if job_id not in JOB_CATALOG:
        return False, f"Unknown job_id {job_id}"

    job_params = JOB_CATALOG[job_id]["parameters"]

    for param_name, param_spec in job_params.items():
        if param_name not in given_params:
            return False, f"Missing parameter {param_name}"

        value = given_params[param_name]

        match param_spec["type"]:
            case "job":
                valid, msg = validate_job(value)
                if not valid:
                    return False, f"Nested job error in {param_name}: {msg}"
            case "string":
                if not isinstance(value, str):
                    return False, f"Type error in {param_name}: expected string"
            case "number":
                if not isinstance(value, (int, float)):
                    return False, f"Type error in {param_name}: expected number"

    return True, "formato valido"


print(validate_job({
  "job_id": "delay_job",
  "parameters": {
    "delay_seconds": "900",
    "job": {
      "job_id": "get_system_time",
      "parameters": {}
    }
  },
  "confidence": 0.98,
  "explanation": "requisitos de tiempo especificados y job de retardo definido"
}))
