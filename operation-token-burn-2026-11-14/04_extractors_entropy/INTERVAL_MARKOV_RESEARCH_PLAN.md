# Matriz fija y modelo Markov con parámetros inciertos

## Resultado ya disponible

Se implementó [interval_markov.py](interval_markov.py), una prueba de concepto con **intervalos racionales exactos**, subdivisión de cajas y certificado verificable. Calcula cotas de la peor probabilidad de salida de una Toeplitz fija en toda una caja de parámetros Markov binarios. No aproxima el dominio continuo mediante una malla ni presume que los extremos estén en vértices.

Este resultado certifica una desigualdad matemática **dentro del modelo y caja declarados**. No acredita que la caja contenga los parámetros de un aparato ni que su proceso sea Markov, ni sustituye una evaluación AIS.

La configuración sintética inicial es:

- `n=8`, `m=2`, semilla fija entera `133` con la convención del laboratorio.
- Distribución inicial exactamente `(1/2,1/2)`.
- `a=P(1|0)∈[1/10,3/20]`, `b=P(0|1)∈[1/5,1/4]`.
- `P=[[1−a,a],[b,1−b]]`; reutilizar un mismo parámetro entre pasos es parte del modelo.

Se conserva [el certificado racional](results/interval_markov_certificate.json) y [el benchmark](results/interval_markov_benchmarks.json). La ejecución final termina con **201 hojas**, brecha en probabilidad `<0.001`, y delimita la peor minentropía de salida entre aproximadamente **1.49177 y 1.49581 bits**. Los extremos racionales de probabilidad son exactos; los logaritmos impresos son aproximaciones de coma flotante.

## Objetivo matemático y certificado

Para cada parámetro `θ=(a,b)` y salida `y`, sea `q_y(θ)=Pr_θ[T X=y]`. Se busca

\[
M=\sup_{\theta\in B}\max_y q_y(\theta),\qquad
\inf_{\theta\in B}H_{\min}(TX)=-\log_2M.
\]

Una evaluación puntual racional en cualquier `θ₀∈B` proporciona una **cota inferior** de `M`. Una inclusión intervalar `q_y(C)⊆[l_y,u_y]` para cada hoja `C` de una partición de `B` proporciona una **cota superior** `max_C max_y u_y`.

El certificado contiene:

1. Matriz, dimensiones, caja raíz y distribución inicial.
2. Hojas identificadas mediante caminos binarios de bisecciones deterministas.
3. Cota superior racional y testigo central exacto por hoja.
4. Mejor testigo retenido, incluso si su caja se subdividió después.
5. Cotas globales racionales y brecha.

El verificador reconstruye cada caja desde su camino, comprueba que las hojas son prefijo-libres y que `Σ2^(−longitud)=1`, y recalcula cada inclusión y testigo. En un árbol binario finito esto prueba cobertura de la caja raíz. También comprueba que el mejor testigo pertenece a la caja. El certificado no confía en una supuesta enumeración completa de puntos. El verificador recalcula también las cifras aproximadas de entropía y rechaza discrepancias superiores a 10⁻¹² bits; el campo narrativo `meaning` es informativo, no una afirmación autenticada. Los extremos y escalares de la API intervalar rechazan floats y aceptan sólo enteros o Fraction exactos.

**Base de confianza actual:** implementación Python, enteros/racionales de la biblioteca estándar, algoritmo de intervalos y la identidad de Fourier demostrada en `fixed_matrix_methods.md`. El replay comparte implementación con el generador; es verificación reproducible y contra manipulación de datos, no un núcleo formal independiente. Una siguiente fase debe reducir esa base de confianza.

## Algoritmo y por qué es correcto

La identidad Walsh convierte cada coeficiente en un producto de matrices 2×2 con entradas polinómicas en `a,b`. Se evalúan sumas y productos sobre intervalos racionales. Toda operación incluye su conjunto de valores exactos por construcción: suma de extremos, producto de las cuatro esquinas, negación con intercambio de extremos.

La repetición de `a,b` genera **dependencia intervalar**, que ensancha las cotas pero no las vuelve optimistas. Por ejemplo, evaluar `a+(1−a)` ingenuamente puede producir un intervalo más ancho que `{1}`. Se usa explícitamente `φ(0)=1`, identidad de normalización, para reducir esa pérdida. Todas las probabilidades se intersectan con `[0,1]`, un hecho universal del modelo.

Se mantiene una cola de prioridad por cota superior. Se subdivide una hoja de mayor cota por su dimensión más ancha, y se evalúan ambas mitades. El proceso termina cuando la brecha real entre la mejor cota superior y el mejor testigo es menor que la tolerancia, o cuando se alcanza el límite de hojas. **Si termina por presupuesto con brecha grande, conserva una cota amplia; no declara éxito de precisión.**

Para un número finito de pasos y parámetros en una caja compacta, las probabilidades son continuas. Una subdivisión que haga tender a cero el diámetro de las cajas relevantes y una extensión intervalar convergente permiten aproximar `M` tanto como se desee. No se promete complejidad polinómica ni convergencia rápida. En la versión actual las fórmulas racionales evitan errores de redondeo, a costa de denominadores grandes.

## Por qué no basta comprobar vértices

