#!/bin/bash
set -e

SERVER="${PALANTIRI_SERVER:-}"
if [ -z "${SERVER}" ]; then
  echo "Error: define la variable de entorno PALANTIRI_SERVER con la IP del servidor."
  exit 1
fi
REPO_PATH="/path/to/Palantiri"  # ajustar al path del repo en el servidor
SERVICE_FILE="memory_service.service"
BINARY="memory_service"

echo "==> Compilando en el servidor..."
ssh "${SERVER}" "cd ${REPO_PATH}/memory_service && go build -o /tmp/${BINARY} ./cmd/"

echo "==> Instalando binario..."
ssh "${SERVER}" "sudo mv /tmp/${BINARY} /usr/local/bin/${BINARY} && sudo chmod +x /usr/local/bin/${BINARY}"

echo "==> Instalando servicio systemd..."
ssh "${SERVER}" "sudo cp ${REPO_PATH}/memory_service/${SERVICE_FILE} /etc/systemd/system/${SERVICE_FILE} && sudo systemctl daemon-reload && sudo systemctl enable ${SERVICE_FILE} && sudo systemctl restart ${SERVICE_FILE}"

echo ""
echo "==> Deploy completo."
ssh "${SERVER}" "sudo systemctl status memory_service --no-pager"
