import json
import os

_catalog_path = os.path.join(os.path.dirname(__file__), '..', 'JOB_CATALOG.json')
with open(_catalog_path) as j:
    JOB_CATALOG = json.load(j)


def merge_mcp_catalog(mcp_catalog: dict):
    """Merges MCP tools into the in-memory JOB_CATALOG."""
    JOB_CATALOG.update(mcp_catalog)
