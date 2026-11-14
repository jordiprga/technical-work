# Fuga por telemetría del control de umbral

Resultado transversal del coordinador, 14 de noviembre de 2026. Son demostraciones matemáticas de modelos genéricos y experimentos finitos exactos. No se afirma novedad científica ni se atribuyen estos comportamientos a un producto real.

## El adversario causal no es el adversario al final del experimento

Sea Bₜ el bit que produce un comparador con umbral θₜ. Conocer la probabilidad de Bₜ dado θₜ y la información pasada responde a una pregunta de predicción causal. El usuario de bits criptográficos suele necesitar una garantía frente a toda la información E que acaba teniendo el adversario, incluida telemetría posterior.

Un controlador sin saturación, sin banda muerta y con ganancia conocida g>0 actualiza, para una ventana de W bits y objetivo p*:

\[
\theta_{k+1}=\theta_k+g(C_k/W-p^*),\qquad C_k=\sum_{t\in\text{ventana }k}B_t.
\]

Si ambos umbrales consecutivos son observables con precisión suficiente, entonces

\[
C_k=W\left((\theta_{k+1}-\theta_k)/g+p^*\right).
\]

El transcript de umbrales contiene los conteos. Esto es una identidad algebraica: no depende de IID, de la distribución arcsine ni de asumir entropía alguna.

Para W=U=1, el transcript completo revela cada bit, de modo que H̃∞(Bⁿ|E)=0. En particular, el ejemplo QRNG de parejas equiprobables 01/10 puede tener H∞(Bⁿ)=n/2 y, al publicar todos los umbrales, cero entropía secreta restante. Si no se publica la última actualización, este argumento deja al menos ese último segmento fuera de la reconstrucción; hay que especificar exactamente qué observa E.

## Ventanas independientes y disjuntas: una cuenta exacta

Consideremos ahora una fuente de n=JW bits uniformes independientes y una telemetría que revela sólo el conteo de cada ventana disjunta. **Este caso de referencia no supone que un comparador realimentado mantenga bits IID.** Sirve para aislar el efecto del canal de divulgación.

La minentropía condicional promedio clásica se define por

\[
\widetilde H_\infty(X|T)=-\log_2\sum_t\max_xP(X=x,T=t).
\]

Para un bloque uniforme, cada palabra tiene probabilidad 2⁻ᵂ. Hay W+1 conteos posibles y cada uno contribuye 2⁻ᵂ a la probabilidad óptima de adivinación. Por tanto,

\[
\widetilde H_\infty(B^W|C)=W-\log_2(W+1),
\qquad
\widetilde H_\infty(B^{JW}|C_1,\ldots,C_J)
=J[W-\log_2(W+1)].
\]

No confundir esto con la entropía de Shannon ni con el promedio de minentropías puntuales. Para un conteo concreto c, la fuente uniforme tiene H∞(Bᵂ|C=c)=log₂ binom(W,c); los casos c=0 y c=W tienen valor cero. Promediar los logaritmos no produce el logaritmo de la probabilidad de adivinación promedio.

Para una fuente general X y un transcript finito T con M posibles valores, la desigualdad clásica H̃∞(X|T)≥H∞(X)−log₂M da una cota conservadora de pérdida por divulgación. Con información lateral E preexistente, la misma desigualdad vale para la minentropía condicional promedio clásica: H̃∞(X|E,T)≥H̃∞(X|E)−log₂M. Esto no calcula la entropía inicial ni convierte una estimación marginal en una garantía conjunta.

## Ventanas solapadas: el tamaño de ventana no evita reconstrucción

Con actualización cada bit U=1, sean Cₜ los conteos de ventanas consecutivas de W bits. Entonces

\[
C_t-C_{t-1}=B_t-B_{t-W}.
\]

Elegidos los W primeros bits, todos los posteriores quedan determinados por esa recurrencia. Dado el primer conteo c₀, hay como máximo binom(W,c₀) candidatos iniciales. Por consiguiente, para cualquier distribución sobre los bits compatible con ese transcript,

\[
H_\infty(B^n|T=t)\le \log_2\binom W{c_0}\le W.
\]

También H̃∞(Bⁿ|T)≤W y su tasa por bit tiende a cero cuando W permanece fijo y n crece. La demostración es de soporte: toda distribución sobre a lo sumo M candidatos tiene probabilidad máxima ≥1/M. Algunas transcripciones determinan una única palabra y dejan entropía cero incluso para un n finito.

El algoritmo `reconstruct_rolling` enumera sólo las posibles W entradas iniciales, reconstruye cada sufijo por diferencias y elimina cualquier candidato que produzca un valor distinto de 0 o 1. No necesita enumerar 2ⁿ palabras. La suite compara sus resultados con la partición exhaustiva de una fuente corta.

