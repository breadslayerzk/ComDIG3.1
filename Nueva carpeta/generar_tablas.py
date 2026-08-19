"""
generar_tablas.py
==================
Genera las dos tablas de resultados exigidas en el documento de
CONDICIONES DE ENTREGA para la sustentación:

  Tabla 1: variación de los niveles de cuantificación (2,4,...,256) para
           la frecuencia de muestreo de Nyquist y la señal C.
           Columnas: Niveles de cuantificación | MSE | SNR

  Tabla 2: variación de la frecuencia de muestreo (0.25fs ... 2fs) para
           16 niveles de cuantificación y la señal D (audio).
           Columnas: Frecuencia de muestreo | Error espectral

Uso:
    python generar_tablas.py --audio ruta/a/tu_audio.wav

Genera:
    tabla1_niveles_vs_mse_snr.csv
    tabla1_niveles_vs_mse_snr.png
    tabla2_fs_vs_error_espectral.csv   (si se entrega un audio)
    tabla2_fs_vs_error_espectral.png
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import wavfile

import signal_utils as su


def tabla1_niveles(a_param=2.0, duracion=4.0):
    """Tabla 1: niveles de cuantificación vs MSE y SNR, para fs = Nyquist, señal C."""
    params = {"a": a_param}
    bw = su.ancho_banda_aprox("C", params)
    fs_nyquist = 2 * bw

    t_dense = np.linspace(0, duracion, su.T_DENSE_RESOLUTION)
    x_dense = su.generar_senal("C", t_dense, **params)

    t_muestras, x_muestras, Ts = su.muestrear_senal("C", t_dense, x_dense, fs_nyquist, params)

    niveles_list = [2, 4, 8, 16, 32, 64, 128, 256]
    filas = []
    for n in niveles_list:
        x_cuant, _ = su.cuantificar_uniforme(x_muestras, n)
        x_recon = su.reconstruir_senal(t_muestras, x_cuant, Ts, t_dense)
        mse = su.error_medio_cuadratico(x_dense, x_recon)
        snr = su.snr_cuantificacion(x_dense, mse)
        filas.append({"Niveles de cuantificación": n, "MSE": mse, "SNR (dB)": snr})

    df = pd.DataFrame(filas)
    df.to_csv("tabla1_niveles_vs_mse_snr.csv", index=False)

    fig, ax1 = plt.subplots(figsize=(7, 5))
    ax1.plot(df["Niveles de cuantificación"], df["MSE"], "o-", color="tab:blue", label="MSE")
    ax1.set_xscale("log", base=2)
    ax1.set_yscale("log")
    ax1.set_xlabel("Niveles de cuantificación (N)")
    ax1.set_ylabel("MSE", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(df["Niveles de cuantificación"], df["SNR (dB)"], "s-", color="tab:red", label="SNR")
    ax2.set_ylabel("SNR (dB)", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    plt.title(f"Tabla 1: MSE y SNR vs niveles de cuantificación\n(fs = Nyquist = {fs_nyquist:.2f} Hz, señal C)")
    fig.tight_layout()
    plt.savefig("tabla1_niveles_vs_mse_snr.png", dpi=150)
    plt.close()

    print("\n=== TABLA 1 ===")
    print(df.to_string(index=False))
    print("Guardado: tabla1_niveles_vs_mse_snr.csv / .png")
    return df


def tabla2_frecuencia(ruta_audio, n_niveles=16):
    """Tabla 2: frecuencia de muestreo vs error espectral, para 16 niveles, señal D."""
    fs_original, audio = wavfile.read(ruta_audio)
    if audio.ndim > 1:
        audio = audio[:, 0]
    audio = audio.astype(float)
    audio = audio / (np.max(np.abs(audio)) + 1e-12)

    t_dense = np.arange(len(audio)) / fs_original
    x_dense = audio

    factores = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    filas = []
    for factor in factores:
        fs_test = factor * fs_original
        t_muestras, x_muestras = su.muestrear_audio(audio, fs_original, fs_test)
        Ts = 1.0 / fs_test
        x_cuant, _ = su.cuantificar_uniforme(x_muestras, n_niveles)
        x_recon = su.reconstruir_senal(t_muestras, x_cuant, Ts, t_dense)
        err = su.error_espectral(x_dense, x_recon)
        filas.append({"Frecuencia de muestreo": f"{factor}·fs", "fs (Hz)": fs_test, "Error espectral": err})

    df = pd.DataFrame(filas)
    df.to_csv("tabla2_fs_vs_error_espectral.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(df["fs (Hz)"], df["Error espectral"], "o-", color="tab:purple")
    ax.set_xlabel("Frecuencia de muestreo [Hz]")
    ax.set_ylabel("Error espectral")
    ax.set_title(f"Tabla 2: Error espectral vs frecuencia de muestreo\n(N = {n_niveles} niveles, señal D)")
    fig.tight_layout()
    plt.savefig("tabla2_fs_vs_error_espectral.png", dpi=150)
    plt.close()

    print("\n=== TABLA 2 ===")
    print(df.to_string(index=False))
    print("Guardado: tabla2_fs_vs_error_espectral.csv / .png")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=str, default=None, help="Ruta a un archivo .wav para la Tabla 2")
    parser.add_argument("--a", type=float, default=2.0, help="Parámetro 'a' de la señal C para la Tabla 1")
    args = parser.parse_args()

    tabla1_niveles(a_param=args.a)

    if args.audio:
        tabla2_frecuencia(args.audio)
    else:
        print(
            "\n[Aviso] No se indicó --audio, se omite la Tabla 2. "
            "Ejecuta: python generar_tablas.py --audio tu_archivo.wav"
        )
