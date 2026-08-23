"""Crea un WAV de 20 s para probar RF2, RF7, RF8 y la Tabla 2.

No sustituye una grabación si el docente exige una fuente específica, pero deja
una señal de audio reproducible y válida para verificar todo el flujo.
"""

import numpy as np
from scipy.io import wavfile


FS = 16_000
DURACION = 20


def crear_audio_demo(ruta="audio_demo_20s.wav"):
    t = np.arange(FS * DURACION) / FS
    envolvente = 0.45 + 0.35 * np.sin(2 * np.pi * 0.23 * t)
    audio = envolvente * (
        0.55 * np.sin(2 * np.pi * 220 * t)
        + 0.30 * np.sin(2 * np.pi * 440 * t)
        + 0.15 * np.sin(2 * np.pi * 880 * t)
    )
    audio /= np.max(np.abs(audio))
    wavfile.write(ruta, FS, (audio * 32767).astype(np.int16))
    print(f"Audio creado: {ruta} ({DURACION} s, {FS} Hz, PCM 16 bits)")


if __name__ == "__main__":
    crear_audio_demo()
