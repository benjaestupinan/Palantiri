# brain

Módulo Python que implementa el núcleo cognitivo del pipeline de LENS: clasifica la intención del usuario, selecciona y valida el job correspondiente, y construye los prompts para los modelos LLM.

---

## Flujo real del módulo

```
Usuario (lenguaje natural)
        │
        ▼
┌──────────────────────────────┐
│  IntentRouterPrompt          │
│  + PromptLLM.ask_qwen()      │  ← Qwen 2.5 3B
│  Clasifica en categoría      │
└──────────────┬───────────────┘
       ┌───────┴────────────────────────┐
       │                                │
       ▼                                ▼
COGNITIVE_REQUEST          COGNITIVE_REQUEST_WITH_EXTRA_DATA
       │                   o SYSTEM_ACTION
       │                                │
       ▼                                ▼
PromptLLM.ask_chatty()    ┌─────────────────────────────────┐
(respuesta directa)       │  JobSelectionPrompt              │
                          │  + PromptLLM.ask_qwen()          │  ← Qwen 2.5 3B
                          │  Elige job del JOB_CATALOG.json  │
                          └──────────────┬──────────────────┘
                                         │
                                 job_id == null?
                                  ╱              ╲
                                sí               no
                                 │                │
                                 ▼                ▼
                    RedactResponsePrompt     validator.validate_job()
                    .get_no_capability_      schema + tipos + existencia
                    prompt()                          │
                    + ask_chatty()           inválido?
                    (fallback)                ╱              ╲
                                            sí               no
                                             │                │
                                             ▼                ▼
                                  hallucinated?        JobExecutorClient
                                  job_id?              HTTP POST :8081
                                   ╱    ╲                     │
                                  sí    no              fallido (non-200)?
                                   │     │               ╱           ╲
                                   ▼     ▼              sí            no
                              fallback  error            │              │
                              chatty    msg              ▼              ▼
                              (no                    error       RedactResponsePrompt
                              capability)            crudo       .get_response_
                                                                 message_prompt()
                                                                 + ask_chatty()
                                                                 (respuesta natural)
```

---

## Categorías de intención

*(Pendiente: reducir a 2 categorías — COGNITIVE_REQUEST y ACTION_REQUEST — ya que COGNITIVE_REQUEST_WITH_EXTRA_DATA y SYSTEM_ACTION siguen exactamente el mismo flujo en el pipeline)*

| Categoría | Descripción | Flujo |
|---|---|---|
| `COGNITIVE_REQUEST` | El modelo puede responder usando solo razonamiento interno. No requiere datos externos ni acciones. | Directo al chatty LLM |
| `COGNITIVE_REQUEST_WITH_EXTRA_DATA` | Solicita información que requiere datos externos al modelo (hora, fecha, estado del sistema). | Job selection → ejecución |
| `SYSTEM_ACTION` | Solicita que el sistema ejecute o programe una acción. | Job selection → ejecución |

---

## Archivos

| Archivo | Descripción |
|---|---|
| `IntentRouterPrompt.py` | Genera el prompt para clasificar la intención del mensaje del usuario |
| `JobSelectionPrompt.py` | Genera el prompt para seleccionar un job del catálogo, incluye reglas estrictas anti-alucinación |
| `RedactResponsePrompt.py` | Genera prompts para el chatty LLM: respuesta natural tras ejecución exitosa, y mensaje de "sin capacidad" |
| `PromptLLM.py` | Cliente HTTP para Ollama. `ask_qwen()` para clasificación/selección, `ask_chatty()` para lenguaje natural |
| `JOB_CATALOG.py` | Carga el `JOB_CATALOG.json` de la raíz como diccionario Python |
| `JobExecutorClient.py` | Envía jobs validados al Go service vía `POST /job/{job_id}` |
| `validator.py` | Valida estructura y tipos del job seleccionado contra el catálogo. Soporta tipos anidados y jobs compuestos |

---

## JOB_CATALOG.json

El catálogo central (en la raíz del proyecto) define todos los jobs disponibles con sus schemas de parámetros. Es la fuente de verdad compartida entre:

- `JobSelectionPrompt.py` — incluye el catálogo completo en el prompt del LLM
- `validator.py` — valida los jobs seleccionados contra los schemas del catálogo
- `job_execution_service/cmd/generate_catalog/` — herramienta Go para regenerar el JSON desde el código

---

## Variables de entorno

Configurar en `.env` (ver `.env.example` o el README raíz):

```env
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
JOB_EXECUTOR_HOST=localhost
JOB_EXECUTOR_PORT=8081
```
