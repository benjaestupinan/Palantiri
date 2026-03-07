# mcp_extensions_module

Servicio Go que actúa como cliente MCP (Model Context Protocol), permitiendo extender las capacidades de LENS con cualquier MCP server externo (Spotify, YouTube, etc.) sin modificar el resto del sistema.

---

## Rol en la arquitectura

```
pipeline.py
  ├── al iniciar → MCPExtensionsClient.get_catalog()
  │     └── GET /catalog → mcp_extensions_module
  │           └── lee mcp_servers.json, conecta procesos MCP, retorna tools
  │
  └── al ejecutar job MCP → MCPExtensionsClient.execute_mcp_tool()
        └── POST /execute → mcp_extensions_module
              └── llama al proceso MCP correspondiente vía stdio
```

El módulo es completamente independiente de `brain`, `job_execution_service` y `the_way_of_the_voice`. Se comunica exclusivamente vía HTTP.

---

## Protocolo MCP

MCP (Model Context Protocol) es un protocolo basado en JSON-RPC 2.0 sobre stdio. Un MCP server es un proceso externo (típicamente Node.js) que expone herramientas con este contrato:

```
Cliente → {"jsonrpc":"2.0","method":"tools/list",...}
Servidor → [{name, description, inputSchema}, ...]

Cliente → {"jsonrpc":"2.0","method":"tools/call","params":{"name":"...","arguments":{...}}}
Servidor → {content:[{type:"text",text:"resultado"}]}
```

Los mismos MCP servers diseñados para Claude Desktop funcionan aquí sin modificaciones, porque el protocolo es estándar.

---

## Estructura de archivos

```
mcp_extensions_module/
  cmd/
    main.go                        entry point del servicio
  manager/
    manager.go                     lógica MCP: conexión, descubrimiento, ejecución
  server/
    handlers.go                    handlers HTTP
    router.go                      registro de rutas
  go.mod                           módulo Go con dependencias
  mcp_extensions_module.service    unidad systemd
  deploy.sh                        script de deploy al servidor
```

Archivos relacionados fuera del módulo:

```
mcp_servers.json          (raíz del proyecto) configuración de MCP servers
brain/MCPExtensionsClient.py        cliente Python para este servicio
brain/JOB_CATALOG.py                modificado: agrega merge_mcp_catalog()
pipeline.py                         modificado: mergea catálogo MCP y rutea jobs
```

---

## Go: archivos del módulo

### `manager/manager.go`

Contiene toda la lógica MCP. Es el núcleo del módulo.

#### Types

**`serverConfig`**
Representa la configuración de un MCP server en `mcp_servers.json`.
```go
type serverConfig struct {
    Command string            // ejecutable a lanzar (ej: "npx")
    Args    []string          // argumentos (ej: ["-y", "mcp-server-spotify"])
    Env     map[string]string // variables de entorno específicas del server
}
```

**`serversFile`**
Estructura raíz de `mcp_servers.json`. Mismo formato que Claude Desktop.
```go
type serversFile struct {
    MCPServers map[string]serverConfig // nombre → config
}
```

**`ParameterSpec`**
Representa un parámetro en el formato que espera el cliente Python (compatible con `JOB_CATALOG`).
```go
type ParameterSpec struct {
    Type        string // "string", "number", "boolean", etc.
    Description string
}
```

**`CatalogEntry`**
Representa un tool MCP en el formato `JOB_CATALOG` esperado por el cliente Python.
```go
type CatalogEntry struct {
    JobID       string
    Description string
    Parameters  map[string]ParameterSpec
}
```

**`registeredTool`** (interno)
Mantiene en memoria la información de un tool registrado y la sesión MCP activa para ejecutarlo.
```go
type registeredTool struct {
    serverName   string              // nombre del server en mcp_servers.json
    originalName string              // nombre del tool tal como lo reporta el MCP server
    session      *mcp.ClientSession  // sesión stdio abierta con el proceso MCP
    description  string
    inputSchema  *jsonschema.Schema  // schema JSON del tool (parámetros)
}
```

**`Manager`**
Centraliza el estado de todas las conexiones MCP activas.
```go
type Manager struct {
    mu    sync.RWMutex
    tools map[string]*registeredTool // jobID → tool
}
```
`jobID` es `{serverName}_{toolName}` (ej: `spotify_play_track`), garantizando unicidad entre servidores.

`Global` es la instancia singleton usada por los handlers HTTP.

#### Funciones

