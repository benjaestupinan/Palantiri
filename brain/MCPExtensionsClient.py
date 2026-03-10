import os

import requests
from dotenv import load_dotenv

load_dotenv()

MCP_EXTENSIONS_HOST = os.getenv("MCP_EXTENSIONS_HOST")
MCP_EXTENSIONS_PORT = os.getenv("MCP_EXTENSIONS_PORT", "8083")

BASE_URL = f"http://{MCP_EXTENSIONS_HOST}:{MCP_EXTENSIONS_PORT}"

_mcp_job_ids: set[str] = set()


def get_catalog() -> dict:
    """
    Fetches the MCP tools catalog from mcp_extensions_module.
    Returns dict in JOB_CATALOG format, or empty dict on failure.
    """
    global _mcp_job_ids
    try:
        response = requests.get(f"{BASE_URL}/catalog", timeout=5)
        response.raise_for_status()
        catalog = response.json()
        _mcp_job_ids = set(catalog.keys())
        return catalog
    except Exception as e:
        print(f"[MCPExtensionsClient] get_catalog failed: {e}")
        return {}


def is_mcp_job(job_id: str) -> bool:
    return job_id in _mcp_job_ids


def execute_mcp_tool(job: dict) -> dict:
    """
    Executes an MCP tool via mcp_extensions_module.
    Returns same format as JobExecutorClient.execute_job().
    """
    try:
        response = requests.post(
            f"{BASE_URL}/execute",
            json={"job_id": job["job_id"], "parameters": job.get("parameters", {})},
            timeout=30,
        )
        response_text = response.text.strip()
        is_error = response.status_code != 200 or response_text.startswith("Error:")
        return {
            "success": not is_error,
            "status_code": response.status_code,
            "response_text": response_text,
        }
    except Exception as e:
        print(f"[MCPExtensionsClient] execute_mcp_tool failed: {e}")
        return {
            "success": False,
            "status_code": 0,
            "response_text": str(e),
        }
