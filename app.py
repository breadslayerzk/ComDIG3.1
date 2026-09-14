"""Interfaz Streamlit para la Simulación de Digitalización de Señales, Fase I."""

import io

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from scipy.io import wavfile

import signal_utils as su


NIVELES_DISPONIBLES = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
CONSTANTE_A = 2.0  # El enunciado la define como constante de libre elección.


def normalizar_audio(audio):
    """Convierte WAV PCM a flotante [-1, 1] y conserva la cantidad de bits."""
    if np.issubdtype(audio.dtype, np.unsignedinteger):
        info = np.iinfo(audio.dtype)
        centro = (info.max + 1) / 2
        normalizado, bits = (audio.astype(float) - centro) / centro, audio.dtype.itemsize * 8
    elif np.issubdtype(audio.dtype, np.signedinteger):
        info = np.iinfo(audio.dtype)
        escala = max(abs(info.min), abs(info.max))
        normalizado, bits = audio.astype(float) / escala, audio.dtype.itemsize * 8
    else:
        normalizado, bits = np.clip(audio.astype(float), -1, 1), 16
    if normalizado.ndim > 1:
        normalizado = normalizado.mean(axis=1)
    return normalizado, bits


def a_wav_bytes(x, fs):
    x = np.asarray(x, dtype=float)
    x = np.clip(x / (np.max(np.abs(x)) + 1e-12), -1, 1)
    buffer = io.BytesIO()
    wavfile.write(buffer, int(fs), (x * 32767).astype(np.int16))
    return buffer.getvalue()


st.set_page_config(page_title="Digitalización de Señales — Fase I", layout="wide")
st.title("Simulación de un Sistema de Digitalización de Señales")
st.caption("Universidad del Cauca · Telecomunicaciones Digitales · Fase I")

st.sidebar.header("1. Señal de entrada")
opcion = st.sidebar.selectbox("Selecciona la señal (RF2)", ["A: Coseno", "B: Sinc", "C: Sinc² + Sinc", "D: Audio"])
codigo = opcion[0]
parametros, audio, fs_audio, bits_audio = {}, None, None, None

if codigo == "A":
    parametros["A"] = st.sidebar.number_input("Amplitud A", min_value=0.1, value=1.0, step=0.1)
    parametros["f0"] = st.sidebar.number_input("Frecuencia f0 [Hz]", min_value=0.1, value=5.0, step=0.5)
    duracion = st.sidebar.slider("Duración a visualizar [s]", 0.5, 5.0, 2.0)
elif codigo in ("B", "C"):
    parametros["a"] = CONSTANTE_A
    duracion = st.sidebar.slider("Duración a visualizar [s]", 0.5, 10.0, 4.0)
    st.sidebar.caption(f"Constante a = {CONSTANTE_A:g} (fijada para la simulación).")
else:
    archivo = st.sidebar.file_uploader("Cargar audio WAV (mínimo 20 s)", type=["wav"])
    if archivo is not None:
        try:
            fs_audio, datos = wavfile.read(io.BytesIO(archivo.getvalue()))
            audio, bits_audio = normalizar_audio(datos)
            duracion = len(audio) / fs_audio
            if duracion < 20:
                st.sidebar.error(f"El audio dura {duracion:.1f} s; RF2 exige al menos 20 s.")
                audio = None
            else:
                st.sidebar.success(f"Audio válido: {duracion:.1f} s · {fs_audio} Hz · {bits_audio} bits")
        except Exception as error:
            st.sidebar.error(f"No se pudo leer el WAV: {error}")

st.sidebar.header("2. Muestreo (RF3)")
if codigo == "D":
    if audio is None:
        st.info("Carga un WAV de al menos 20 segundos para procesar la señal D.")
        st.stop()
    fs = st.sidebar.slider(
        "Nueva frecuencia de muestreo [Hz]",
        min_value=max(1, int(fs_audio * 0.25)), max_value=int(fs_audio * 2),
        value=int(fs_audio), step=max(1, int(fs_audio / 100)),
    )
else:
    banda = su.ancho_banda_aprox(codigo, parametros)
    fs_nyquist = 2 * banda
    st.sidebar.caption(f"Ancho de banda = {banda:.2f} Hz · Nyquist = {fs_nyquist:.2f} Hz")
    fs = st.sidebar.slider("Frecuencia de muestreo fs [Hz]", 1.0, float(max(10 * fs_nyquist, 50)), float(fs_nyquist), 0.5)
st.sidebar.write(f"Periodo de muestreo: Ts = {1 / fs:.6f} s")

st.sidebar.header("3. Cuantificación (RF4)")
n_niveles = st.sidebar.select_slider("Número de niveles N (potencia de 2)", options=NIVELES_DISPONIBLES, value=16)

