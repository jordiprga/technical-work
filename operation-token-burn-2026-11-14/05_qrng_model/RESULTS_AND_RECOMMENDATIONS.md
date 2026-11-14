# Resultados, interpretación y decisiones

Ejecutado el 14 de noviembre de 2026. Parámetros de referencia: A=1, ruido clásico σ=0.15, fase IID, sin deriva, W=U=256, g=0.5, objetivo 1/2 y límites ±3. Cada caso tiene cuatro semillas independientes, 524 288 muestras y descarte de 16 384 muestras iniciales. Las comparaciones usan las mismas semillas entre configuraciones para reducir variación ajena al parámetro estudiado; las réplicas entre sí son independientes.

Los CSV incluyen 96 ejecuciones y todos sus parámetros. Las barras ± de las figuras representan desviación estándar **entre cuatro réplicas**, no intervalos de confianza ni incertidumbre metrológica. No se ha estimado una incertidumbre de modelo físico. La semilla no se utiliza como fuente de seguridad.

## Hallazgos numéricos principales

`Hcausal` designa `−log₂ promedio[max(pₜ,1−pₜ)]`, calculado con ruido clásico y estado causal revelados. **Excluye el transcript futuro del controlador**; no es una tasa de min-entropía de bloques. En los casos de difusión, además se revela la fase anterior, una información lateral más fuerte que observar sólo bits. Por ello las filas no deben tratarse como una comparación uniforme de seguridad física.

| Escenario | Fracción de unos | Corr. bloques consecutivos | Hcausal (bits) | Interpretación |
|---|---:|---:|---:|---|
| Umbral fijo, fase IID | 0.500062 | 0.0015 | 0.8932 | El ruido clásico revelado reduce la incertidumbre respecto al bit marginal casi perfecto. |
| g=0.5, W=U=256 | 0.499989 | −0.0831 | 0.8912 | El control equilibra y crea anticorrelación entre bloques. |
| g=2, W=U=256 | 0.499998 | −0.3299 | 0.8831 | Mayor corrección introduce más memoria y jitter. |
| g=5, W=U=256 | 0.500055 | −0.9102 | 0.6719 | Grandes excursiones y dispersión entre réplicas; la aproximación local pierde precisión. |
| g=7, W=U=256 | 0.500000 | −1.0000 | 0.000006 | Balance casi perfecto junto a alternancia de bloques casi deterministas. |
| g=4, W=1024, U=256 | 0.499976 | 0.6645 | 0.1717 | El solapamiento produce oscilación con ganancia excesiva para ese retardo. |
| g=2, W=4096, U=256 | 0.499625 | 0.9538 | 0.0927 | Oscilación lenta y fuerte memoria. |
| Umbral fijo, σ=1 conocido | 0.500127 | 0.0098 | 0.3747 | Incrementar ruido observado no implica incrementar entropía privada. |
| Difusión sφ=0.25, control | 0.500144 | −0.0160 | 0.0952 | El control oculta el sesgo de largo plazo, pero la memoria de fase sigue presente. |

La correlación de bits consecutivos en el caso de difusión sφ=0.25 es aproximadamente 0.83 y el predictor de contexto de seis bits acierta alrededor del 91.5 %. El mismo histograma arcsine marginal es compatible con fase IID o con esta fase altamente correlacionada. El predictor es un diagnóstico empírico, no una prueba de optimalidad ni una cota de entropía con confianza estadística.

## Comparación con la teoría local

La densidad numérica f_X(0) de referencia es aproximadamente 0.322. Para W=U y g=0.5, la fórmula predice correlación de bloques cercana a −0.0805; la observada es −0.0831 ± 0.0215. Para g=2 predice aproximadamente −0.322; la observada es −0.3299 ± 0.0123. Esta concordancia apoya la implementación y el uso local de la aproximación en esos parámetros; no prueba su validez global.

