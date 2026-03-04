# Métricas del pipeline

Métricas sugeridas por etapa para evaluar la salud del pipeline y detectar regresiones.

---

## IntentRouter

| Métrica | Descripción | Señal de problema |
|---|---|---|
| `intent_distribution` | % de cada categoría (`COGNITIVE_REQUEST`, `COGNITIVE_REQUEST_WITH_EXTRA_DATA`, `SYSTEM_ACTION`) en el tiempo | Una categoría domina de forma inesperada → posible sesgo del clasificador |
| `intent_confidence_avg` | Promedio del campo `confidence` retornado por el LLM | Cae consistentemente por debajo de 0.7 → el modelo está dudando en la clasificación |

---

## JobSelection

| Métrica | Descripción | Señal de problema |
|---|---|---|
| `null_job_rate` | % de llamadas donde `job_id` vuelve `null` | Muy alto → catálogo no cubre necesidades reales, o el prompt es demasiado conservador. Muy bajo → puede estar sobreseleccionando |
| `validation_failure_rate` | % de jobs seleccionados que fallan en el validador | Alto → el LLM está inventando parámetros o estructuras |
| `fallback_rate` | % de requests que terminan en el chatty LLM por `job_id = null` | Útil para ver si el nuevo fallback se usa demasiado o muy poco |
| `job_confidence_distribution` | Distribución del campo `confidence` de los jobs seleccionados | Mayoría en 0.4–0.6 → selecciones poco seguras, revisar el prompt |

---

## RedactResponse

| Métrica | Descripción | Señal de problema |
|---|---|---|
| `negative_keywords_in_success` | % de respuestas generadas tras ejecución exitosa que contienen palabras como `"falló"`, `"error"`, `"no pudo"`, `"no fue posible"` | Cualquier valor > 0 indica que el LLM está respondiendo como si hubiera fallo en una ejecución exitosa |

> Esta es la métrica directa para validar el fix del `RedactResponsePrompt`. Antes del fix podía ser alta por el default `failed = True` cuando el regex no encontraba el campo `Failed:`. Después del fix debería ser cercana a 0.

---

## Pipeline completo

| Métrica | Descripción |
|---|---|
| `end_to_end_success_rate` | % de requests que retornan una respuesta en lenguaje natural (no un error crudo) |
| `execution_failure_rate` | % de requests donde el job executor retorna non-200 |
| `path_distribution` | Distribución de los caminos que toma cada request (ver tabla abajo) |

### Distribución de caminos esperada

```
COGNITIVE_REQUEST                  → chatty directo
COGNITIVE_WITH_DATA / SYSTEM_ACTION → job ejecutado → respuesta natural
COGNITIVE_WITH_DATA / SYSTEM_ACTION → null job_id   → fallback chatty
COGNITIVE_WITH_DATA / SYSTEM_ACTION → validación fallida → error
COGNITIVE_WITH_DATA / SYSTEM_ACTION → ejecución fallida  → error crudo
```

---

## Implementación sugerida

Todas estas métricas se pueden obtener loggeando el estado del pipeline en cada paso de `process_msg`:

- `intent_obj` (categoría + confidence) → métricas de IntentRouter
- `job_obj` (job_id + confidence) y resultado del validador → métricas de JobSelection
- `execution_response` (status_code) → métricas de ejecución
- Respuesta final del chatty LLM → métrica de `negative_keywords_in_success`
