#!/bin/bash
set -e

# Setup del servidor que corre Ollama para LENS.
#
# Instala/actualiza Ollama, lo deja escuchando en la red (para que otros
# servidores puedan usarlo vía OLLAMA_HOST), descarga qwen2.5:14b
# (clasificación de intención / selección de jobs), y registra en Ollama el
# modelo custom "lens" (respuestas conversacionales) a partir de los archivos
# que ya existen en este servidor bajo LENS_MODEL_DIR.
#
# Idempotente: correrlo de nuevo no reinstala ni recrea lo que ya está listo.

OLLAMA_MODEL="qwen2.5:14b"
LENS_MODEL_NAME="lens"
LENS_MODEL_DIR="/home/dofoam/models/LENS"
OLLAMA_HOST_BIND="0.0.0.0"

echo "==> Verificando Ollama..."
if ! command -v ollama >/dev/null 2>&1; then
  echo "==> Instalando Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "    Ya instalado: $(ollama --version)"
fi

echo "==> Configurando Ollama para escuchar en ${OLLAMA_HOST_BIND} (acceso desde otros servidores)..."
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<EOF
[Service]
Environment="OLLAMA_HOST=${OLLAMA_HOST_BIND}"
EOF

sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl restart ollama

echo "==> Esperando a que Ollama levante..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:11434/api/tags > /dev/null; then
    break
  fi
  sleep 1
done

echo "==> Descargando ${OLLAMA_MODEL}..."
ollama pull "${OLLAMA_MODEL}"

echo "==> Verificando modelo custom '${LENS_MODEL_NAME}'..."
if ollama list | awk 'NR>1{print $1}' | grep -qE "^${LENS_MODEL_NAME}(:|$)"; then
  echo "    '${LENS_MODEL_NAME}' ya está registrado en Ollama."
elif [ -f "${LENS_MODEL_DIR}/Modelfile" ]; then
  echo "    Registrando '${LENS_MODEL_NAME}' desde ${LENS_MODEL_DIR}/Modelfile..."
  ollama create "${LENS_MODEL_NAME}" -f "${LENS_MODEL_DIR}/Modelfile"
else
  echo "    ADVERTENCIA: '${LENS_MODEL_NAME}' no está registrado en Ollama y no se"
  echo "    encontró ${LENS_MODEL_DIR}/Modelfile para crearlo automáticamente."
  echo "    Los archivos del modelo existen en ${LENS_MODEL_DIR} — registralo a mano:"
  echo "      ollama create ${LENS_MODEL_NAME} -f ${LENS_MODEL_DIR}/Modelfile"
fi

echo ""
echo "==> Setup completo. Modelos disponibles:"
ollama list
