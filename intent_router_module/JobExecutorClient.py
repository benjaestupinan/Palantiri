import os
import requests
from dotenv import load_dotenv

load_dotenv()

JOB_EXECUTOR_HOST = os.getenv("JOB_EXECUTOR_HOST")
JOB_EXECUTOR_PORT = os.getenv("JOB_EXECUTOR_PORT", "8081")

BASE_URL = f"http://{JOB_EXECUTOR_HOST}:{JOB_EXECUTOR_PORT}"


def execute_job(job: dict):
    """
    Sends a validated job to the Go job execution service.

    Expects job format:
    {
        "job_id": str,
        "parameters": dict
    }

    Returns:
        dict with:
        {
            "success": bool,
            "status_code": int,
            "response_text": str
        }
    """

    job_id = job["job_id"]

    # print(f"job to be sent: {job}")
    
    # print(f"url: {BASE_URL}/job/{job_id}")
    response = requests.post(
        url=f"{BASE_URL}/job/{job_id}",
        json=job,
    )

    return {
        "success": response.status_code == 200,
        "status_code": response.status_code,
        "response_text": response.text.strip()
    }

if __name__ == '__main__':
    job = {
        "job_id": "get_system_date_and_time",
        "parameters": {}
    }

    print(execute_job(job))
