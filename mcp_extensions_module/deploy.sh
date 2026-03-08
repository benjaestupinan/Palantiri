#!/bin/bash
set -e

REPO_PATH="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_FILE="mcp_extensions_module.service"
BINARY="mcp_extensions_module"

echo "==> Compilando..."
cd "${REPO_PATH}/mcp_extensions_module"
go build -o "/tmp/${BINARY}" ./cmd/

echo "==> Instalando binario..."
sudo mv "/tmp/${BINARY}" "/usr/local/bin/${BINARY}"
sudo chmod +x "/usr/local/bin/${BINARY}"

echo "==> Instalando servicio systemd..."
sudo cp "${REPO_PATH}/mcp_extensions_module/${SERVICE_FILE}" "/etc/systemd/system/${SERVICE_FILE}"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_FILE}"
sudo systemctl restart "${SERVICE_FILE}"

echo ""
echo "==> Deploy completo."
sudo systemctl status mcp_extensions_module --no-pager
