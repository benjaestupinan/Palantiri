# Cómo correr Palantiri (LENS)

Esta guía consolida, en un solo lugar, cómo levantar **todos** los componentes del
sistema, tanto en un servidor remoto (producción) como en una sola máquina para
desarrollo local. Para el detalle de cada servicio individual, ver su propio
`README.md`.

---

## 1. Topología real del sistema

El repo contiene **dos formas distintas de correr el pipeline cognitivo**:

| Modo | Entry point | Cómo se usa | TTS |
|---|---|---|---|
| **Servicio remoto (producción)** | `pipeline_service/server.py` (Flask, `:8084`) | Un `client/` liviano local le manda texto por HTTP y reproduce el audio que recibe de vuelta | Server-side, `pipeline_service/tts.py` (Coqui TTS), devuelve WAV en base64 |
| **CLI local (todo en una máquina)** | `pipeline.py` (raíz) | Se corre directo, sin red, todo en el mismo proceso | Local, vía `the_way_of_the_voice.tts_service.speak()` |

Ambos modos comparten el mismo cerebro (`brain/`) y los mismos servicios Go
(`job_execution_service`, `memory_service`, `mcp_extensions_module`), pero **no
son intercambiables**: `pipeline_service/pipeline.py` agrega manejo de sesiones
multi-cliente, logging estructurado de cada "flow", encadenamiento de jobs
prerequisito (`ParameterExtractionPrompt` / `PrerequisiteJobPrompt`) y feedback;
`pipeline.py` de la raíz es la versión simple de un solo usuario por proceso.

Topología recomendada (la que describe "agente en servidor remoto + MCPs"):

```
┌─────────────────────┐        HTTP :8084        ┌───────────────────────────────────────┐
│  client/ (local,     │ ────────────────────────▶│  Servidor remoto                       │
│  tu máquina)         │◀──────────────────────── │                                        │
│  input → texto       │   {text, audio_b64}       │  ┌──────────────────────────────────┐ │
│  output → play_audio │                           │  │ pipeline_service  :8084 (Flask)   │ │
└─────────────────────┘                           │  │  usa brain/ + TTS (Coqui)          │ │
                                                    │  └───────────────┬────────────────────┘ │
                                                    │                  │ HTTP interno           │
                                                    │   ┌──────────────┼──────────────────┐    │
                                                    │   ▼              ▼                  ▼    │
                                                    │ job_execution   memory_service   mcp_extensions │
                                                    │ _service :8081  :8082 (+Postgres) _module :8083 │
                                                    │                                        │
                                                    │  mcp_extensions_module lanza procesos   │
                                                    │  MCP locales (stdio): fetch (uvx),      │
                                                    │  spotify (node), etc. — definidos en    │
                                                    │  mcp_servers.json                       │
                                                    │                                        │
                                                    │  Ollama :11434 (modelos "lens" y        │
                                                    │  qwen2.5:14b) — puede vivir en este     │
                                                    │  mismo servidor o en otro accesible      │
                                                    │  por red (OLLAMA_HOST)                  │
                                                    └───────────────────────────────────────┘
```

> Nota sobre "MCPs desde otro servidor remoto": `mcp_extensions_module` no llama
> a servers MCP remotos por HTTP — lanza los procesos MCP (node/npx/uvx) como
> **subprocesos locales vía stdio**, igual que Claude Desktop. Si tus MCP
> servers deben vivir en otra máquina, tenés que correr una instancia de
> `mcp_extensions_module` en esa máquina y apuntar `MCP_EXTENSIONS_HOST` del
> resto del sistema a esa IP.

---

## 2. Prerrequisitos

