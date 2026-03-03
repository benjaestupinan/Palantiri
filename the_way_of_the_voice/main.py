from TTS.api import TTS
import sounddevice as sd

def speak(msg):
    tts = TTS(model_name="tts_models/es/css10/vits", gpu=False)
    wav = tts.tts(msg)
    sd.play(wav, samplerate=tts.synthesizer.output_sample_rate)
    sd.wait()
