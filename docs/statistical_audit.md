# Auditoría estadística de los experimentos principales

Revisión realizada sobre `entropy_oracle/experiment.py`, `statistics.py` y los
tres resultados de `results/main/nonlinear_seed{11,29,47}_n12000.json`.
Esta auditoría verifica el procedimiento computacional e inferencial; no es una
certificación criptográfica de la fuente.

## Protocolo verificado

- Cada realización tiene 12 000 símbolos; la ventana contiene 32 observaciones
  anteriores. Train tiene 7 168 objetivos, validación 2 400 y test final 2 400.
  Los objetivos de test son los índices 9 600–11 999, inclusivos.
- La construcción de ventanas usa `x[t-window:t]`, nunca `x[t]` ni su futuro.
  El pasado ya observado del test es información permitida para el siguiente
  pronóstico, sin reentrenar pesos ni conteos.
- El ganador `selected` se elige mediante precisión de validación y desempate
  por log-loss de validación. El ensemble ajusta pesos convexos mediante
  log-loss de validación. Los números de test no entran en esas funciones.
- Se fijan tres contrastes por realización: `selected`, `ensemble` y
  `transformer`, cada uno frente a `markov5`. Los intervalos guardados en JSON
  usan `alpha=0.05/3`, controlando por Bonferroni una familia de tres contrastes
  dentro de cada realización.
- Las barras de precisión de cada fila, por separado, tienen cobertura
  individual del 95%; no son una familia simultánea que cubra todos los modelos.
- La semilla de desarrollo 1001 es distinta de las tres realizaciones finales.
  Se exploró el entrenamiento neuronal mediante validación; se inspeccionó un
  resultado de test de desarrollo del flow sin cambiar su configuración por ese
  resultado. Esa realización de desarrollo no se presenta como test
  confirmatorio. Los resultados finales requieren que no se hayan reajustado
  modelos o decisiones tras inspeccionar las semillas 11, 29 y 47.

No se encontró un error crítico de alineamiento temporal o selección mediante
test en el código revisado. La selección se computa después de construir las
tablas de test en el orden de ejecución, pero su función solo recibe los
pronósticos y etiquetas de validación. La ausencia de dependencia de datos de
test en esa función es lo que determina su validez.

## Corrección simultánea entre las tres realizaciones

Para formular una afirmación conjunta sobre los tres contrastes en las tres
semillas, la familia contiene nueve comparaciones. La cota de martingala pareada
con \(D_t\in[-1,1]\), \(n=2400\) y \(\alpha_i=0.05/9\) tiene radio

\[
r=\sqrt{\frac{2\ln(2\cdot9/0.05)}{2400}}
=0.0700363240959656.
\]

Cada intervalo individual tiene cobertura al menos 99.4444%; por la unión de
eventos, los nueve simultáneamente tienen cobertura al menos 95%. Bonferroni no
requiere independencia entre los contrastes o entre las semillas. El objetivo
es el promedio de las diferencias de probabilidades condicionales de éxito a lo
largo de cada trayectoria de test, definido en `mathematics.md`; no es la
precisión de una sesión futura arbitraria.

Los números siguientes son **puntos porcentuales** de diferencia de acierto
frente a Markov de orden 5. Los intervalos se recalculan para la familia de nueve;
son deliberadamente más amplios que los almacenados originalmente para familias
de tres.

| Semilla | Predictor | Diferencia observada | Intervalo simultáneo, familia al 95% |
|---:|:---|---:|:---|
| 11 | Selección por validación | +19.9167 | [+12.9130, +26.9203] |
| 11 | Ensemble probabilístico | +20.7917 | [+13.7880, +27.7953] |
| 11 | Transformer | +20.8333 | [+13.8297, +27.8370] |
| 29 | Selección por validación | +22.8750 | [+15.8714, +29.8786] |
| 29 | Ensemble probabilístico | +21.4167 | [+14.4130, +28.4203] |
| 29 | Transformer | +22.8750 | [+15.8714, +29.8786] |
| 47 | Selección por validación | +19.6250 | [+12.6214, +26.6286] |
| 47 | Ensemble probabilístico | +19.5000 | [+12.4964, +26.5036] |
| 47 | Transformer | +18.7917 | [+11.7880, +25.7953] |

Todos los extremos inferiores son positivos. La mejora del Transformer frente a
Markov 5 sigue siendo defendible incluso con este control familiar más amplio.
Si se incorporan afirmaciones confirmatorias sobre otras fuentes, tamaños,
hiperparámetros o modelos elegidos tras inspeccionar test, esa familia también
debe ampliarse; esta corrección de nueve no cubre todos los experimentos posibles
del repositorio.

## Resultados descriptivos entre semillas