| Herramienta | Versión | Para qué |
|---|---|---|
| Go | 1.25.3 | `job_execution_service`, `memory_service`, `mcp_extensions_module` |
| Python | 3.10+ | `brain/`, `pipeline.py`, `pipeline_service/`, `client/`, `the_way_of_the_voice/` |
| [Ollama](https://ollama.com) | — | Corre los LLM. Necesita **dos modelos**: ver abajo |
| PostgreSQL | 13+ | Backend de `memory_service` (lo instala `setup_server.sh`) |
| Node.js / npx | — | Para MCP servers tipo `npx -y mcp-server-...` |
| [uv](https://docs.astral.sh/uv/) (`uvx`) | — | Para MCP servers tipo `uvx mcp-server-fetch` |

### Modelos de Ollama

```sh
ollama pull qwen2.5:14b
```

`brain/PromptLLM.ask_chatty()` usa un modelo llamado **`lens`**, un modelo
custom ya creado y configurado en el servidor remoto que corre Ollama — no
requiere ninguna acción adicional de tu parte si apuntás `OLLAMA_HOST` a ese
servidor.

---

## 3. Variables de entorno

### `.env` en la raíz del proyecto (leído por Python y por los binarios Go vía `../.env`)

```env
OLLAMA_HOST=localhost
OLLAMA_PORT=11434

JOB_EXECUTOR_HOST=localhost
JOB_EXECUTOR_PORT=8081

MEMORY_HOST=<ip_del_servidor>
MEMORY_PORT=8082

MCP_EXTENSIONS_HOST=<ip_del_servidor>
MCP_EXTENSIONS_PORT=8083
```

### `PIPELINE_HOST` / `PIPELINE_PORT` (para `client/`)

El cliente (`client/server.py`) lee estas del mismo `.env`:

```env
PIPELINE_HOST=<ip_del_servidor>
PIPELINE_PORT=8084
```

### `/etc/memory_service.env` (en el servidor, generado por `setup_server.sh`)

```env
PGHOST=localhost
PGPORT=5432
PGUSER=palantiri_user
PGPASSWORD=<generado automáticamente>
PGDATABASE=palantiri_db
```

### `/etc/mcp_extensions_module.env` (en el servidor)

```env
MCP_EXTENSIONS_PORT=8083
MCP_SERVERS_CONFIG=/ruta/absoluta/al/repo/mcp_servers.json
```

> `mcp_servers.json` trae rutas bajo `/home/dofoam/...`, que corresponden al
> usuario del servidor remoto donde vive `mcp_extensions_module` — no hace
> falta tocarlas si estás desplegando ahí.

---

## 4. Levantar todo en un servidor remoto (producción)

Asumiendo que ya clonaste el repo en el servidor (`git clone <url> ~/Palantiri`).

### 4.1 Ollama
```sh
ollama pull qwen2.5:14b
# crear/ajustar el modelo "lens" — ver sección de prerrequisitos
ollama serve   # si no corre ya como servicio
```

### 4.2 Memory Service (Go + Postgres) — una sola vez
```sh
cd ~/Palantiri/memory_service
chmod +x setup_server.sh
sudo ./setup_server.sh     # instala Postgres, crea DB/usuario, aplica schema.sql
                            # anota la password que imprime al final
```
Deploy / arranque como servicio systemd:
```sh
# ajustar REPO_PATH dentro de memory_service/deploy.sh primero
cd ~/Palantiri/memory_service
chmod +x deploy.sh
./deploy.sh
# sudo systemctl status memory_service
```

### 4.3 Job Execution Service (Go)
No trae `deploy.sh` propio en este repo; para correrlo como proceso simple:
```sh
cd ~/Palantiri/job_execution_service
go run server/main.go
# o compilado: go build -o job_execution_service ./server && ./job_execution_service
# escucha en :8081
```
(Si querés que sobreviva reinicios, armale una unit systemd análoga a las de
`memory_service` / `mcp_extensions_module`.)

### 4.4 MCP Extensions Module (Go)
```sh
# 1. Crear el env file en el servidor
sudo tee /etc/mcp_extensions_module.env <<'EOF'
MCP_EXTENSIONS_PORT=8083
MCP_SERVERS_CONFIG=/home/dofoam/Palantiri/mcp_servers.json
EOF

# 2. Deploy
cd ~/Palantiri/mcp_extensions_module
chmod +x deploy.sh
./deploy.sh
# sudo systemctl status mcp_extensions_module
```

### 4.5 Pipeline Service (Python + Flask, expone :8084)
```sh
cd ~/Palantiri
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

mkdir -p logs   # pipeline_service escribe logs/pipeline.log
```
```sh
python -m pipeline_service.server
# o como servicio systemd:
cd pipeline_service
chmod +x deploy.sh   # ajustar REPO_PATH/venv path dentro si difiere
./deploy.sh
# sudo systemctl status pipeline_service
```

### 4.6 Verificar que todo responde
```sh
curl http://localhost:8081/health   # job_execution_service
curl http://localhost:8082/health   # memory_service
curl http://localhost:8083/health   # mcp_extensions_module
curl http://localhost:8083/catalog  # tools MCP detectados
curl -X POST http://localhost:8084/message \
  -H 'Content-Type: application/json' \
  -d '{"session_id": null, "message": "hola"}'
```

---

## 5. Correr el cliente (tu máquina local)

```sh
cd Palantiri
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```
Configurar en `.env` local:
```env
PIPELINE_HOST=<ip_del_servidor>
PIPELINE_PORT=8084
```
Correr:
```sh
python -m client.client
```
Esto entra en un loop: pide texto por consola (`msg: `), lo manda al
`pipeline_service` remoto, reproduce el audio de la respuesta con
`sounddevice`, y pregunta feedback (`yes`/`no`) que se loguea en el servidor.

---

## 6. Modo alternativo: todo local, sin cliente/servidor (desarrollo rápido)

Para probar el pipeline cognitivo sin levantar Flask ni el módulo de cliente,
usando el flujo simple original:

```sh
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

`.env` con todo apuntando a `localhost` (o a las IPs reales de
`memory_service` / `mcp_extensions_module` si esos corren en el servidor y
solo querés correr el cerebro localmente):
```env
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
JOB_EXECUTOR_HOST=localhost
JOB_EXECUTOR_PORT=8081
MEMORY_HOST=<ip_del_servidor>
MEMORY_PORT=8082
MCP_EXTENSIONS_HOST=<ip_del_servidor>
MCP_EXTENSIONS_PORT=8083
```

Levantar `job_execution_service` localmente (obligatorio, corre siempre en el
mismo proceso Python vía HTTP):
```sh
cd job_execution_service && go run server/main.go
```

Correr el pipeline:
```sh
python pipeline.py
```
Este modo sí usa `ask_qwen`/`ask_chatty` (sin el bug de `ask_model`) y hace
TTS local con Coqui vía `the_way_of_the_voice`. Corre en loop hasta que el
intent detectado sea `END_SESSION`.

---

## 7. Tests

```sh
cd job_execution_service && go test ./...
```
No hay suite de tests Python en el repo. CI (`.github/workflows/go.yml`) solo
compila y testea `job_execution_service` con Go 1.25.3 en cada push/PR a `main`.

---

## 8. Actualizar el catálogo de jobs

Después de agregar o modificar un job Go, regenerar `JOB_CATALOG.json` (en la
raíz) desde el código:
```sh
cd job_execution_service/cmd/generate_catalog
go run main.go
```
Las descripciones escritas a mano en el JSON se preservan; solo se
actualiza la estructura de parámetros inferida del código Go.

---

## 9. Manejo de los servicios systemd (en el servidor)

```sh
sudo systemctl status  <memory_service|mcp_extensions_module|pipeline_service>
sudo systemctl restart <memory_service|mcp_extensions_module|pipeline_service>
sudo journalctl -u <servicio> -f
```

---

## 10. Referencias

- [`README.md`](./README.md) — arquitectura general y diagrama de flujo del intent router
- [`brain/README.md`](./brain/README.md) — detalle del núcleo cognitivo
- [`job_execution_service/README.md`](./job_execution_service/README.md) — API y cómo registrar jobs nuevos
- [`memory_service/README.md`](./memory_service/README.md) — setup de Postgres y deploy
- [`mcp_extensions_module/README.md`](./mcp_extensions_module/README.md) — protocolo MCP y configuración de servers externos
- [`the_way_of_the_voice/README.md`](./the_way_of_the_voice/README.md) — TTS local
- [`METRICS.md`](./METRICS.md) — métricas sugeridas por etapa del pipeline