## Generalización: importa el período de actualización, no sólo W

Revisión independiente de la misión 04: sea U un divisor de W, L=W/U y n=JU con J≥L. Agrupar los bits en J grupos disjuntos de U bits y llamar cⱼ al conteo de cada grupo. Las observaciones son sumas de L conteos consecutivos. Dados los L−1 primeros conteos y la primera suma, queda fijado el siguiente; las diferencias de sumas fijan todos los restantes.

Hay (U+1)ᴶ secuencias de conteos posibles y cada transcript tiene como máximo (U+1)ᴸ⁻¹ preimágenes. Si M es el número de transcripts posibles:

\[
(U+1)^{J-L+1}\le M\le(U+1)^J.
\]

Para bits de referencia uniformes, toda palabra tiene masa 2⁻ⁿ, de modo que Pguess=M/2ⁿ y

\[
n-J\log_2(U+1)\le\widetilde H_\infty(B^n|T)
\le n-(J-L+1)\log_2(U+1).
\]

Manteniendo W y U fijos y haciendo J→∞, la tasa exacta converge a **1−log₂(U+1)/U**, independientemente de W. La primera ventana sólo aporta un término de borde acotado. Para U=1 la tasa es cero; para U=2 es aproximadamente 0.2075 bits por bit. Esto no se extiende por sustitución a una fuente realimentada no uniforme: la fórmula exacta usa equiprobabilidad de las palabras. El resultado de soporte para U=1 sí era independiente de esa hipótesis.

## Resultados reproducidos

| Fuente de referencia | W | U | Bits | H∞ antes | H̃∞ después de revelar conteos |
|---|---:|---:|---:|---:|---:|
| Uniforme | 1 | 1 | 8 | 8 | 0 |
| Uniforme | 4 | 4 | 12 | 12 | 5.0342 |
| Uniforme | 4 | 1 | 12 | 12 | 0.1185 |
| Uniforme | 4 | 1 | 16 | 16 | 0.0314 |
| Parejas 01/10 equiprobables | 1 | 1 | 12 | 6 | 0 |

Las probabilidades de [results.json](results.json) se calculan con `fractions.Fraction`, sin Monte Carlo. Sólo la transformación final a logaritmos se aproxima en punto flotante. En el caso uniforme W=4,U=1,n=16, el atacante tiene probabilidad óptima exacta 64125/65536.

## Límites y consecuencias de diseño

- Los umbrales pueden ser internos y no accesibles al adversario. Si es así, esta fuga no se presume: debe justificarlo el modelo de amenazas.
- Una banda muerta, clipping, cuantización de telemetría o ruido observado limita la inversión exacta. No implica automáticamente fuga pequeña. Se deben agrupar todas las preimágenes del transcript realmente observable y volver a calcular o acotar la probabilidad de adivinación.
- Cota de precisión: si cada umbral observado tiene error absoluto ≤ε, el conteo inferido tiene error ≤2Wε/g. Por tanto ε<g/(4W) garantiza recuperación exacta por redondeo al entero. Para telemetría redondeada con paso Δ, basta Δ<g/(2W). Esto supone el controlador ideal descrito; cuantizar el actuador modifica la ecuación y requiere otro análisis.
- Los updates visibles pueden revelar información aun si los valores de θ se ocultan: momentos de activación, alarmas, contadores, logs de depuración y estadísticas también forman parte de E.
- Un extractor fuerte tolera semilla pública bajo sus supuestos; no recupera entropía que ya se ha revelado. El parámetro de entrada debe ser Hmin(X|E) con el transcript pertinente incluido.
- Si el propio feedback utiliza salidas extraídas con la semilla S, puede fallar además la independencia entre S y la fuente conjunta; esto es una obligación separada del presupuesto de entropía.
- Los experimentos uniformes son un modelo del canal de divulgación, no una estimación de entropía del simulador físico de la misión 05.

## Reproducción

```bash
cd /workspace/operation-token-burn/00_coordination/feedback_leakage
python3 -m unittest -v
python3 leakage.py --out results.json
```

Dependencias: Python 3.10+ y biblioteca estándar. Nueve tests comprueban fórmulas exactas, cotas de cardinalidad para distintos períodos, reconstrucción, recuperación algebraica de conteos y entradas inválidas. No hay acceso a red, dispositivos o datos privados.

Estas pruebas son derivaciones propias. La base teórica y bibliografía primaria sobre minentropía lateral y extracción está en [la misión 04](../../04_extractors_entropy/README.md); el modelo de control físico genérico está en [la misión 05](../../05_qrng_model/README.md).
