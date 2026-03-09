import base64
import io

import sounddevice as sd
import soundfile as sf


def play_audio(audio_b64: str):
    audio_bytes = base64.b64decode(audio_b64)
    buf = io.BytesIO(audio_bytes)
    data, samplerate = sf.read(buf)
    sd.play(data, samplerate)
    sd.wait()