try:
    if codigo != "D":
        t_original = np.linspace(0, duracion, su.T_DENSE_RESOLUTION)
        x_original = su.generar_senal(codigo, t_original, **parametros)
        t_muestras, x_muestras, ts = su.muestrear_senal(codigo, t_original, x_original, fs, parametros)
    else:
        t_original = np.arange(len(audio)) / fs_audio
        x_original = audio
        t_muestras, x_muestras = su.muestrear_audio(audio, fs_audio, fs)
        ts = 1 / fs

    x_cuantificada, delta = su.cuantificar_uniforme(x_muestras, n_niveles)
    x_reconstruida = su.reconstruir_senal(t_muestras, x_cuantificada, ts, t_original)
    mse, snr = su.metricas_cuantificacion(x_muestras, x_cuantificada)
    error_espectral = su.error_espectral(x_original, x_reconstruida)

    if codigo == "D":
        niveles_originales = 2 ** bits_audio
        x_cuant_original, _ = su.cuantificar_uniforme(x_muestras, niveles_originales)
        x_recon_original = su.reconstruir_senal(t_muestras, x_cuant_original, ts, t_original)
        mse_original, snr_original = su.metricas_cuantificacion(x_muestras, x_cuant_original)
        error_original = su.error_espectral(x_original, x_recon_original)
except Exception as error:
    st.error(f"Error controlado durante la simulación: {error}")
    st.stop()

st.header("Métricas de desempeño (RF5)")
if codigo == "D":
    izquierda, derecha = st.columns(2)
    with izquierda:
        st.subheader(f"Cuantificación original ({bits_audio} bits / {niveles_originales:,} niveles)")
        st.metric("MSE de cuantificación", f"{mse_original:.6g}")
        st.metric("SNR de cuantificación", f"{snr_original:.2f} dB")
        st.metric("Error espectral de reconstrucción", f"{error_original:.5f}")
    with derecha:
        st.subheader(f"Cuantificación seleccionada ({n_niveles} niveles)")
        st.metric("MSE de cuantificación", f"{mse:.6g}")
        st.metric("SNR de cuantificación", f"{snr:.2f} dB")
        st.metric("Error espectral de reconstrucción", f"{error_espectral:.5f}")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("MSE de cuantificación", f"{mse:.6g}")
    c2.metric("SNR de cuantificación", f"{snr:.2f} dB")
    c3.metric("Error espectral de reconstrucción", f"{error_espectral:.5f}")
st.caption(f"Paso de cuantificación Δ = {delta:.6g} · fs = {fs:.2f} Hz · Ts = {ts:.6f} s")

st.header("Visualizaciones (RF6)")
frecuencias_original, espectro_original = su.espectro(x_original, fs_audio if codigo == "D" else len(x_original) / duracion)
frecuencias_muestras, espectro_muestras = su.espectro(x_muestras, fs)
limite = min(len(t_muestras), 500)
figura, ejes = plt.subplots(3, 2, figsize=(12, 9))
ejes[0, 0].plot(t_original, x_original, lw=0.8); ejes[0, 0].set_title("a) Señal original en el tiempo"); ejes[0, 0].set_xlabel("Tiempo [s]")
ejes[0, 1].plot(frecuencias_original, espectro_original); ejes[0, 1].set_title("b) Espectro de la señal original"); ejes[0, 1].set_xlabel("Frecuencia [Hz]")
ejes[1, 0].stem(t_muestras[:limite], x_muestras[:limite], basefmt=" "); ejes[1, 0].set_title("c) Señal muestreada en el tiempo"); ejes[1, 0].set_xlabel("Tiempo [s]")
ejes[1, 1].plot(frecuencias_muestras, espectro_muestras); ejes[1, 1].set_title("d) Espectro de la señal muestreada"); ejes[1, 1].set_xlabel("Frecuencia [Hz]")
ejes[2, 0].step(t_muestras[:limite], x_cuantificada[:limite], where="mid"); ejes[2, 0].set_title("e) Señal cuantificada"); ejes[2, 0].set_xlabel("Tiempo [s]")
ejes[2, 1].plot(t_original, x_reconstruida, lw=0.8); ejes[2, 1].set_title("f) Señal reconstruida"); ejes[2, 1].set_xlabel("Tiempo [s]")
for eje in ejes.flat:
    eje.grid(alpha=0.25)
figura.tight_layout()
st.pyplot(figura)

if codigo == "D":
    st.header("Reproducción de audio (RF8)")
    original, reconstruido = st.columns(2)
    with original:
        st.write("Audio original")
        st.audio(a_wav_bytes(x_original, fs_audio), format="audio/wav")
    with reconstruido:
        st.write("Audio reconstruido (resampling + recuantificación)")
        st.audio(a_wav_bytes(x_reconstruida, fs_audio), format="audio/wav")

st.divider()
st.caption("RNF2: muestreo, cuantificación y reconstrucción se implementan explícitamente. FFT solo se usa para análisis espectral.")
