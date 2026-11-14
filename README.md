# ENTROPY ORACLE

Prototipo de investigación funcional para estimación adversarial de predictibilidad. Implementa **14 predictores**, **10 fuentes controladas**, selección temporal, ensemble probabilístico, intervalos con dependencia temporal, benchmarks reproducibles y una interfaz Streamlit. **No certifica una cota inferior de min-entropía y no es una implementación normativa SP 800-90B/AIS 31.**

## Ejecutar

Python 3.10 o posterior. Entorno probado: Python 3.12, PyTorch CPU. Desde este directorio:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python benchmark.py --source nonlinear --models all
streamlit run app.py
```

En el entorno entregado ya existe `.venv`: basta activarlo. La interfaz abre en `http://localhost:8501`. Para GPU, instalar la distribución PyTorch adecuada al dispositivo; los modelos la detectan automáticamente. Los resultados entregados se produjeron en **CPU**. Semillas reproducibles no implican identidad numérica entre versiones de bibliotecas o dispositivos.

```bash
python -m pytest -q
bash scripts/run_suite.sh
python scripts/summarize.py
```

`run_suite.sh` reproduce los tres experimentos, tres semillas por experimento y las curvas de aprendizaje. Es secuencial para que los tiempos sean más fáciles de interpretar. Los tiempos de los artefactos originales incluyen algunas ejecuciones concurrentes. `requirements-tested.txt` registra las versiones directas utilizadas; la versión CPU de Torch se instala desde el índice indicado arriba.

## Resultados reales incluidos

Cada fila siguiente es la media de las semillas **11, 29 y 47**; no es un intervalo de confianza. Los valores proceden de [results/summary.csv](results/summary.csv), generado exclusivamente a partir de los JSON guardados.

| Fuente | Predictor | Acierto test | Log-loss bits |
|---|---|---:|---:|
| No lineal, n=12.000 | Marginal | 24,94 % | 2,0003 |
| No lineal | Markov-5 | 26,89 % | 2,3185 |
| No lineal | Random Forest | 47,72 % | 1,3568 |
| No lineal | GRU | 47,47 % | 1,2596 |
| No lineal | Transformer | 47,72 % | 1,2461 |
| No lineal | Conditional spline flow | 47,29 % | 1,2621 |
| No lineal | Ensemble | 47,46 % | 1,2271 |
| Bernoulli IID p=0,8, n=1.600 | Marginal | 80,42 % | 0,7134 |
| Bernoulli IID | Transformer | 80,42 % | 0,7327 |
| Bernoulli IID | MLP | 73,96 % | 1,7130 |
| AR(1) cuantizado, n=12.000 | Markov-2 | 70,04 % | 1,1198 |
| AR(1) cuantizado | GRU | 68,06 % | 1,2045 |
| AR(1) cuantizado | Transformer | 67,97 % | 1,2136 |
| AR(1) cuantizado | Conditional spline flow | 69,43 % | 1,1506 |

La fuente no lineal tiene **marginal exactamente uniforme en su ley** sobre cuatro símbolos y éxito óptimo dado el pasado de **0,485**. No se fuerza el balance de la muestra. Un nuevo bit justo y un multiplexor ruidoso de bits observados con retardos 9, 13 y 17 forman cada símbolo. Su min-entropía marginal es 2 bits, su average conditional min-entropy es 1,043943 bits y su tasa de entropía de Shannon es 1,194392 bits. Estas son propiedades analíticas de esta fuente controlada.

Markov de orden 4–5 tiene una referencia de éxito óptimo **0,305225**, no 0,25: algunos bits antiguos se comparten. La derivación y una verificación por enumeración exacta están en [docs/nonlinear_reference.md](docs/nonlinear_reference.md). El rendimiento observado inferior de Markov-5 refleja también la escasez de conteos.

