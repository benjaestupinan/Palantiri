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
│  + PromptLLM.ask_qwen()      │  ← qwen2.5:14b
│  Clasifica en categoría      │
└──────────────┬───────────────┘
   ┌───────────┼──────────────────────┐
   │           │                      │
   ▼           ▼                      ▼
END_SESSION  COGNITIVE_REQUEST  EXTEND_CONTEXT_WITH
   │               │             SYSTEM_ACTION
   │               │                  │
   ▼               ▼                  ▼
nueva sesión  MemoryClient       ┌──────────────────────────────────┐
+ despedida   .get_history()     │  JobSelectionPrompt              │
                   │             │  + PromptLLM.ask_qwen()          │  ← qwen2.5:14b
                   ▼             │  Elige job del JOB_CATALOG.json  │
              ask_chatty()       └──────────────┬───────────────────┘
              (respuesta)                        │
                   │                    job_id == null?
                   ▼                     ╱              ╲
              save_message()            sí               no
              en memoria                │                │
                                        ▼                ▼
                           RedactResponsePrompt     validator.validate_job()
                           .get_no_capability_      schema + tipos + existencia
                           prompt()                          │
                           + ask_chatty()           inválido?
                           (fallback)                ╱              ╲
                                                    sí               no
                                                     │                │
                                                     ▼                ▼
                                          hallucinated?         Router
                                          job_id?          (is_mcp_job?)
                                           ╱    ╲               │
                                          sí    no         ┌────┴────┐
                                           │     │         ▼         ▼
                                           ▼     ▼    MCP job    Go job
                                       fallback error    │           │
                                       chatty  msg  :8083        :8081
                                                         └────┬────┘
                                                              │
                                                         fallido?
                                                          ╱        ╲
                                                         sí         no
                                                          │          │
                                                          ▼          ▼
                                                      error    RedactResponsePrompt
                                                      crudo    .get_response_
                                                               message_prompt()
                                                               + ask_chatty()
                                                               + save_message()
```

---

## Categorías de intención

| Categoría | Descripción | Flujo |
|---|---|---|
| `COGNITIVE_REQUEST` | El modelo puede responder usando solo razonamiento interno. No requiere capacidades externas. | Chatty LLM con historial de sesión |
| `EXTEND_CONTEXT_WITH_SYSTEM_ACTION` | Requiere ejecutar un job del catálogo (datos externos o acción del sistema). | Job selection → validación → ejecución → formatter |
| `END_SESSION` | El usuario se despide o indica que terminó la conversación. | Nueva sesión + despedida |

---

## Archivos

| Archivo | Descripción |
|---|---|
| `IntentRouterPrompt.py` | Genera el prompt para clasificar la intención del mensaje del usuario |
| `JobSelectionPrompt.py` | Genera el prompt para seleccionar un job del catálogo, incluye reglas estrictas anti-alucinación |
| `ParameterExtractionPrompt.py` | Genera el prompt para extraer parámetros de un job prerequisito hacia el job objetivo |
| `PrerequisiteJobPrompt.py` | Genera el prompt para seleccionar el job que debe correr primero cuando uno falla por parámetros faltantes |
| `RedactResponsePrompt.py` | Genera prompts para el chatty LLM: respuesta natural tras ejecución exitosa, y mensaje de "sin capacidad" |
| `PromptLLM.py` | Cliente HTTP para Ollama. `ask_qwen()` para clasificación/selección, `ask_chatty()` para lenguaje natural |
| `JOB_CATALOG.py` | Carga el `JOB_CATALOG.json` de la raíz como diccionario Python. Incluye `merge_mcp_catalog()` |
| `JobExecutorClient.py` | Envía jobs Go al service vía `POST /job/{job_id}` (:8081) |
| `MCPExtensionsClient.py` | Obtiene catálogo MCP y ejecuta tools via `mcp_extensions_module` (:8083) |
| `MemoryClient.py` | Cliente para `memory_service`: crea sesiones, guarda mensajes, consulta historial y búsqueda (:8082) |
| `MemoryContextPrompt.py` | Genera el bloque de contexto a partir de mensajes históricos para enriquecer respuestas |
| `validator.py` | Valida estructura y tipos del job seleccionado contra el catálogo. Soporta tipos anidados y jobs compuestos |

---

## JOB_CATALOG.json

El catálogo central (en la raíz del proyecto) define todos los jobs disponibles con sus schemas de parámetros. Es la fuente de verdad compartida entre:

- `JobSelectionPrompt.py` — incluye el catálogo completo en el prompt del LLM
- `validator.py` — valida los jobs seleccionados contra los schemas del catálogo
- `job_execution_service/cmd/generate_catalog/` — herramienta Go para regenerar el JSON desde el código
- `MCPExtensionsClient.py` + `merge_mcp_catalog()` — los tools MCP se mergean al catálogo en memoria al arrancar

---

## Variables de entorno

Configurar en `.env` en la raíz del proyecto:

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
