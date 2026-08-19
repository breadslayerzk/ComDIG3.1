"""Bloques DSP implementados para la Fase I.

No se usan rutinas de muestreo, cuantificación o reconstrucción de alto nivel.
La FFT se usa únicamente para análisis espectral (RF5 y RF6).
"""

import numpy as np


T_DENSE_RESOLUTION = 20_000
RADIO_SINC = 16
TAMANO_BLOQUE_RECONSTRUCCION = 4_096


def sinc_manual(x):
    """sinc normalizada: sin(pi*x)/(pi*x), con sinc(0)=1."""
    x = np.asarray(x, dtype=float)
    salida = np.ones_like(x)
    mascara = x != 0
    salida[mascara] = np.sin(np.pi * x[mascara]) / (np.pi * x[mascara])
    return salida


def senal_a(t, A=1.0, f0=5.0):
    return A * np.cos(2 * np.pi * f0 * t)


def senal_b(t, a=2.0):
    return sinc_manual(2 * a * t)


def senal_c(t, a=2.0):
    return sinc_manual(a * t) ** 2 + senal_b(t, a)


def generar_senal(tipo, t, **parametros):
    if tipo == "A":
        return senal_a(t, parametros.get("A", 1.0), parametros.get("f0", 5.0))
    if tipo == "B":
        return senal_b(t, parametros.get("a", 2.0))
    if tipo == "C":
        return senal_c(t, parametros.get("a", 2.0))
    raise ValueError(f"Tipo de señal no reconocido: {tipo}")


def ancho_banda_aprox(tipo, parametros):
    """Ancho de banda teórico para sugerir Nyquist."""
    if tipo == "A":
        return parametros.get("f0", 5.0)
    if tipo in ("B", "C"):
        return parametros.get("a", 2.0)
    raise ValueError("El audio usa su propia frecuencia de referencia.")


def muestrear_senal(tipo, t_densa, _x_densa, fs, parametros):
    """Muestreo ideal: evalúa x(nTs) directamente, sin depender de la grilla."""
    if fs <= 0:
        raise ValueError("La frecuencia de muestreo debe ser positiva.")
    ts = 1.0 / fs
    n = np.arange(np.ceil(t_densa[0] / ts), np.floor(t_densa[-1] / ts) + 1)
    t_muestras = n * ts
    return t_muestras, generar_senal(tipo, t_muestras, **parametros), ts


def muestrear_audio(audio, fs_original, fs_nueva):
    """Resampling manual por interpolación lineal de la señal discreta."""
    if fs_original <= 0 or fs_nueva <= 0:
        raise ValueError("Las frecuencias de muestreo deben ser positivas.")
    if len(audio) < 2:
        raise ValueError("El audio debe contener al menos dos muestras.")
    duracion = (len(audio) - 1) / fs_original
    n_nuevas = int(np.floor(duracion * fs_nueva)) + 1
    t_nuevo = np.arange(n_nuevas) / fs_nueva
    posicion = np.minimum(t_nuevo * fs_original, len(audio) - 1)
    indice_izq = np.floor(posicion).astype(int)
    indice_der = np.minimum(indice_izq + 1, len(audio) - 1)
    fraccion = posicion - indice_izq
    salida = audio[indice_izq] * (1 - fraccion) + audio[indice_der] * fraccion
    return t_nuevo, salida


def cuantificar_uniforme(x, n_niveles):
    """Cuantificador uniforme mid-rise de N niveles, N potencia entera de dos."""
    valido, mensaje = validar_niveles(n_niveles)
    if not valido:
        raise ValueError(mensaje)
    x = np.asarray(x, dtype=float)
    minimo, maximo = x.min(), x.max()
    if maximo == minimo:
        return np.full_like(x, minimo), 0.0
    delta = (maximo - minimo) / n_niveles
    indice = np.clip(np.floor((x - minimo) / delta), 0, n_niveles - 1)
    return minimo + (indice + 0.5) * delta, delta