**`(*Manager) Init(configPath string) error`**
Lee `mcp_servers.json` e inicializa las conexiones con todos los MCP servers configurados.
- Para cada server en el JSON, llama a `connectServer`.
- Si un server falla, loguea el error y continúa con los demás (degradación parcial).

**`(*Manager) connectServer(name string, cfg serverConfig) error`**
Conecta a un MCP server individual:
1. Crea el `exec.Cmd` con el comando y argumentos configurados.
2. Hereda el entorno del proceso padre (`os.Environ()`) para que `node`, `npx`, etc. estén en PATH. Agrega las env vars específicas del server encima.
3. Crea un cliente MCP con identidad `lens-mcp-client`.
4. Conecta usando `CommandTransport` (stdio).
5. Llama `session.ListTools()` para descubrir todos los tools disponibles.
6. Registra cada tool en el mapa con jobID `{name}_{tool.Name}`.
7. Mantiene la sesión abierta para ejecuciones futuras (no la cierra).

**`(*Manager) Catalog() map[string]CatalogEntry`**
Retorna todos los tools registrados en formato `JOB_CATALOG`. Llamado por el handler de `GET /catalog`. Thread-safe via `RLock`.

**`(*Manager) Execute(jobID string, parameters map[string]any) (string, error)`**
Ejecuta un tool MCP:
1. Busca el tool por `jobID`.
2. Llama `session.CallTool()` usando el `originalName` del tool (sin el prefijo del server).
3. Concatena todos los contenidos `TextContent` del resultado.
4. Retorna el texto de salida o un error.

**`schemaToParams(schema *jsonschema.Schema) map[string]ParameterSpec`** (interno)
Convierte el `inputSchema` de un tool MCP al formato `ParameterSpec` que espera el cliente Python.
- Itera `schema.Properties`.
- Usa `Type` o el primero de `Types` si `Type` está vacío.
- Defaultea a `"string"` si no hay tipo definido.

---

### `server/handlers.go`

Handlers HTTP. Sin lógica de negocio, solo deserialización y delegación al `Manager`.

**`handleCatalog`** — `GET /catalog`
Obtiene el catálogo del `Manager` y lo serializa como JSON. El cliente Python lo usa para mergear en `JOB_CATALOG`.

**`handleExecute`** — `POST /execute`
Deserializa `{job_id, parameters}`, delega al `Manager.Execute()`, retorna el output como texto plano. En caso de error retorna HTTP 400 con el mensaje.

```json
// Request
{"job_id": "spotify_play_track", "parameters": {"track_id": "3n3Ppam7vgaVa1iaRUIOKE"}}

// Response (200 OK)
"Now playing: Bohemian Rhapsody"
```

---

### `server/router.go`

Registra las tres rutas del servicio:

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/catalog` | Retorna tools MCP en formato JOB_CATALOG |
| POST | `/execute` | Ejecuta un tool MCP |

---

### `cmd/main.go`

Entry point del servicio:
1. Carga `.env` del directorio padre (`../.env`) via godotenv.
2. Lee `MCP_SERVERS_CONFIG` del entorno (default: `../mcp_servers.json`).
3. Inicializa el `Manager` con la config de MCP servers.
4. Arranca el servidor HTTP en el puerto `MCP_EXTENSIONS_PORT` (default: `8083`).

---

## Configuración: `mcp_servers.json`

Mismo formato que Claude Desktop. Ubicado en la raíz del proyecto.

```json
{
  "mcpServers": {
    "spotify": {
      "command": "npx",
      "args": ["-y", "mcp-server-spotify"],
      "env": {
        "SPOTIFY_CLIENT_ID": "tu_client_id",
        "SPOTIFY_CLIENT_SECRET": "tu_client_secret"
      }
    },
    "youtube": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-youtube"],
      "env": {
        "YOUTUBE_API_KEY": "tu_api_key"
      }
    }
  }
}
```

Los nombres de los servers (`"spotify"`, `"youtube"`) se usan como prefijo en los `job_id` resultantes: `spotify_play_track`, `youtube_search_videos`, etc.

---

## Python: archivos modificados/nuevos

### `brain/MCPExtensionsClient.py` (nuevo)

Cliente Python para este servicio. Sigue el mismo patrón que `brain/JobExecutorClient.py`.

**`get_catalog() → dict`**
Consulta `GET /catalog` y retorna el catálogo MCP en formato `JOB_CATALOG`. Si el servicio no está disponible, retorna `{}` y loguea el error (degradación silenciosa). También actualiza `_mcp_job_ids` con los job_ids obtenidos.

**`is_mcp_job(job_id: str) → bool`**
Retorna `True` si el `job_id` pertenece a un tool MCP. Usado en `pipeline.py` para el routing.

**`execute_mcp_tool(job: dict) → dict`**
Envía `POST /execute` y retorna el resultado en el mismo formato que `JobExecutorClient.execute_job()`:
```python
{"success": bool, "status_code": int, "response_text": str}
```

---

### `brain/JOB_CATALOG.py` (modificado)

**`merge_mcp_catalog(mcp_catalog: dict)`** (nueva función)
Mergea el catálogo MCP en el diccionario `JOB_CATALOG` en memoria. Como `JOB_CATALOG` es un dict importado por referencia en `validator.py` y `JobSelectionPrompt.py`, el merge es visible automáticamente en todos los módulos sin recargas adicionales.

---

### `pipeline.py` (modificado)

**Al iniciar (module-level):**
```python
_mcp_catalog = MCPExtensionsClient.get_catalog()
if _mcp_catalog:
    merge_mcp_catalog(_mcp_catalog)
