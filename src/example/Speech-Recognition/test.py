# =========== Speech to text module ============
# from deepspeech import Model
import wave
import numpy as np
import time
import io

# ds = Model("./Model/deepspeech-0.9.3-models.pbmm")
# ds.enableExternalScorer("./Model/deepspeech-0.9.3-models.scorer")

with open("./Audio/2830-3980-0043.wav", 'rb') as f:
    data = f.read()

fp = io.BytesIO(data)

fin = wave.open(fp)
print(fin.getnframes())
audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
fin.close()

# result = ds.stt(audio)

print(audio)