En el contraste Transformer menos Markov-5, las mejoras observadas fueron **20,83, 22,88 y 18,79 puntos porcentuales**. Las cotas inferiores simultáneas fueron **13,83, 15,87 y 11,79 puntos**, con cobertura familiar al menos 95 % para nueve contrastes: tres políticas —seleccionado, ensemble y Transformer— por tres semillas. Son cotas martingala de la diferencia media condicional en la trayectoria evaluada, no garantías sobre sesiones futuras. Véase [results/simultaneous_comparisons.json](results/simultaneous_comparisons.json).

Los modelos complejos aportan capacidad frente a contextos cortos, pero estos datos **no demuestran que la atención, recurrencia o flows sean indispensables**: boosting y RF también resuelven el experimento. El caso IID y el AR(1) muestran cuándo una solución sencilla es mejor en coste y/o log-loss. La MLP de presupuesto fijo sobreajusta y no tiene restauración por validación, de modo que su fallo no demuestra inferioridad intrínseca de las MLP.

## Implementado, entrenado y evaluado

Todos estos predictores fueron implementados, entrenados en las tres fuentes principales y evaluados en sus tests temporales finales, para las tres semillas:

| Identificador | Implementación | Selección / límites |
|---|---|---|
| `marginal` | Frecuencias con suavizado | Ajuste solo en train |
| `markov1`…`markov5` | Conteos de contexto, suavizado y fallback | Órdenes fijos |
| `ppm` | PPM interpolado Witten–Bell, profundidad hasta 12 | Sin exclusión; no normativa |
| `lz78` | Trie de frases LZ78, predictor inspirado en compresión | Congelado; no LZ78Y normativo ni codec de referencia |
| `gb` | Histogram Gradient Boosting | 100 iteraciones fijas |
| `rf` | Random Forest | 100 árboles, un hilo |
| `mlp` | MLP sobre ventanas, one-hot multiclase | Hasta 65 épocas; sin checkpoint de validación |
| `gru` | GRU pequeña + readout temporal MLP | Checkpoint por log-loss de validación |
| `transformer` | Atención causal pequeña + posiciones + readout MLP | Checkpoint por log-loss de validación |
| `flow` | Conditional rational-quadratic spline flow | Masas exactas por diferencias de CDF; checkpoint por validación |

`selected` aplica el predictor con mayor accuracy de validación, desempate por log-loss. `ensemble` ajusta pesos convexos para minimizar log-loss de validación. Ambos quedan fijados antes de evaluar test. El orden de presentación de las métricas de test no influye en estas decisiones. Los tiempos cero de estas dos filas indican reutilización de las probabilidades ya calculadas; no son el coste total de desplegar la política.

El flow es un modelo escalar condicional genuinamente invertible con base logística y spline racional cuadrática. Se integra sobre bins, incluidos extremos infinitos. **No se utiliza una densidad puntual como probabilidad discreta.** La implementación independiente no necesita `nflows`. MAF multidimensional, LSTM y flujos discretos no se implementaron; se eligieron GRU y spline condicional por viabilidad. El floor numérico de masas y la no identificabilidad de la densidad dentro de cada bin se documentan en [docs/flow.md](docs/flow.md).

Los 10 generadores tienen pruebas de reproducibilidad, alfabeto y referencias: Bernoulli, Markov binaria, Markov superior, dependencia periódica, HMM, AR(1) gaussiano cuantizado, arcsine con ruido gaussiano, drift, dependencia de largo alcance y no lineal. Los oráculos condicionan solo sobre observaciones pasadas, salvo referencias privilegiadas expresamente separadas. En AR(1) cuantizado no se afirma disponer del oráculo exacto: la referencia con estado continuo previo es privilegiada y numérica. La convolución arcsine usa cuadratura documentada, no una expresión analítica falsa.

## Protocolo e interpretación

