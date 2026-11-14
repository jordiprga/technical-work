# ENTROPY ORACLE

Prototipo de investigación para estimación adversarial de predictibilidad de fuentes discretas. La versión **0.2.0** implementa **14 predictores**, **10 fuentes controladas**, entrada de datos reales, selección temporal, ensemble probabilístico, cotas con dependencia temporal, archivos completos de predicciones y una interfaz Streamlit. **No certifica una cota inferior de min-entropía y no es una implementación normativa de SP 800-90B/AIS 31.**

## Instalación y ejecución

Python 3.10 o posterior. Entorno probado: Python 3.12 y PyTorch CPU. Desde este directorio:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'torch>=2.2' --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e '.[ui,dev]'
python benchmark.py --source nonlinear --models all
streamlit run app.py
```

`python -m pip install -r requirements.txt` instala los mismos extras. En el entorno entregado ya existe `.venv`. La interfaz abre en `http://localhost:8501`; permite configurar fuentes, importar observaciones, seleccionar y entrenar modelos, comparar métricas y explorar historiales, probabilidades y errores.

La instalación añade un comando utilizable fuera del directorio del proyecto:

```bash
entropy-oracle --source nonlinear --models all
python -m entropy_oracle.cli --source nonlinear --models marginal,markov5,transformer
```

`benchmark.py` es un wrapper de la misma CLI. Para GPU, instalar la distribución PyTorch adecuada al dispositivo; los modelos la detectan automáticamente. Los resultados incluidos se produjeron en **CPU**. Semillas explícitas no garantizan identidad numérica entre bibliotecas o dispositivos; CUDA solicita algoritmos deterministas con advertencias, sin prometer determinismo bit a bit.

## Verificación y reproducción

```bash
python -m pytest -q
bash scripts/run_suite.sh
python scripts/summarize.py
python scripts/verify_results.py results/v2 --require-audit
```

La suite cubre generadores, fórmulas probabilísticas, normalización, causalidad, selección temporal, carga de datos, archivos de auditoría, CLI y flujos de la interfaz con entrenamiento real. `run_suite.sh` reproduce los tres experimentos principales con semillas **211, 229 y 247** y curvas de aprendizaje separadas con semilla **201**. El script de resumen genera tablas, gráficos y comparaciones simultáneas a partir de los JSON guardados. `requirements-tested.txt` registra versiones directas del entorno; cada ejecución guarda también versiones y hashes del código.

Los tiempos varían con la carga de CPU. Algunas ejecuciones entregadas se realizaron concurrentemente; el script de reproducción es secuencial. La memoria registrada es RSS del proceso muestreada durante entrenamiento e inferencia, no memoria aislada por modelo ni una medida exacta del pico.

El workflow [`.github/workflows/tests.yml`](.github/workflows/tests.yml) configura pruebas en Python 3.11 y 3.12, instalación PyTorch CPU y una ejecución de la CLI. **Está configurado, pero no se afirma haber ejecutado CI remoto ni disponer de un repositorio GitHub publicado.**

## Resultados reales de v0.2.0

Las filas son medias de tres semillas, **211, 229 y 247**; no son intervalos de confianza. Proceden de los artefactos completos en [`results/v2/`](results/v2/), resumidos en [REPORT.md](results/v2/REPORT.md) y [summary.csv](results/v2/summary.csv).

| Fuente | Predictor | Acierto test | Log-loss bits |
|---|---|---:|---:|
| No lineal, n=12.000 | Marginal | 24,68 % | 2,0003 |
| No lineal | Markov-5 | 27,51 % | 2,3051 |
| No lineal | Gradient Boosting | 49,18 % | 1,2454 |
| No lineal | Random Forest | 49,03 % | 1,3502 |
| No lineal | MLP | 47,88 % | 1,3140 |
| No lineal | GRU | 48,76 % | 1,2498 |
| No lineal | Transformer | 48,17 % | 1,2629 |
| No lineal | Conditional spline flow | 47,11 % | 1,2561 |
| No lineal | Ensemble | 48,44 % | 1,2258 |
| Bernoulli IID p=0,8, n=1.600 | Marginal | 81,77 % | 0,6881 |
| Bernoulli IID | MLP | 81,77 % | 0,7069 |
| Bernoulli IID | Transformer | 81,77 % | 0,7061 |
| AR(1) cuantizado, n=12.000 | Markov-2 | 70,00 % | 1,1191 |
| AR(1) cuantizado | GRU | 68,79 % | 1,1942 |
| AR(1) cuantizado | Transformer | 67,60 % | 1,2247 |
| AR(1) cuantizado | Conditional spline flow | 69,69 % | 1,1476 |

