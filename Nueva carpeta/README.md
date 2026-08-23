# Simulación de un Sistema de Digitalización de Señales — Fase I

Universidad del Cauca — Facultad de Ingeniería Electrónica y Telecomunicaciones
Telecomunicaciones Digitales

## Estructura del proyecto

```
proyecto_digitalizacion/
├── signal_utils.py      # Motor de DSP: muestreo, cuantificación, métricas, reconstrucción
├── app.py                # Interfaz gráfica interactiva (Streamlit)
├── generar_tablas.py     # Script para las Tablas 1 y 2 de la sustentación
├── requirements.txt
└── README.md
```

## Instalación

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
streamlit run app.py
```

## Generar las tablas de la sustentación


- **Tabla 1**: MSE y SNR vs niveles de cuantificación (2 a 256), a la frecuencia
  de Nyquist, para la señal C.
- **Tabla 2**: Error espectral vs frecuencia de muestreo (0.25·fs a 2·fs), con
  16 niveles de cuantificación, para la señal D (audio).

```bash
python generar_tablas.py --audio ruta/a/tu_audio.wav
```

Esto genera `tabla1_..._.csv/.png` y `tabla2_..._.csv/.png`, listos para
pegar en el informe o mostrarlos en la sustentación.



| Requerimiento |
|---|---|
| RF1 Interfaz gráfica | `app.py` (Streamlit, sliders y selects reactivos) |
| RF2 Señales sintéticas A–D | `signal_utils.generar_senal`, carga de audio en `app.py` |
| RF3 Muestreo | `signal_utils.muestrear_senal` / `muestrear_audio` (resampling) |
| RF4 Cuantificación | `signal_utils.cuantificar_uniforme` + `validar_niveles` |
| RF5 Métricas | `error_medio_cuadratico`, `snr_cuantificacion`, `error_espectral` |
| RF6 Visualizaciones (6 gráficas) | bloque de `matplotlib` en `app.py` |
| RF7 Cargue de audio | `st.file_uploader` en `app.py` |
| RF8 Reproducción de audio | `st.audio(...)` en `app.py` (original y reconstruido) |
| RNF1 Manejo de errores | `try/except`, `validar_niveles`, mensajes `st.error` |
| RNF2 Sin funciones de alto nivel | Muestreo, cuantificación y reconstrucción (sinc) son implementación propia en `signal_utils.py`. `np.fft` se usa solo como herramienta de análisis para graficar espectros y calcular el error espectral, no reemplaza los bloques del sistema. |
| RNF3 Reproducibilidad | Sin aleatoriedad; misma entrada → mismos resultados siempre |


## Ejecución del código para la Tabla 1 y 2 (resumen para el informe)

Corre `generar_tablas.py`, adjunta las imágenes `.png` generadas y comenta
en el informe/sustentación las tendencias observadas (MSE decreciente y SNR
creciente con más niveles; error espectral creciente al alejarse de `fs`
original en el resampling de audio).
