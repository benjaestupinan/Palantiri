import io

import numpy as np
import scipy.io.wavfile as wav
from TTS.api import TTS

_tts = TTS(model_name="tts_models/es/css10/vits", gpu=False)

def synthesize(text: str) -> bytes:
    samples = _tts.tts(text)
    sample_rate = _tts.synthesizer.output_sample_rate
    buf = io.BytesIO()
    wav.write(buf, sample_rate, np.array(samples, dtype=np.float32))
    return buf.getvalue()