La fuente no lineal tiene **marginal exactamente uniforme en su ley** sobre cuatro símbolos y, tras la inicialización, probabilidad óptima de acierto dado todo el pasado de **0,485**. No se fuerza el balance de la muestra. Un nuevo bit justo y un multiplexor ruidoso de bits observados con retardos 9, 13 y 17 forman cada símbolo. Su min-entropía marginal es 2 bits, su average conditional min-entropy tras la inicialización es 1,043943 bits y su tasa de entropía de Shannon es 1,194392 bits. Son propiedades analíticas de esta fuente controlada. Un acierto empírico por encima de 0,485 en un test finito es fluctuación muestral, no superación del óptimo de Bayes.

Markov de orden 4–5 tiene una referencia de éxito óptimo **0,305225**, no 0,25: algunos bits antiguos se comparten. La derivación y su enumeración exacta están en [docs/nonlinear_reference.md](docs/nonlinear_reference.md). El rendimiento inferior del Markov-5 ajustado refleja también escasez de conteos.

Los nueve contrastes preespecificados de la fuente no lineal —seleccionado, ensemble y Transformer frente a Markov-5, en tres semillas— tienen cotas inferiores simultáneas positivas. [simultaneous_comparisons.json](results/v2/simultaneous_comparisons.json) aplica Bonferroni sobre los nueve contrastes para cobertura familiar al menos 95 %. Las cotas martingala corresponden a la diferencia media condicional en las trayectorias evaluadas; no garantizan rendimiento en sesiones futuras.

Los modelos con acceso a ventanas largas explotan dependencias que los contextos cortos representan mal. **No se demuestra que atención, recurrencia o flows sean indispensables ni superiores a todos los métodos clásicos**: boosting y RF también resuelven el caso. El IID muestra una ventaja descriptiva de log-loss del predictor marginal a igual accuracy; en AR(1), Markov-2 supera en promedio a los tres modelos avanzados. Esas diferencias de log-loss no se presentan como contrastes confirmatorios.

Los resultados iniciales de v0.1.0 permanecen en sus ubicaciones históricas y en el commit `bd7e077`. Utilizaron semillas 11, 29 y 47 y una MLP sin checkpoint temporal. Las nuevas ejecuciones cambian semillas y protocolo; las diferencias entre versiones **no identifican por sí solas el efecto causal de un cambio de implementación**.

## Implementado, entrenado y evaluado

Los 14 predictores siguientes fueron implementados, entrenados y evaluados en los tests temporales finales de las tres fuentes principales y sus tres semillas de v0.2.0. [model_status.json](results/v2/model_status.json) enumera el estado derivado de los artefactos.

| Identificador | Implementación | Selección / límites |
|---|---|---|
| `marginal` | Frecuencias con suavizado | Ajuste solo en train |
| `markov1`…`markov5` | Conteos de contexto, suavizado y fallback | Órdenes fijos |
| `ppm` | PPM interpolado Witten–Bell, profundidad hasta 12 | Sin exclusión; no normativa |
| `lz78` | Trie de frases LZ78, predictor inspirado en compresión | Congelado; no LZ78Y normativo ni codec de referencia |
| `gb` | Histogram Gradient Boosting | 100 iteraciones fijas |
| `rf` | Random Forest | 100 árboles, un hilo |
| `mlp` | MLP sobre ventanas, one-hot multiclase | Hasta 65 épocas, early stopping y mejor checkpoint por log-loss de validación |
| `gru` | GRU pequeña + readout temporal MLP | Mejor checkpoint por log-loss de validación |
| `transformer` | Atención causal pequeña + posiciones + readout MLP | Mejor checkpoint por log-loss de validación |
| `flow` | Conditional rational-quadratic spline flow | Masas por diferencias de CDF; mejor checkpoint por validación |