```
Esto agrega los tools MCP al `JOB_CATALOG` en memoria antes de procesar cualquier mensaje. El job selector y el validator los ven automáticamente.

**En `process_msg` (routing):**
```python
if MCPExtensionsClient.is_mcp_job(job_obj["job_id"]):
    execution_response = MCPExtensionsClient.execute_mcp_tool(job_obj)
else:
    execution_response = JobExecutorClient.execute_job(job_obj)
```
Si el job seleccionado por el LLM corresponde a un tool MCP, se rutea a `mcp_extensions_module`. De lo contrario, el flujo es idéntico al original.

---

## Variables de entorno

En `.env` del root del proyecto:

```
MCP_EXTENSIONS_HOST=<ip_del_servidor>
MCP_EXTENSIONS_PORT=8083
```

En `/etc/mcp_extensions_module.env` en el servidor (leído por systemd):

```
MCP_EXTENSIONS_PORT=8083
MCP_SERVERS_CONFIG=/home/dofoam/Palantiri/mcp_servers.json
```

---

## Deploy

### Primera vez

```bash
# 1. Crear el archivo de entorno en el servidor
ssh <servidor> "sudo tee /etc/mcp_extensions_module.env << 'EOF'
MCP_EXTENSIONS_PORT=8083
MCP_SERVERS_CONFIG=/home/dofoam/Palantiri/mcp_servers.json
EOF"

# 2. En el servidor: instalar dependencias Go y compilar
ssh <servidor> "cd /home/dofoam/Palantiri/mcp_extensions_module && /usr/local/go/bin/go mod tidy"

# 3. Deploy
PALANTIRI_SERVER=<ip> bash mcp_extensions_module/deploy.sh
```

### Actualizaciones

```bash
# En el servidor: git pull (manual)
# Desde local:
PALANTIRI_SERVER=<ip> bash mcp_extensions_module/deploy.sh
```

### Agregar un nuevo MCP server

1. Editar `mcp_servers.json` en la raíz del proyecto.
2. Hacer `git pull` en el servidor.
3. Reiniciar el servicio: `sudo systemctl restart mcp_extensions_module`.

No se requiere recompilar.

---

## Flujo completo de un mensaje con tool MCP

```
Usuario: "poneme Bohemian Rhapsody en Spotify"

1. pipeline.py → IntentRouterPrompt → qwen2.5:14b
   intent = EXTEND_CONTEXT_WITH_SYSTEM_ACTION

2. pipeline.py → JobSelectionPrompt → qwen2.5:14b
   (el catálogo incluye spotify_play_track mergeado al arrancar)
   job = {job_id: "spotify_play_track", parameters: {query: "Bohemian Rhapsody"}}

3. validator.validate_job(job)
   → busca "spotify_play_track" en JOB_CATALOG (ya mergeado) → válido

4. MCPExtensionsClient.is_mcp_job("spotify_play_track") → True
   MCPExtensionsClient.execute_mcp_tool(job)
   → POST http://servidor:8083/execute

5. mcp_extensions_module recibe la request
   → Manager.Execute("spotify_play_track", {query: "Bohemian Rhapsody"})
   → session.CallTool("play_track", {query: "Bohemian Rhapsody"})  ← nombre original sin prefijo
   → proceso npx mcp-server-spotify responde

6. mcp_extensions_module retorna: "Now playing: Bohemian Rhapsody by Queen"

7. pipeline.py → RedactResponsePrompt → LENS (chatty)
   → "Listo, puse Bohemian Rhapsody de Queen."
```
