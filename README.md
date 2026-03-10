# Palantiri — LENS

LENS es un asistente virtual local tipo Jarvis. Recibe lenguaje natural, clasifica la intención, ejecuta acciones del sistema si corresponde, y responde en voz.

Todo el razonamiento corre localmente vía [Ollama](https://ollama.com). No hay llamadas a APIs externas de IA.

---

## Arquitectura general

```
┌─────────────────────────────────────────────────────────────┐
│                         Usuario                             │
└───────────────────────────┬─────────────────────────────────┘
                            │ lenguaje natural
                            ▼
                   [ pipeline.py ]
                   │ al iniciar:
                   │  · MemoryClient.create_session()
                   │  · MCPExtensionsClient.get_catalog() → merge en JOB_CATALOG
                            │
                            ▼
            ┌───────────────────────────┐
            │   1. Intent Router (LLM)  │
            │   qwen2.5:14b via Ollama  │
            └──────────────┬────────────┘
          ┌─────────────────┼──────────────────┐
          │                 │                  │
          ▼                 ▼                  ▼
    END_SESSION    COGNITIVE_REQUEST    EXTEND_CONTEXT_WITH
          │                │            SYSTEM_ACTION
          │                │                  │
          ▼                ▼                  ▼
    Nueva sesión  MemoryClient        ┌──────────────────────┐
    + despedida   .get_history()      │ 2. Job Selector (LLM) │
                       │              │    qwen2.5:14b         │
                       ▼              └──────────┬────────────┘
                  Chatty LLM                     │
                  (respuesta)          job_id == null?
                       │                   │       │
                       ▼                   ▼       ▼
                  save_message()      fallback  ┌──────────────────┐
                  en memoria         chatty     │  3. Validator     │
                                    (no         │  schema + tipos   │
                                    capability) └──────┬───────────┘
                                                       │
                                              inválido / hallucinated?
                                                   │       │
                                                   ▼       ▼
                                                error   ┌──────────────────────────┐
                                                msg     │  4. Router de ejecución   │
                                                        │  · MCP job → :8083        │
                                                        │  · Go job  → :8081        │
                                                        └──────────┬───────────────┘
                                                                   │
                                                              fallido?
                                                             │       │
                                                             ▼       ▼
                                                         error   ┌──────────────────────┐
                                                         crudo   │  5. Result Formatter  │
                                                                 │  Chatty LLM           │
                                                                 └──────────┬────────────┘
                                                                            │
                                                                    save_message()
                                                                    en memoria
                                                                            │
                                                                            ▼
                                                              ┌─────────────────────────┐
                                                              │  6. TTS (opcional)       │
                                                              │  the_way_of_the_voice    │
                                                              └─────────────────────────┘
```

---

## Componentes

| Componente | Tecnología | Descripción |
|---|---|---|
| `pipeline.py` | Python | Orquestador principal del flujo |
| `brain/` | Python | Clasificación de intención, selección y validación de jobs, prompts LLM |
| `job_execution_service/` | Go | Servidor HTTP que ejecuta jobs de forma determinista (:8081) |
| `memory_service/` | Go + PostgreSQL | Memoria persistente: sesiones, historial de mensajes, búsqueda (:8082) |
| `mcp_extensions_module/` | Go | Cliente MCP que expone tools de servidores externos como jobs (:8083) |
| `the_way_of_the_voice/` | Python (Coqui TTS) | Síntesis de voz del output |
| `JOB_CATALOG.json` | JSON | Catálogo central de jobs disponibles con schemas |
| `mcp_servers.json` | JSON | Configuración de MCP servers externos (Spotify, YouTube, etc.) |

---

## Modelos LLM (Ollama local)

| Rol | Modelo | Uso |
|---|---|---|
| Intent Router / Job Selector | `qwen2.5:14b` | Clasificación estructurada, salida JSON |
| Chatty / Result Formatter | `qwen2.5:7b-instruct` | Respuestas en lenguaje natural |

---

## Categorías de intención

| Categoría | Descripción | Flujo |
|---|---|---|
| `COGNITIVE_REQUEST` | El modelo puede responder usando solo razonamiento interno. | Chatty LLM con historial de sesión |
| `EXTEND_CONTEXT_WITH_SYSTEM_ACTION` | Requiere ejecutar un job del catálogo (datos externos o acción del sistema). | Job selection → ejecución → chatty formatter |
| `END_SESSION` | El usuario se despide o indica que terminó la conversación. | Nueva sesión + respuesta de despedida |

---

## Setup

### 1. Requisitos
- Python 3.10+
- Go 1.22+
- [Ollama](https://ollama.com) corriendo localmente con los modelos:
  ```sh
  ollama pull qwen2.5:14b
  ollama pull qwen2.5:7b-instruct
  ```

### 2. Variables de entorno

Crear `.env` en la raíz del proyecto:
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

### 3. Instalar dependencias Python
```sh
python -m venv venv
source venv/bin/activate
pip install -r brain/requirements.txt
```

### 4. Correr el Job Execution Service (Go)
```sh
cd job_execution_service
go run server/main.go
```

### 5. Correr el Memory Service (Go + PostgreSQL)

Ver [`memory_service/README.md`](./memory_service/README.md) para setup inicial del servidor y deploy.

### 6. Correr el MCP Extensions Module (Go, opcional)

Ver [`mcp_extensions_module/README.md`](./mcp_extensions_module/README.md) para configuración de MCP servers y deploy.

### 7. Correr el pipeline
```sh
python pipeline.py
```

---

## Tests

```sh
# Tests del Job Execution Service
cd job_execution_service && go test ./...
```

---

## Métricas

Ver [`METRICS.md`](./METRICS.md) para métricas sugeridas por etapa del pipeline y guía de implementación.

---

## Palabra de activación

El asistente se llama **LENS**. Esta también debería ser su palabra de activación si se implementa interacción por voz continua.