`selected` aplica el predictor con mayor accuracy de validación, con desempate por log-loss. `ensemble` ajusta pesos convexos para minimizar log-loss de validación. La ejecución tiene dos etapas explícitas: primero entrena todos los candidatos y fija checkpoints, selección y pesos; después abre el test final. Ninguna métrica de test interviene en esas elecciones. En v0.2, `fit_seconds` de `selected` y `ensemble` suma los ajustes de todos los candidatos y la selección de la política; `predict_seconds` refleja los componentes de inferencia de la política desplegada. La inferencia de validación figura por separado en cada candidato. Estos campos no son el tiempo total de pared de toda la ejecución.

La MLP usa ahora validación temporal para detener el entrenamiento y restaurar el mejor checkpoint; las etiquetas de validación nunca entran en sus actualizaciones Adam. Hiperparámetros, capacidad y presupuestos siguen siendo distintos entre familias. GRU y Transformer usan un readout MLP sobre todos los estados de la ventana: atribuir la mejora exclusivamente a recurrencia o atención requeriría ablaciones adicionales.

El flow es escalar y condicional, con transformación invertible, base logística y spline racional cuadrática. Integra masas sobre bins, incluidos extremos infinitos. **No evalúa una densidad puntual como probabilidad discreta.** La implementación independiente no necesita `nflows`. MAF multidimensional, LSTM y flujos discretos no se implementaron; se eligieron GRU y spline condicional. El suelo numérico de masas y la no identificabilidad de la densidad dentro de cada bin se describen en [docs/flow.md](docs/flow.md).

Los 10 generadores tienen pruebas de reproducibilidad, alfabeto y referencias: Bernoulli, Markov binaria, Markov superior, dependencia periódica, HMM, AR(1) gaussiano cuantizado, arcsine con ruido gaussiano, drift, dependencia de largo alcance y no lineal. Los oráculos usan observaciones pasadas, salvo referencias privilegiadas expresamente separadas. Para AR(1) cuantizado no se afirma disponer del oráculo exacto: la referencia con estado continuo previo es privilegiada y numérica. La convolución arcsine usa cuadratura documentada. Véase [docs/sources.md](docs/sources.md).

## Evaluar observaciones reales

La secuencia debe estar discretizada previamente y mantener su orden de adquisición. El alfabeto **debe declararse explícitamente**; no se infiere del máximo observado ni se remapean símbolos.

```bash
# Un símbolo uint8 por byte; alfabeto declarado de 256 símbolos
entropy-oracle --input data/capture.bin --alphabet-size 256 --dtype uint8 \
  --models marginal,markov1,markov2,flow

# Enteros little-endian de 16 bits; 16 símbolos posibles
python benchmark.py --input data/capture16.bin --alphabet-size 16 --dtype uint16le \
  --models marginal,markov1,gru

# Matriz NumPy o una columna de texto/CSV; --dtype solo afecta a binarios
entropy-oracle --input data/capture.npy --alphabet-size 4 --models all
```

Formatos: `.bin` con `uint8`, `uint16le` o `uint32le`; `.npy` numérico sin pickle; `.csv`/`.txt` de una secuencia de enteros. Se rechazan valores fuera del alfabeto, fracciones, NaN, infinitos y estructuras ambiguas. Los detalles y límites de lectura están en [docs/data.md](docs/data.md).

`--input` sustituye la fuente sintética y utiliza la longitud real del archivo: **`--n` se ignora en este modo**. No se proporciona un oráculo teórico para observaciones importadas. Varias semillas repiten el ajuste de modelos sobre **la misma secuencia**; no crean réplicas independientes de la fuente.

El output predeterminado de datos externos es `local-results/`, excluido de Git junto con `data/`. `--output RUTA` lo cambia explícitamente. Los archivos de auditoría contienen etiquetas reales de test y probabilidades: su guardado local no implica publicación. Se registra el basename y el SHA-256 de los bytes originales, sin la ruta absoluta.

El lector admite por defecto archivos de hasta 64 MiB. El ejecutor limita el alfabeto a **4096 símbolos** y rechaza estimaciones de asignación densa superiores a **2 GiB**; son controles preventivos, no garantías sobre el pico real de memoria. No se reduce ni recodifica el alfabeto para superar esos límites.

## Protocolo e interpretación

