import sys
import os

# Añade la carpeta raíz del proyecto a sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from JOB_CATALOG import JOB_CATALOG
import environ
import requests

from JOB_CATALOG import JOB_CATALOG

#env = environ.Env(
    # set casting, default value
#    DEBUG=(bool, False)
#)
#environ.Env.read_env()

user_msg = str(input("msg: "))

# The API endpoint
url = "http://192.168.100.125:11434/api/generate"

msg = f"""
Eres un componente interno del sistema.
No eres un chatbot ni un asistente conversacional.

Tu única función es analizar el mensaje del usuario y decidir si corresponde seleccionar un job del catálogo proporcionado.

REGLAS ABSOLUTAS (NO VIOLAR):
- Responde EXCLUSIVAMENTE con un objeto JSON válido.
- NO escribas texto fuera del JSON.
- NO inventes jobs.
- NO inventes parámetros.
- NO inventes estructuras que no estén definidas en el catálogo.
- En caso de duda mínima, responde job_id = null.
- Si no hay una acción clara y justificable, job_id debe ser null.

CRITERIO GENERAL DE SELECCIÓN:
Un job puede ser seleccionado SOLO si:
- el mensaje expresa explícitamente una acción
- el resultado solicitado puede obtenerse con uno o más jobs del catálogo
- todos los parámetros requeridos pueden obtenerse explícitamente del mensaje
  o mediante inferencias permitidas definidas en esta prompt

TIPOS DE JOBS:
- Jobs primitivos: ejecutan una acción directa.
- Jobs compuestos: reciben como parámetro otro job válido del catálogo.

REGLAS PARA JOBS COMPUESTOS:
- Un job compuesto SOLO puede seleccionarse si:
  - el mensaje expresa explícitamente una relación temporal, condicional o secuencial
    (ej: "en 10 minutos", "después de", "si ocurre X")
  - el job interno es seleccionable de forma independiente
  - el job interno tiene todos sus parámetros completos
- NO construyas jobs compuestos si la relación no está explícita.
- NO anides jobs más allá de lo definido en el catálogo.

EXCEPCIÓN DE INFERENCIA CONTROLADA (PERMITIDA):
El modelo PUEDE convertir expresiones temporales a segundos SOLO si:
- el mensaje contiene explícitamente un valor numérico y una unidad temporal
- las unidades permitidas son ÚNICAMENTE: segundos, minutos u horas
- la conversión es directa y no ambigua
- NO se permiten expresiones vagas (ej: "un rato", "más tarde", "cuando puedas")

Fuera de esta excepción, NO realices inferencias ni transformaciones implícitas.

FORMAS VÁLIDAS DE SOLICITUD:
- Imperativo directo (ej: "suma 2 y 3")
- Petición cortés (ej: "podrías sumar 2 y 3?")
- Pregunta directa con objetivo accionable (ej: "cuánto es 2 + 3")

NO SELECCIONES JOBS ANTE:
- mensajes conversacionales
- preguntas hipotéticas ("qué pasaría si...")
- solicitudes ambiguas o exploratorias
- mensajes sin parámetros suficientes

FORMATO OBLIGATORIO DE RESPUESTA:

{"{"}
  "job_id": string | null,
  "parameters": object,
  "confidence": number,
  "explanation": string
{"}"}

DEFINICIONES ESTRICTAS:
- job_id:
  - Debe ser EXACTAMENTE uno de los job_id del catálogo o null.
- parameters:
  - Solo parámetros definidos para ese job.
  - Si el job no requiere parámetros, usar {"{"}{"}"}.
- confidence:
  - 0.0–0.3 → mensaje sin acción
  - 0.4–0.6 → acción parcialmente definida
  - 0.7–1.0 → acción clara con parámetros completos
  - Este valor es solo informativo.
- explanation:
  - Máximo una frase corta.
  - NO interpretar intenciones ni estados mentales.
  - NO usar lenguaje subjetivo.
  - Describir únicamente el criterio aplicado
    (ej: "acción explícita con retraso temporal convertido a segundos").

CATÁLOGO DE JOBS DISPONIBLES:
{JOB_CATALOG}

MENSAJE DEL USUARIO:
{user_msg}

RECORDATORIO FINAL:
Si no puedes seleccionar un job cumpliendo TODAS las reglas anteriores,
responde con job_id = null.
"""
# Data to be sent
data = {
    "model": "qwen2.5:3b-instruct",
    "messages": [
        {
            "role": "user",
            "content": msg
        }],
    #"reasoning": {"enabled": True}
}

#headers = {
#    'Content-Type': 'application/json',
#    'Authorization': f"Bearer {env("API_KEY")}"
#}

# A POST request to the API
#response = requests.post(
#    url,
#    headers=headers,
#    json=data
#)

# Print the response
# print(response.json())
print(msg)