- Split cronológico **60 % train / 20 % validación / 20 % test**, ventana por defecto 32. Los primeros 32 símbolos solo forman contexto.
- Ventanas `X[t-window:t]`; nunca contienen el target. Sí pueden contener símbolos anteriores del test, observables al predecir el siguiente. No hay actualización de pesos ni de conteos en test.
- La validación selecciona checkpoints, predictor y pesos del ensemble. Sus estadísticas no constituyen validación independiente de esas elecciones.
- Accuracy es la proporción de aciertos de `argmax q`; `mean(max q)` es confianza del modelo y se reporta separadamente. Log-loss en bits y Brier evalúan probabilidades.
- Intervalos principales: Hoeffding condicional de horizonte fijo, válidos con dependencia para la media realizada de probabilidades condicionales de éxito. Bootstrap circular de bloques: diagnóstico exploratorio que requiere estacionariedad y mezcla; no válido en general para drift.
- Las cotas inferiores del éxito de un predictor pueden dar **cotas superiores** sobre la min-entropía condicional promedio pertinente. No producen cotas inferiores conservadoras de la entropía real.
- Tiempo medido con reloj monótono; memoria RSS del proceso muestreada durante ajuste e inferencia, no memoria aislada de cada modelo. No había GPU disponible.
- Hiperparámetros, capacidad y contexto difieren; el Transformer/GRU usa readout MLP sobre todos los estados de la ventana. No se atribuye causalmente la mejora a atención o recurrencia sin ablaciones.

[docs/mathematics.md](docs/mathematics.md) desarrolla las distinciones entre min-entropía marginal, condicional puntual, peor contexto, average conditional min-entropy, tasas de Shannon/min-entropía de bloques, cross-entropy, log-loss y guessing probability. Incluye derivaciones de las cotas y límites de la relación con SP 800-90B.

## Uso experimental

```bash
# Configurar una fuente y escoger modelos
python benchmark.py --source markov --models marginal,markov1,gru,flow \
  --n 20000 --seeds 11,29,47 --params '{"p01":0.02,"p10":0.02}'

# Curvas exploratorias: mismos segmentos de validación/test, train de tamaño creciente
python benchmark.py --source nonlinear --models marginal,markov5,gru,transformer,flow \
  --n 12000 --seed 101 --learning-sizes 500,1500,4000,7000 --output results/learning

# Exportar una secuencia para otro estimador (un byte por símbolo)
python scripts/export_source.py --source nonlinear --n 1000000 --seed 11 --out data/nonlinear.bin
```

La exportación no ejecuta ni valida una herramienta normativa. Las comparaciones SP 800-90B requieren la implementación y las condiciones de uso correspondientes. Cambiar modelos tras mirar el test convierte ese test en exploratorio; se necesitan nuevas semillas o muestras reservadas para una confirmación posterior.

## Archivos

- `entropy_oracle/`: generadores, modelos, estadísticas y ejecución.
- `tests/`: pruebas matemáticas, probabilísticas, causales, de integración y de UI con entrenamiento real.
- `results/main/`, `results/iid/`, `results/ar1/`: nueve ejecuciones principales; cada JSON incluye configuración, versiones, métricas, selección, historia y primeras 1.024 probabilidades de test.
- `results/learning/`: cuatro tamaños de entrenamiento con semilla 101 separada.
- [results/REPORT.md](results/REPORT.md), `summary.csv`, `metrics.csv`: resultados completos, regenerables.
- `results/accuracy_mean.html`, `results/log_loss_bits_mean.html`: gráficas interactivas autónomas, sin servicio externo.
- `app.py`: selección de fuentes/parámetros/modelos, entrenamiento local, carga de resultados, errores, probabilidades, referencias y curvas.

Las probabilidades de la traza guardada son un subconjunto de visualización; las métricas usan todo el test. Los resultados completos se reproducen con sus configuraciones y semillas. El repositorio no contiene datos ficticios ni resultados sustituidos por simulaciones de entrenamiento.
