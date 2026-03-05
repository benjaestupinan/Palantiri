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
                            │
                            ▼
            ┌───────────────────────────┐
            │   1. Intent Router (LLM)  │
            │   Qwen 2.5 3B via Ollama  │
            └──────────────┬────────────┘
                   ┌───────┴────────┐
                   │                │
                   ▼                ▼
        COGNITIVE_REQUEST    COGNITIVE_REQUEST_WITH_EXTRA_DATA
                   │         o SYSTEM_ACTION
                   │                │
                   ▼                ▼
          ┌──────────────┐  ┌───────────────────────┐
          │  Chatty LLM  │  │  2. Job Selector (LLM) │
          │  Qwen 2.5 7B │  │   Qwen 2.5 3B          │
          └──────────────┘  └──────────┬────────────┘
                                       │
                              job_id = null?
                                  │       │
                                  ▼       ▼
                           fallback   ┌──────────────────┐
                           chatty     │  3. Validator     │
                           (no        │  schema + tipos   │
                           capability)└──────┬───────────┘
                                             │
                                    inválido / hallucinated?
                                         │       │
                                         ▼       ▼
                                      error   ┌──────────────────────┐
                                      msg     │  4. Job Executor      │
                                              │  Go HTTP service      │
                                              │  :8081                │
                                              └──────────┬───────────┘
                                                         │
                                                    fallido?
                                                   │       │
                                                   ▼       ▼
                                               error   ┌──────────────────────┐
                                               crudo   │  5. Result Formatter  │
                                                       │  Chatty LLM           │
                                                       └──────────┬────────────┘
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
| `job_execution_service/` | Go | Servidor HTTP que ejecuta jobs de forma determinista |
| `the_way_of_the_voice/` | Python (Coqui TTS) | Síntesis de voz del output |
| `JOB_CATALOG.json` | JSON | Catálogo central de jobs disponibles con schemas |

---

## Modelos LLM (Ollama local)

| Rol | Modelo | Uso |
|---|---|---|
| Intent Router / Job Selector | `qwen2.5:3b` | Clasificación estructurada, salida JSON |
| Chatty / Result Formatter | `qwen2.5:7b-instruct` | Respuestas en lenguaje natural |

---

## Setup

### 1. Requisitos
- Python 3.10+
- Go 1.22+
- [Ollama](https://ollama.com) corriendo localmente con los modelos:
  ```sh
  ollama pull qwen2.5:3b
  ollama pull qwen2.5:7b-instruct
  ```

### 2. Variables de entorno

Crear `brain/.env`:
```env
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
JOB_EXECUTOR_HOST=localhost
JOB_EXECUTOR_PORT=8081
```

### 3. Instalar dependencias Python
```sh
cd brain
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Correr el Job Execution Service (Go)
```sh
cd job_execution_service
go run server/main.go
```

### 5. Correr el pipeline
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
