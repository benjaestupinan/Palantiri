#!/bin/bash
set -e

# Setup del servidor que hostea mcp_extensions_module y los procesos MCP
# externos definidos en mcp_servers.json:
#   - fetch    -> "uvx mcp-server-fetch"       (necesita uv/uvx)
#   - spotify  -> "node .../build/index.js"    (necesita Node.js + build local)
#
# Instala los runtimes (nvm/Node, uv) y deja compilado spotify-mcp-server en
# el path exacto que espera mcp_servers.json. No compila ni despliega
# mcp_extensions_module en sí — para eso usar mcp_extensions_module/deploy.sh
# una vez que este script terminó.
#
# Idempotente: correrlo de nuevo no reinstala ni reclona lo que ya está listo.

NODE_VERSION="24.14.0"
SPOTIFY_MCP_DIR="/home/dofoam/mcp_server_dependencies/spotify-mcp-server"
# URL del repo git de spotify-mcp-server. Solo se usa si SPOTIFY_MCP_DIR no
# existe todavía en este servidor.
SPOTIFY_MCP_REPO="${SPOTIFY_MCP_REPO:-}"

echo "==> Verificando nvm / Node v${NODE_VERSION}..."
export NVM_DIR="$HOME/.nvm"
if [ ! -s "${NVM_DIR}/nvm.sh" ]; then
  echo "==> Instalando nvm..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
fi
# shellcheck disable=SC1091
. "${NVM_DIR}/nvm.sh"

if ! nvm list | grep -q "v${NODE_VERSION}"; then
  echo "==> Instalando Node v${NODE_VERSION}..."
  nvm install "${NODE_VERSION}"
fi
nvm alias default "${NODE_VERSION}"
nvm use "${NODE_VERSION}"
echo "    node: $(node --version), npm: $(npm --version)"

echo "==> Verificando uv/uvx (para mcp-server-fetch)..."
if ! command -v uv >/dev/null 2>&1; then
  echo "==> Instalando uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "    uv: $(uv --version)"
echo "    (mcp-server-fetch se descarga solo la primera vez que uvx lo corre, no requiere pre-instalación)"

echo "==> Preparando spotify-mcp-server en ${SPOTIFY_MCP_DIR}..."
mkdir -p "$(dirname "${SPOTIFY_MCP_DIR}")"
if [ -d "${SPOTIFY_MCP_DIR}/.git" ]; then
  echo "    Repo ya existe, actualizando..."
  git -C "${SPOTIFY_MCP_DIR}" pull
elif [ -d "${SPOTIFY_MCP_DIR}" ]; then
  echo "    Directorio ya existe (sin .git), se usa tal cual."
else
  if [ -z "${SPOTIFY_MCP_REPO}" ]; then
    echo "ERROR: ${SPOTIFY_MCP_DIR} no existe y no se definió SPOTIFY_MCP_REPO."
    echo "Definí la variable de entorno con la URL del repo y volvé a correr:"
    echo "  SPOTIFY_MCP_REPO=<url-del-repo> ./setup_mcp_server.sh"
    exit 1
  fi
  git clone "${SPOTIFY_MCP_REPO}" "${SPOTIFY_MCP_DIR}"
fi

echo "==> Instalando dependencias y compilando spotify-mcp-server..."
( cd "${SPOTIFY_MCP_DIR}" && npm install && npm run build )

if [ ! -f "${SPOTIFY_MCP_DIR}/build/index.js" ]; then
  echo "ADVERTENCIA: no se encontró ${SPOTIFY_MCP_DIR}/build/index.js tras el build."
  echo "mcp_servers.json espera exactamente esa ruta — revisá el script de build del repo."
fi

echo ""
echo "==> Setup completo."
echo "  - Revisá mcp_servers.json en la raíz del repo si cambian rutas, comandos o credenciales."
echo "  - Corré mcp_extensions_module/deploy.sh para compilar y (re)iniciar el servicio, que"
echo "    es el que efectivamente lanza estos procesos MCP vía stdio."