Para g=5, la varianza de umbral media es 0.271, con desviación entre réplicas 0.318. Este tamaño relativo revela que una cifra media oculta regímenes muy distintos. Aunque g f_X(0)<2, el controlador puede abandonar la zona donde la pendiente f_X(0) describe la distribución. El análisis adicional del mapa no lineal encuentra un ciclo estable de amplitud 1.234763 y otro inestable de amplitud 0.851462 para g=5, coexistiendo con θ=0 estable. Esta estructura es compatible con transiciones entre regímenes por fluctuaciones finitas; no se ha demostrado una tasa de escape. Véase [la figura de bifurcación](figures/nonlinear_bifurcation.png) y la sección 11 del modelo. No se recomienda elegir ganancia sólo por el criterio local.

La ventana larga W=U=2048 reduce la varianza del umbral de aproximadamente 0.000892 a 0.000103 respecto de W=256, pero sólo aporta unas 248 ventanas después del descarte. La correlación estimada tiene desviación de réplicas 0.0703: aquí no procede interpretar una diferencia pequeña frente a la teoría como un efecto confirmado.

Para ventanas solapadas, la ganancia crítica depende de K=W/U. K=4 permite a<1.1716; K=16 permite a<0.3074. Mantener g fijo al aumentar K puede cruzar la frontera de estabilidad. Aumentar W sin revisar g y U es una decisión de control, no sólo una mejora de precisión estadística.

## Deriva y banda muerta

Con offset sinusoidal de amplitud 0.4 y periodo 32 768 muestras, g=0.5 y W=U=256 sigue razonablemente el offset en este modelo: Hcausal≈0.876 frente a 0.762 con umbral fijo. Cambiar a W=U=2048 conservando g hace el control ocho veces más lento en muestras; el resultado Hcausal≈0.763 apenas mejora el caso fijo. El efecto depende de la escala temporal de la deriva. No demuestra que W=256 sea óptimo para otra frecuencia de muestreo o dispositivo.

Las bandas muertas 0.02 y 0.05 reducen ciertas correcciones y alteran correlaciones de bloques, pero no mejoran de forma significativa Hcausal en estos ensayos. La simulación larga corrige el offset inicial del caso `deadband_biased`; no se ha observado un sesgo residual persistente importante con esos parámetros. La existencia de una región de equilibrio del modelo medio no equivale a una observación de bloqueo permanente cuando hay ruido.

## Recomendaciones condicionadas al modelo

1. **Separar tres objetivos de diseño.** Estabilizar el punto de operación, producir bits con baja dependencia y acreditar entropía condicional son tareas distintas. Una métrica de balance sólo cubre parte de la primera.
2. **Definir la telemetría del controlador como posible fuga.** Si los umbrales posteriores son observables, incorporarlos a la información lateral del bloque. Con precisión exacta y sin saturación revelan cuentas de ventanas. W=U=1 revela todos los bits. Véase [análisis de fuga de coordinación](../00_coordination/feedback_leakage/README.md).
3. **Elegir g, W y U conjuntamente.** Estimar la pendiente alrededor de los extremos de operación, incluir retardo y saturación, y exigir margen respecto a las raíces del modelo. La condición local en el punto nominal es insuficiente ante excursiones o cambios de amplitud.
4. **Distinguir frecuencia de muestreo de frecuencia de actualización.** Registrar fs, U/fs, W/fs, ancho de banda del detector y escalas de deriva. Un barrido en muestras carece de recomendación física universal si no se conoce esa correspondencia.
5. **Conservar muestras antes del control/postprocesado.** Diseñar capturas sintéticas o de evaluación autorizada que permitan analizar señales analógicas, umbral, decisiones de actualización, estados de fallo y salidas. Aplicar después un modelo de amenaza que determine qué parte del registro puede salir del perímetro protegido.
6. **Evaluar condicionamiento en bloques.** Si se quieren extraer m bits de n muestras, justificar una cota de min-entropía del bloque condicionada a historial e información lateral pertinente. No usar n veces una estimación marginal ni n veces la métrica causal de este informe.
7. **Repetir ensayos por regímenes.** Inicio, cambio de offset, cambio de amplitud, ruido clásico correlacionado, deriva rápida, saturación, pérdida de difusión y reinicio del controlador deben tener escenarios propios. Descartar un prefijo de longitud fija no demuestra que todos ellos mezclen igual.
8. **Cuantificar colas y fallos.** Gaussianas de soporte infinito impiden ciertas cotas puntuales uniformes positivas. Si se usa una región de operación de alta probabilidad, declarar la probabilidad fuera de región y cómo se agrega al error de seguridad.

