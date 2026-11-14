# Matriz fija: análisis exacto para una clase de fuentes explícita

Este entregable profundiza la vía alternativa sugerida por la lectura de AIS: si la matriz se fija, se analiza su acción sobre un modelo concreto. No se invoca automáticamente una garantía promedio sobre semillas que ya no se están muestreando.

El código [fixed_matrix_analysis.py](fixed_matrix_analysis.py) calcula exactamente la distribución de salida de una matriz Toeplitz fija para una fuente binaria Markov de primer orden **especificada como entrada**. No decide que una muestra de laboratorio es Markov ni estima sus parámetros. Utiliza fracciones racionales y una transformada de Walsh; para `n=32, m=8` evita enumerar `2³²` palabras.

## Identidad de Fourier

Sea `Y=TX`, con `T` fija, y `v∈GF(2)ᵐ`. Entonces

\[
\phi_Y(v)=\mathbb E[(-1)^{v\cdot Y}]
=\mathbb E[(-1)^{(T^\mathsf tv)\cdot X}]=\phi_X(T^\mathsf tv).
\]

La inversión exacta da

\[
P(Y=y)=2^{-m}\sum_v(-1)^{v\cdot y}\phi_X(T^\mathsf tv).
\]

Para una fuente Markov con distribución inicial `π` y transición `P`, sea `D_a=diag(1,(-1)^a)`. Para una máscara `a₁,…,a_n`:

\[
\phi_X(a)=\pi^\mathsf t D_{a_1}P D_{a_2}P\cdots P D_{a_n}\mathbf1.
\]

La recurrencia mantiene sólo dos pesos firmados, uno por estado. Después se aplica Walsh–Hadamard para reconstruir las `2ᵐ` probabilidades. Complejidad aproximada `O(2ᵐ n + m2ᵐ)` operaciones racionales, más el cálculo de máscaras, con crecimiento del tamaño de los denominadores. La ventaja desaparece si `m` es enorme; es un instrumento de investigación y evaluación de diseños pequeños, no un pipeline de producción de alto throughput.

La minentropía del bloque de entrada se obtiene mediante una recurrencia de máximo producto (Viterbi sin observaciones). Para condicionar en el bit inmediatamente anterior, se sustituye `π` por la fila de transición correspondiente y se toma el peor estado previo. Esto es válido por la hipótesis Markov clásica; no se extrapola a una fuente con memoria oculta ni a información lateral cuántica.

## Cota robusta para bits independientes sesgados

Si los bits son independientes y `|1−2p_j|≤β_j`, entonces

\[
|\phi_X(a)|\le\prod_{j:a_j=1}\beta_j.
\]

Por inversión y Parseval:

\[
\max_yP(Y=y)\le2^{-m}\left(1+\sum_{v\ne0}\prod_{j:(T^\mathsf tv)_j=1}\beta_j\right),
\]

\[
\operatorname{TV}(Y,U_m)\le\tfrac12\sqrt{\sum_{v\ne0}\prod_{j:(T^\mathsf tv)_j=1}\beta_j^2}.
\]

Si todos los `β_j≤β`, basta el enumerador de pesos `A_w=#{v≠0:wt(Tᵗv)=w}`. Las sumas son `Σ_w A_wβʷ` y `Σ_w A_wβ²ʷ`. Esta es una **garantía para una matriz concreta y toda la clase de fuentes independientes con esos límites de sesgo**. No necesita aleatorizar la semilla, pero su clase de fuentes es mucho más restringida que «minentropía k».

Con información lateral clásica, la misma cota sirve si la independencia de bits y los límites `β_j` son válidos condicionados en cada valor lateral relevante. Tener esas propiedades sólo marginalmente no basta. La matriz debe tener rango completo si se pretende cercanía a uniforme para la fuente exactamente uniforme: un vector no nulo `v` con `Tᵗv=0` produce una relación lineal determinista en las salidas.

## Resultados sintéticos

Misma matriz fija de 32 a 8 bits, rango 8. Los parámetros son convenciones sintéticas, no mediciones:

| Modelo | Hmin del bloque bruto | Hmin de salida | TV de salida |
|---|---:|---:|---:|
| IID, `p=0.6` | 23.5829 | 7.999972 | 0.0000064 |
| Markov simétrico, permanencia `0.8` | 10.9798 | 7.826108 | 0.023328 |
| Markov simétrico, permanencia `0.95` | 3.2940 | 3.280711 | 0.413381 |
| IID uniforme | 32 | 8 | 0 |

En los dos modelos Markov las marginales de cada bit son exactamente uniformes. La pérdida nace de la dependencia. La minentropía total de salida no excede la entrada, como exige cualquier transformación determinista; aumentar entropía **por bit de salida** no crea entropía total.

[fixed_matrix.json](results/fixed_matrix.json) conserva la semilla fija, matrices de transición, distribución inicial, enumerador de pesos y cotas robustas para `|1−2p_j|≤0.2`. Incluye una columna comparativa del LHL para una semilla hipotéticamente uniforme; esa columna **no es una cota** para la semilla fija estudiada.

## Validación y límites

Seis tests adicionales comparan el método de transferencia y Fourier contra enumeración exhaustiva para todas las semillas de familias pequeñas, verifican el caso IID, las probabilidades máximas de trayectorias y el mapa cero. Estos seis tests, junto con los ocho del laboratorio inicial, cubren este método; la suite completa añade cuatro tests intervalares y suma dieciocho. El resultado no valida la hipótesis de Markov, los intervalos de parámetros, la ausencia de fugas ni la conformidad de un producto.

Una siguiente ampliación útil sería demostrar cotas sobre **intervalos** de matrices de transición. Evaluar sólo una malla de parámetros no demuestra un peor caso continuo; las probabilidades son polinomios y sus extremos no tienen por qué quedar en vértices sin una prueba adicional.

## Ejecución

```bash
python3 -m unittest -v
python3 fixed_matrix_analysis.py
```
