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


## Ejecutar la aplicación

```bash
python -m streamlit run app.py
```

Se abrirá en el navegador (por defecto `http://localhost:8501`).

## Generar las tablas de la sustentación

Las "CONDICIONES DE ENTREGA" piden dos tablas de resultados:

- **Tabla 1**: MSE y SNR vs niveles de cuantificación (2 a 256), a la frecuencia
  de Nyquist, para la señal C.
- **Tabla 2**: Error espectral vs frecuencia de muestreo (0.25·fs a 2·fs), con
  16 niveles de cuantificación, para la señal D (audio).

```bash
python generar_tablas.py --audio ruta/a/tu_audio.wav
```

Esto genera `tabla1_..._.csv/.png` y `tabla2_..._.csv/.png`, listos para
pegar en el informe o mostrarlos en la sustentación.

> **Nota sobre el audio:** RF2 exige un audio de mínimo 20 s. Debes
> conseguir/grabar tú mismo un archivo `.wav` (mono o estéreo) — el proyecto
> no incluye uno por licenciamiento. Cualquier grabadora de voz del celular
> sirve; exporta a `.wav`.

## Cómo se cumple cada requerimiento

| Requerimiento | Dónde está implementado |
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

## Notas de teoría para preparar la sustentación (50% de la nota)

Como el criterio de mayor peso en la rúbrica es la sustentación, conviene
que puedas explicar —no solo mostrar— lo siguiente:

1. **Teorema de muestreo (Nyquist-Shannon):** por qué `fs ≥ 2·B` evita
   aliasing. En la app, prueba a bajar `fs` por debajo del valor de Nyquist
   sugerido y observa cómo el espectro de la señal muestreada empieza a
   solaparse (aliasing) y el error espectral sube.
2. **Cuantificación uniforme y ruido de cuantificación:** el paso
   `Δ = rango/N`; el ruido de cuantificación se modela como uniforme en
   `[-Δ/2, Δ/2]`, con potencia `Δ²/12`. Por eso el SNR de cuantificación
   sube aproximadamente **6 dB por cada bit adicional** (cada vez que N se
   duplica) — puedes verificarlo con la Tabla 1: entre 2→4 niveles el SNR
   sube ~6 dB, y así sucesivamente, hasta que el error empieza a estar
   dominado por otros efectos (p. ej. el propio muestreo) en niveles muy
   altos.
3. **Reconstrucción ideal (Whittaker–Shannon):** la interpolación con
   función `sinc` es la reconstrucción "ideal" de un tren de impulsos
   muestreado, válida si se cumplió Nyquist. Relaciona esto con por qué el
   filtro reconstructor ideal es un pasa-bajas con respuesta `sinc` en el
   tiempo.
4. **Relación entre dominio del tiempo y frecuencia:** por qué muestrear en
   el tiempo genera réplicas periódicas del espectro (convolución con un
   tren de impulsos en frecuencia) — esto es justo lo que se ve al comparar
   las gráficas b) y d) de la app.
5. **Resampling y recuantificación de audio:** por qué cambiar `fs` de un
   audio ya digital requiere interpolar (no es lo mismo que "muestrear" una
   señal continua), y qué distorsión introduce hacerlo con muy pocos
   niveles o una `fs` muy por debajo de la original.

## Ejecución del código para la Tabla 1 y 2 (resumen para el informe)

Corre `generar_tablas.py`, adjunta las imágenes `.png` generadas y comenta
en el informe/sustentación las tendencias observadas (MSE decreciente y SNR
creciente con más niveles; error espectral creciente al alejarse de `fs`
original en el resampling de audio).
