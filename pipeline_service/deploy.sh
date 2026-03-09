#!/bin/bash
set -e

REPO_PATH="/home/dofoam/Palantiri"
SERVICE_FILE="pipeline_service.service"

echo "==> Instalando dependencias..."
"${REPO_PATH}/venv/bin/pip" install -r "${REPO_PATH}/requirements.txt" -q

echo "==> Instalando servicio systemd..."
sudo cp "${REPO_PATH}/pipeline_service/${SERVICE_FILE}" "/etc/systemd/system/${SERVICE_FILE}"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_FILE}"
sudo systemctl restart "${SERVICE_FILE}"

echo ""
echo "==> Deploy completo."
sudo systemctl status pipeline_service --no-pager
