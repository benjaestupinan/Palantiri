# the_way_of_the_voice

Módulo Python de síntesis de voz (TTS) para LENS. Convierte el texto de respuesta del pipeline en audio y lo reproduce en tiempo real.

---

## Uso

```python
from the_way_of_the_voice.tts_service import speak

speak("Hola, soy LENS.")
```

---

## Archivos

| Archivo | Descripción |
|---|---|
| `tts_service.py` | Expone `speak(msg)`: sintetiza el texto con Coqui TTS y lo reproduce con sounddevice |

---

## Dependencias

- [Coqui TTS](https://github.com/coqui-ai/TTS) — modelo `tts_models/es/css10/vits` (español)
- `sounddevice` — reproducción de audio en tiempo real

Instalar junto con el resto del proyecto:
```sh
pip install -r input_intent_router/requirements.txt
```

---

## Integración con el pipeline

`pipeline.py` llama a `speak()` con la respuesta final del asistente:

```python
from the_way_of_the_voice.tts_service import speak
speak(process_msg(msg))
```

El módulo corre en CPU (`gpu=False`). Para habilitar GPU, modificar `tts_service.py`.
