from TTS.api import TTS
import sounddevice as sd

# cargar modelo
tts = TTS(model_name="tts_models/es/css10/vits", gpu=False)

# generar audio (numpy array)
wav = tts.tts("Hola mi nombre es LENS, en que te puedo ayudar dofoam")

# reproducir
sd.play(wav, samplerate=tts.synthesizer.output_sample_rate)
sd.wait()
