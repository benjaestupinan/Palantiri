from JOB_CATALOG import JOB_CATALOG


def validate_value(value, spec, path):
    match spec["type"]:
        case "job":
            return validate_job(value)
        case "string":
            if not isinstance(value, str):
                return False, f"Type error in {path}: expected string"
        case "number":
            if not isinstance(value, (int, float)):
                return False, f"Type error in {path}: expected number"
        case "boolean":
            if not isinstance(value, bool):
                return False, f"Type error in {path}: expected boolean"
        case "array":
            if not isinstance(value, list):
                return False, f"Type error in {path}: expected array"
            items_spec = spec.get("items")
            if items_spec:
                for i, item in enumerate(value):
                    valid, msg = validate_value(item, items_spec, f"{path}[{i}]")
                    if not valid:
                        return False, msg
        case "object":
            if not isinstance(value, dict):
                return False, f"Type error in {path}: expected object"
            for field_name, field_spec in spec.get("properties", {}).items():
                if field_name not in value:
                    return False, f"Missing field '{field_name}' in {path}"
                valid, msg = validate_value(value[field_name], field_spec, f"{path}.{field_name}")
                if not valid:
                    return False, msg
    return True, "formato valido"


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

        valid, msg = validate_value(given_params[param_name], param_spec, param_name)
        if not valid:
            return False, msg

    return True, "formato valido"

if __name__ == '__main__':
    print(validate_job({
      "job_id": "delay_job",
      "parameters": {
        "delay_seconds": 900,
        "job": {
          "job_id": "get_system_time",
          "parameters": {}
        }
      },
      "confidence": 0.98,
      "explanation": "requisitos de tiempo especificados y job de retardo definido"
    }))
