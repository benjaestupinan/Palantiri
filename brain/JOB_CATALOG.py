import json
import os

_catalog_path = os.path.join(os.path.dirname(__file__), '..', 'JOB_CATALOG.json')
with open(_catalog_path) as j:
    JOB_CATALOG = json.load(j)