La media y desviación estándar muestral siguientes resumen tres realizaciones.
El signo ± representa **una desviación estándar entre semillas**, no un
intervalo de confianza. No se usa una aproximación normal con tres puntos para
justificar las afirmaciones anteriores.

| Modelo | Acierto medio ± DE (%) | Log-loss medio (bits/símbolo) |
|:---|---:|---:|
| Marginal | 24.944 ± 1.009 | 2.00028 |
| Markov 4 | 28.597 ± 0.610 | 2.05249 |
| Markov 5 | 26.889 ± 0.277 | 2.31850 |
| Gradient Boosting | 47.236 ± 0.963 | 1.25511 |
| Random Forest | 47.722 ± 1.039 | 1.35679 |
| MLP | 46.708 ± 1.078 | 5.21095 |
| GRU | 47.472 ± 0.385 | 1.25958 |
| Transformer | 47.722 ± 2.081 | 1.24612 |
| Flow | 47.292 ± 1.242 | 1.26208 |
| Selección por validación | 47.694 ± 1.718 | 1.25548 |
| Ensemble probabilístico | 47.458 ± 1.086 | 1.22713 |

La precisión óptima teórica de esta fuente, con su historia observada completa,
es 48.5%. El argmax del oráculo obtuvo 48.931% en promedio en estas tres muestras;
una realización puede superar el valor esperado por fluctuación aleatoria, sin
superar al oráculo en probabilidad real de éxito.

La distribución marginal teórica de los cuatro símbolos es exactamente uniforme.
Las frecuencias realizadas no se han equilibrado artificialmente; varían entre
24.5% y 25.5083% en las tres secuencias completas. Se analiza una ley de
probabilidad uniforme, no una imposición de conteos idénticos.

Los resultados descriptivos muestran que los modelos neuronales y el flow
explotan una dependencia que los contextos cortos capturan mal. Los contrastes
con control familiar explicitados aquí corresponden al Transformer, la selección
y el ensemble frente a Markov 5. **No demuestran una ventaja
predictiva del Transformer o del flow sobre Gradient Boosting o Random Forest**:
esos modelos también capturan la dependencia. Tampoco aíslan el valor causal de
la atención frente al readout denso de la arquitectura; eso requeriría
ablaciones. El mal log-loss del MLP, pese a una precisión elevada, ilustra el
coste de probabilidades demasiado confiadas y confirma que ambas métricas no
son intercambiables.

## Bootstrap, memorización y alcance criptográfico

Las afirmaciones de mejora de esta auditoría utilizan la cota de martingala, no
el bootstrap. Este último exige hipótesis adicionales sobre el proceso de
aciertos y una elección adecuada de bloques; el código lo etiqueta como
exploratorio. Aunque la regla no lineal se estabiliza después de la inicialización,
el generador documenta explícitamente un prefijo de inicialización no
estacionario. Las cotas de martingala no requieren borrar ese hecho.

El entrenamiento, la inspección de curvas y los benchmarks adicionales pueden
servir para investigación, pero deben distinguirse del contraste final fijado.
Reutilizar estos mismos tests para decidir una nueva arquitectura convertiría
la siguiente comparación en exploratoria. La evidencia de aciertos del
predictor limita **por arriba**, no por abajo, la min-entropía condicional
promedio correspondiente, con las precisiones de estimando descritas en la
documentación matemática.

## Reproducir los intervalos de la tabla

Desde la raíz del repositorio:

```bash
python - <<'PY'
import json, math
from pathlib import Path
for path in sorted(Path('results/main').glob('nonlinear_seed*_n12000.json')):
    result = json.loads(path.read_text())
    n = result['split']['test_count']
    radius = math.sqrt(2 * math.log(2 * 9 / 0.05) / n)
    rows = {row['model']: row for row in result['metrics']}
    for comparison in result['comparisons']:
        a, b = comparison['model_a'], comparison['model_b']
        delta = rows[a]['accuracy'] - rows[b]['accuracy']
        assert abs(delta - comparison['delta_accuracy']) < 1e-12
        print(result['config']['seed'], a, b,
              100*delta, 100*(delta-radius), 100*(delta+radius))
PY
```

Los resultados JSON auditados tenían los siguientes SHA-256:

```text
e5f92d5549eb05d6ff4e48159af4345302bd21030e07a296ada2b91d27474f0b  nonlinear_seed11_n12000.json
d3f00cc2c11cf2b270306729b9e4a8909f864553852004fc1bf142ff867641b6  nonlinear_seed29_n12000.json
304de8406b42b92e7e08399c6d19501fd144b9fbaa49c906e6b0a027905ed30b  nonlinear_seed47_n12000.json
```

Los tiempos y las mediciones de memoria son específicos del entorno; ejecutar
de nuevo el benchmark cambia esos campos y por tanto el hash del JSON aun
cuando las predicciones sean reproducibles.
