# job_execution_service

Servidor HTTP escrito en Go que ejecuta jobs de forma completamente determinista — sin IA. Recibe un job validado desde el pipeline Python y devuelve el resultado de la ejecución.

---

## Correr el servidor

```sh
cd job_execution_service
go run server/main.go
# Escucha en :8081
```

---

## API HTTP

### `GET /health`
Verifica que el servidor esté corriendo.

**Response:**
```
200 OK
Server up and running
```

---

### `POST /job/{jobID}`
Ejecuta un job por su ID.

**Request body:**
```json
{
    "job_id": "get_system_date_and_time",
    "parameters": {}
}
```

**Response exitosa (`200`):**
```
+++ Execution +++
Failed: false
Message: ok
Output: 2024-01-15 10:30:00
+++++++++++++++++
```

**Response con error de ejecución (`400`):**
```
--- Execution ---
Failed: true
Error: <mensaje de error>
-----------------
```

**Job no registrado (`400`):**
```
--- Routing ---
Job doesnt exist in the router
---------------
```

---

## Jobs disponibles

| Job ID | Descripción | Parámetros |
|---|---|---|
| `get_system_date_and_time` | Fecha y hora actual del sistema | ninguno |
| `echo` | Devuelve el mensaje tal cual | `message: string` |
| `readfile` | Lee el contenido de un archivo (máx 100KB) | `path: string` |
| `createfile` | Crea un archivo vacío | `path: string` |
| `editfile` | Edita líneas específicas de un archivo | `path: string`, `edits: [{linenum, newline}]` |
| `list_working_directory` | Lista archivos de un directorio | `path: string` |

---

## Registrar un nuevo job

Los jobs se registran con el patrón **blank import** en `server/main.go`. Al importar el paquete del job, su función `init()` lo registra automáticamente en el router.

### 1. Crear el paquete del job

```
jobs/
└── mi_nuevo_job/
    ├── mi_nuevo_job.go
    └── mi_nuevo_job_test.go
```

**Estructura mínima del job:**
```go
package mi_nuevo_job

import "github.com/benjaestupinan/job-execution-service/jobs/types"

func init() { types.Register("mi_nuevo_job", MiNuevoJob) }

func MiNuevoJob(job types.Job) (types.Execution, error) {
    param := job.Parameters["mi_param"].(string)
    // lógica determinista aquí...
    return types.Execution{
        Output: resultado,
        Msg:    "ok",
        Failed: false,
    }, nil
}
```

### 2. Registrar el import en `server/main.go`

```go
import (
    // ...imports existentes...
    _ "github.com/benjaestupinan/job-execution-service/jobs/mi_nuevo_job"
)
```

### 3. Actualizar el JOB_CATALOG.json

El catálogo se puede regenerar automáticamente con la herramienta incluida:

```sh
cd job_execution_service/cmd/generate_catalog
go run main.go
```

Esto escanea todos los paquetes de jobs, infiere los parámetros y tipos desde el código Go, y actualiza `JOB_CATALOG.json` en la raíz del proyecto. Las descripciones escritas manualmente en el JSON se preservan.

---

## Tests

```sh
cd job_execution_service && go test ./...
```

---

## Tipos internos

Definidos en `jobs/types/types.go`:

```go
type Job struct {
    JobID      string
    Parameters map[string]any
}

type Execution struct {
    Output string
    Msg    string
    Failed bool
}

type JobFunc func(Job) (Execution, error)
```