## Evidencia y límites por categoría

| Categoría | Resultado | Alcance |
|---|---|---|
| Demostración analítica | Arcsine marginal; correlación de fase; ley causal; contraejemplo de pares; cadena finita y tasa Hmin. | Sólo dentro de los modelos especificados. |
| Aproximación matemática | Varianza de umbral, correlación de bloques, polinomio de estabilidad local. | Cerca del equilibrio y bajo hipótesis de sección 4; la condición de raíces es exacta para la dinámica linealizada. |
| Experimento reproducible | 24 escenarios y cuatro réplicas, gráficas y CSV. | Datos sintéticos, tolerancias y parámetros documentados. |
| Hipótesis física | Independencia del componente de fase confiado; adecuación de ruido gaussiano/aditivo y difusión circular. | No contrastadas con un dispositivo. |
| No demostrado | Entropía de hardware, seguridad cuántica general, estacionariedad global, certificación NIST/BSI. | Requiere modelo y evidencia adicionales. |

## Trabajo posterior con mayor valor

- Incorporar respuesta FIR/IIR del detector y demostrar qué memoria queda al condicionar por estado accesible; las pruebas de histograma no bastan.
- Modelar DAC cuantizado, offset del comparador, metastabilidad, retardo variable y anti-windup; estudiar explícitamente la fuga de telemetría cuantizada.
- Sustituir parámetros puntuales por intervalos calibrados y optimización adversarial, manteniendo separados los errores de modelo y de muestreo.
- Para modelos finitos, calcular probabilidades máximas de bloques con programación dinámica y aritmética de intervalos; para modelos continuos, construir abstracciones conservadoras antes de reclamar una tasa.
- Comparar control con umbral fijo durante bloques de extracción y actualizaciones sólo en bloques separados destinados a calibración. Esto puede simplificar el análisis, pero reduce rendimiento y no elimina la necesidad de caracterizar dependencia entre bloques.

El análisis posterior de una matriz Toeplitz fija debe conservar el modelo de dependencia: [métodos exactos de la misión de extractores](../04_extractors_entropy/fixed_matrix_methods.md) proporciona una vía para casos Markov binarios pequeños. El hecho de que ambas piezas sean computables no demuestra automáticamente que el proceso de feedback sea Markov de orden uno en los bits.

## Comprobación numérica adicional

[numerical_validation.py](numerical_validation.py) contrasta el análisis con cálculos independientes de los barridos Monte Carlo. La densidad f_X(0) se evalúa mediante Bessel escalada; la bifurcación se recalcula con 256, 1024, 4096 y 16 384 nodos de fase. Los valores de nacimiento del ciclo y de sus raíces coinciden en las seis cifras que se reportan. Esto verifica resolución numérica en los parámetros estudiados; no acredita precisión para cualquier entrada.

Para umbral fijo cero, fase IID y ruido gaussiano **conocido, no controlado** por el adversario, la integral unidimensional independiente da Hcausal=0.893264 para σ=0.15 y 0.374867 para σ=1. Los respectivos promedios Monte Carlo fueron 0.893236 y 0.374688. Las diferencias son pequeñas respecto de la dispersión entre réplicas y apoyan que el cálculo condicional se implementó de forma coherente. Todos los casos mantienen min-entropía marginal teórica exactamente 1 por simetría.

La [salida JSON](results/numerical_validation.json) conserva además sensibilidad a σ=0.01, 0.05, 0.3 y 0.6. El ruido clásico puede modificar simultáneamente la pendiente del controlador y la incertidumbre privada; ambas consecuencias requieren un análisis separado.