- Split cronológico **60 % train / 20 % validación / 20 % test**, ventana predeterminada 32. Los primeros 32 símbolos forman contexto.
- Ventanas `X[t-window:t]`, sin incluir el target. Pueden contener símbolos anteriores del test, observables al predecir el siguiente. No se actualizan parámetros ni conteos en test.
- La validación selecciona checkpoints, predictor y pesos. Sus estadísticas no son validación independiente de esas elecciones.
- Accuracy mide aciertos de `argmax q`; `mean(max q)` mide confianza declarada del modelo y se reporta aparte. Log-loss en bits y Brier puntúan las probabilidades.
- Las cotas principales usan Hoeffding condicional a horizonte fijo y admiten dependencia temporal para la media realizada de probabilidades condicionales de éxito.
- Bootstrap circular de bloques: diagnóstico exploratorio que requiere estacionariedad y mezcla. Se **desactiva cuando la estacionariedad de la fuente es falsa o desconocida**, incluidos drift, inicialización no estacionaria declarada y archivos importados. Declarar una fuente estacionaria tampoco demuestra mezcla suficiente de los errores del predictor.
- Una cota inferior del éxito de un predictor puede inducir una **cota superior** de la min-entropía condicional promedio pertinente. No proporciona una cota inferior conservadora de la entropía real.

[docs/mathematics.md](docs/mathematics.md) distingue min-entropía marginal, condicional puntual, peor contexto, average conditional min-entropy, tasas de Shannon/min-entropía de bloques, cross-entropy, log-loss y guessing probability. Incluye derivaciones y límites de la relación con SP 800-90B.

## Archivos completos y auditoría

Cada ejecución v0.2.0 guarda un JSON de resultados y un archivo `.predictions.npz` con **todos** los targets, índices y vectores de probabilidades de test. El JSON contiene configuración, versiones, hashes del código y de las observaciones, selección, historiales, métricas y una traza parcial para visualización. La traza no sustituye al archivo completo.

```bash
# Recalcular accuracy, log-loss y Brier; comprobar hash, modelos, índices y traza
python scripts/verify_results.py results/v2 --require-audit

# Auditar un resultado local importado
python scripts/verify_results.py local-results/file_seed11_n12000.json --require-audit
```

La verificación comprueba la consistencia de las predicciones guardadas con las métricas. No demuestra por sí sola ausencia de fuga, autenticidad de la fuente ni min-entropía. Los NPZ se leen con `allow_pickle=False`. El formato y su alcance se describen en [docs/artifacts.md](docs/artifacts.md).

Los JSON históricos de v0.1.0 solo guardaban las primeras 1024 predicciones para visualización; el verificador los identifica como legacy y no simula una auditoría de las observaciones omitidas.

## Otros experimentos

```bash
# Parámetros de una fuente y subconjunto de modelos
entropy-oracle --source markov --models marginal,markov1,gru,flow \
  --n 20000 --seeds 211,229,247 --params '{"p01":0.02,"p10":0.02}'

# Curvas exploratorias: segmentos fijos de validación/test y train creciente
entropy-oracle --source nonlinear --models marginal,markov5,gb,mlp,gru,transformer,flow \
  --n 12000 --seed 201 --learning-sizes 500,1500,4000,7000 --output results/v2/learning

# Exportación de una fuente sintética, un byte por símbolo
python scripts/export_source.py --source nonlinear --n 1000000 --seed 211 --out data/nonlinear.bin
```

Las curvas con validación/test compartidos son exploratorias. Cambiar modelos tras consultar el test exige nuevas muestras reservadas para otra confirmación. Exportar una secuencia no ejecuta ni valida una herramienta normativa; las comparaciones con SP 800-90B requieren su implementación y condiciones de uso.

## Organización

- `entropy_oracle/`: generadores, entrada de datos, modelos, estadísticas, ejecución, auditoría y CLI.
- `tests/`: pruebas matemáticas, de causalidad, archivos, integración e interfaz.
- `results/v2/main/`, `results/v2/iid/`, `results/v2/ar1/`: nueve ejecuciones principales con JSON y NPZ completos.
- `results/v2/learning/`: curvas con semilla 201, separadas de las semillas principales.
- `results/v2/REPORT.md`, `summary.csv`, `metrics.csv`, `model_status.json`: informe y tablas derivados de resultados reales.
- `results/v2/accuracy_mean.html`, `results/v2/log_loss_bits_mean.html`: gráficos autónomos.
- `results/main/`, `results/iid/`, `results/ar1/`, `results/learning/`: artefactos iniciales conservados.
- `app.py`: interfaz local Streamlit; [`CHANGELOG.md`](CHANGELOG.md): cambios por versión.