def validar_niveles(n_niveles):
    if isinstance(n_niveles, (float, np.floating)) and not n_niveles.is_integer():
        return False, "El número de niveles debe ser un entero."
    try:
        n_niveles = int(n_niveles)
    except (TypeError, ValueError):
        return False, "El número de niveles debe ser un entero."
    if n_niveles < 2 or n_niveles & (n_niveles - 1):
        return False, "El número de niveles debe ser una potencia entera de 2 (2, 4, 8, ...)."
    return True, ""


def reconstruir_senal(t_muestras, x_muestras, ts, t_recon, radio=RADIO_SINC):
    """Reconstrucción sinc truncada y calculada por bloques para audio largo.

    La suma ideal de Whittaker-Shannon es infinita. Se usan las
    ``2*radio+1`` muestras vecinas, aproximación explícita sin crear una
    matriz de tamaño ``len(t_recon) x len(t_muestras)``.
    """
    if ts <= 0:
        raise ValueError("El periodo de muestreo debe ser positivo.")
    t_muestras = np.asarray(t_muestras, dtype=float)
    x_muestras = np.asarray(x_muestras, dtype=float)
    t_recon = np.asarray(t_recon, dtype=float)
    if len(t_muestras) != len(x_muestras) or len(t_muestras) == 0:
        raise ValueError("Las muestras de entrada no son válidas.")
    salida = np.empty(len(t_recon), dtype=float)
    desplazamientos = np.arange(-radio, radio + 1)
    indices_base = np.rint((t_recon - t_muestras[0]) / ts).astype(int)
    for inicio in range(0, len(t_recon), TAMANO_BLOQUE_RECONSTRUCCION):
        fin = min(inicio + TAMANO_BLOQUE_RECONSTRUCCION, len(t_recon))
        indices = indices_base[inicio:fin, None] + desplazamientos[None, :]
        validos = (indices >= 0) & (indices < len(x_muestras))
        indices_seg = np.clip(indices, 0, len(x_muestras) - 1)
        tiempos = t_muestras[indices_seg]
        pesos = sinc_manual((t_recon[inicio:fin, None] - tiempos) / ts) * validos
        salida[inicio:fin] = np.sum(pesos * x_muestras[indices_seg], axis=1)
    return salida


def error_medio_cuadratico(x_referencia, x_estimado):
    n = min(len(x_referencia), len(x_estimado))
    if n == 0:
        raise ValueError("No hay muestras para calcular el MSE.")
    diferencia = np.asarray(x_referencia[:n], dtype=float) - np.asarray(x_estimado[:n], dtype=float)
    return float(np.mean(diferencia ** 2))


def snr_cuantificacion(x_referencia, mse):
    potencia_senal = float(np.mean(np.asarray(x_referencia, dtype=float) ** 2))
    return float("inf") if mse <= 0 else float(10 * np.log10(potencia_senal / mse))


def metricas_cuantificacion(x_muestreada, x_cuantificada):
    """MSE y SNR debidos exclusivamente al cuantificador uniforme."""
    mse = error_medio_cuadratico(x_muestreada, x_cuantificada)
    return mse, snr_cuantificacion(x_muestreada, mse)


def error_espectral(x_original, x_reconstruida):
    """Error relativo L2 entre las magnitudes espectrales de ambas señales."""
    n = min(len(x_original), len(x_reconstruida))
    if n == 0:
        raise ValueError("No hay muestras para calcular el error espectral.")
    X_original = np.abs(np.fft.fft(np.asarray(x_original[:n], dtype=float)))
    X_reconstruida = np.abs(np.fft.fft(np.asarray(x_reconstruida[:n], dtype=float)))
    norma = np.linalg.norm(X_original)
    return 0.0 if norma == 0 else float(np.linalg.norm(X_original - X_reconstruida) / norma)


def espectro(x, fs):
    """Espectro de magnitud bilateral centrado para RF6."""
    x = np.asarray(x, dtype=float)
    X = np.fft.fftshift(np.fft.fft(x))
    frecuencias = np.fft.fftshift(np.fft.fftfreq(len(x), d=1.0 / fs))
    return frecuencias, np.abs(X) / len(x)
