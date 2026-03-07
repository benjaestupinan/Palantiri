#!/bin/bash
set -e

SERVER="${PALANTIRI_SERVER:-}"
if [ -z "${SERVER}" ]; then
  echo "Error: define la variable de entorno PALANTIRI_SERVER con la IP del servidor."
  exit 1
fi
REPO_PATH="/home/dofoam/Palantiri"
SERVICE_FILE="mcp_extensions_module.service"
BINARY="mcp_extensions_module"

echo "==> Compilando en el servidor..."
ssh "${SERVER}" "cd ${REPO_PATH}/mcp_extensions_module && /usr/local/go/bin/go build -o /tmp/${BINARY} ./cmd/"

echo "==> Instalando binario..."
ssh "${SERVER}" "sudo mv /tmp/${BINARY} /usr/local/bin/${BINARY} && sudo chmod +x /usr/local/bin/${BINARY}"

echo "==> Instalando servicio systemd..."
ssh "${SERVER}" "sudo cp ${REPO_PATH}/mcp_extensions_module/${SERVICE_FILE} /etc/systemd/system/${SERVICE_FILE} && sudo systemctl daemon-reload && sudo systemctl enable ${SERVICE_FILE} && sudo systemctl restart ${SERVICE_FILE}"

echo ""
echo "==> Deploy completo."
ssh "${SERVER}" "sudo systemctl status mcp_extensions_module --no-pager"
