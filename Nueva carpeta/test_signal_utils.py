"""Pruebas básicas de los bloques exigidos en la Fase I."""

import numpy as np

import signal_utils as su


def test_validacion_de_potencias_de_dos():
    assert su.validar_niveles(2)[0]
    assert su.validar_niveles(256)[0]
    assert not su.validar_niveles(3)[0]
    assert not su.validar_niveles(2.5)[0]


def test_el_mse_de_cuantificacion_disminuye_con_mas_niveles():
    x = np.linspace(-1, 1, 1_001)
    x4, _ = su.cuantificar_uniforme(x, 4)
    x64, _ = su.cuantificar_uniforme(x, 64)
    assert su.error_medio_cuadratico(x, x64) < su.error_medio_cuadratico(x, x4)


def test_reconstruccion_en_rejilla_de_muestreo():
    t = np.arange(100) / 100
    x = su.senal_a(t, f0=5)
    reconstruida = su.reconstruir_senal(t, x, 0.01, t)
    assert np.allclose(reconstruida, x, atol=1e-10)


def test_error_espectral_es_cero_para_senales_iguales():
    x = np.sin(np.linspace(0, 2 * np.pi, 100))
    assert su.error_espectral(x, x) == 0