Las entradas de `P` son afines, pero la misma matriz aparece repetida. Una probabilidad de trayectoria puede contener términos como `a²(1−a)`; el producto no es multiafín en el parámetro global `a`. Incluso `a(1−a)` tiene su máximo en el interior de `[0,1]` y vale cero en ambos extremos. El mero hecho de que cada transición sea afín no autoriza una regla de vértices para una secuencia completa.

Para una familia o propiedad particular se puede demostrar monotonía, convexidad o una forma multiafín genuina; entonces se puede explotar. Sin esa prueba, muestrear los vértices o una malla sólo produce testigos y diagnósticos, no una cota superior certificada.

## Benchmarks pequeños ejecutados

| Presupuesto de hojas | Hojas usadas | Brecha de probabilidad | Intervalo aproximado de peor Hmin |
|---:|---:|---:|---|
| 1 | 1 | 0.144642 | [1.08778, 1.61775] |
| 16 | 16 | 0.025332 | [1.41141, 1.51206] |
| 64 | 64 | 0.006290 | [1.47404, 1.49947] |
| 256 | 201 | 0.000993 | [1.49177, 1.49581] |

Los tiempos observados se guardan sólo como mediciones de este entorno y configuración; no se extrapolan a throughput de producto. Cuatro tests nuevos comprueban inclusiones sobre una malla racional como regresión, coincidencia exacta de intervalos puntuales y rechazo de certificados con hojas omitidas o cotas modificadas. La garantía continua proviene de la aritmética intervalar y la cobertura, no del test sobre la malla.

## Hoja de ruta ejecutable por una persona durante diez días

| Fase | Trabajo concreto | Criterio de aceptación |
|---|---|---|
| Días 1–2 | Separar generador y checker; serialización racional canónica, límites de recursos y validación estricta de esquema | Checker acepta certificados válidos y rechaza cobertura incompleta, límites alterados, parámetros fuera de caja y dimensiones incompatibles. |
| Días 3–4 | Mejorar inclusiones: polinomios dispersos de baja dimensión, forma de Bernstein o modelos de Taylor; preservar versión intervalar simple como referencia | Misma cota o más estrecha, con replay independiente. Comparar número de hojas, tamaño certificado y tiempo sin cambiar el modelo. |
| Días 5–6 | Incorporar estado inicial conocido/adversario y familias de modelos, conservando cada supuesto | Cota peor caso sobre `S₀=0/1`; test explícito donde promedio estacionario sobreestima entropía frente a estado conocido. |
| Días 7–8 | Extender a HMM finito con matrices etiquetadas por bit; integrar caso racional de feedback g=2 | Coincidencia exacta con enumeración de pares 01/10 y Toeplitz; no asumir que los bits observados son Markov1. |
| Días 9–10 | Certificado/contrato de entropía para CryptoSure y bosquejo de checker formal | Bundle identifica caja, matriz, información lateral, definición de entropía, checker y resultado; se conserva REVIEW para adecuación física/normativa. |

Priorizar primero `n≤32,m≤8,2–4 parámetros`. La enumeración de salidas `2ᵐ` limita esta arquitectura. Para `m` grande se necesita explotar estructura del código lineal, factorizar el grafo o usar cotas espectrales; aumentar los recursos sin cambiar el algoritmo no resuelve esa barrera.

## Extensión HMM y vínculo con el QRNG realimentado

La misión 05 propone una extensión útil: para estado finito `S`, usar matrices etiquetadas

\[
P_b[i,j]=\Pr(B=b,S'=j\mid S=i),\quad
M_a=P_0+(-1)^aP_1.
\]

Entonces

\[
\phi_X(a_1,…,a_n)=\pi^\mathsf tM_{a_1}\cdots M_{a_n}\mathbf1.
\]

La misma inversión Walsh calcula la salida de una Toeplitz fija sobre el proceso oculto. Esto incluye control por umbral y memoria de estado sin declarar que los bits por sí solos sean Markov de primer orden.

Para el ejemplo exacto `g=2,A=1` de la misión 05, las transiciones del estado `−1,0,1` tienen probabilidades `0,1/2,1`, por lo que son racionales y admiten una primera integración exacta. Para ganancias generales aparece `arccos(θ/A)/π`: se requieren intervalos trascendentes certificados, por ejemplo con una biblioteca de bolas con redondeo controlado y un checker adecuado. Copiar floats y añadir un epsilon arbitrario no basta.

Además cambia el número de estados alcanzables cuando `ceil(A/(g/2))` cambia. El dominio de parámetros debe particionarse por cambios de topología, o usarse una abstracción común conservadora. Una cadena calculada para un punto nominal no representa automáticamente toda una caja de parámetros.

## Qué seguiría sin estar demostrado

- Que los parámetros físicos y la dinámica reales pertenecen al modelo/caja.
- Que la información lateral del adversario se reduce a parámetros y estados clásicos modelados.
- Ausencia de fugas del transcript del controlador o de la implementación.
- Seguridad cuántica a partir de una mera cadena Markov clásica.
- Aceptación de la evidencia en un esquema de certificación.

El avance concreto es reemplazar una exploración de parámetros por una desigualdad continua reproducible, manteniendo separadas esas obligaciones.
