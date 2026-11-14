# Teoría, supuestos y pruebas

Este documento combina resultados clásicos identificados con derivaciones explícitas realizadas para esta investigación. No se presenta una prueba nueva del leftover hash lemma cuántico ni una certificación física.

## 1. La garantía que se quiere demostrar

Sean `X ∈ {0,1}ⁿ` los datos brutos, `S` una semilla y `Y = T_S X ∈ {0,1}ᵐ`, con operaciones sobre GF(2). Para distribuciones clásicas:

\[
\operatorname{TV}(P,Q)=\tfrac12\sum_z |P(z)-Q(z)|,
\qquad H_{\min}(X)=-\log_2\max_x P(X=x).
\]

Con información lateral clásica `E` usamos **minentropía condicional promedio**:

\[
p_{\rm guess}(X|E)=\sum_eP(e)\max_xP(x|e),\quad
H_{\min}(X|E)=-\log_2p_{\rm guess}(X|E).
\]

No es `E_e[Hmin(X|E=e)]`: logaritmo y promedio no conmutan. Una cota de peor caso sobre cada `e` implica la cota promedio; el recíproco no.

Un extractor strong satisface, para una semilla uniforme **independiente de `(X,E)`**,

\[
\operatorname{TV}(P_{S,Y,E},P_S\otimes U_m\otimes P_E)\le\epsilon.
\]

La semilla está dentro de la vista del adversario. Por ello puede ser pública en este teorema. La independencia debe seguir siendo cierta para el experimento de generación considerado: si un atacante observa `S` y después elige la fuente según `S`, el experimento ha cambiado.

La distancia conjunta es operacional: cualquier prueba, incluso computacionalmente ilimitada, cambia su probabilidad de aceptación como máximo en `ε`. **No** equivale automáticamente a una probabilidad física de que el aparato «esté roto». Tampoco significa que todos los valores de semilla tengan el mismo error.

## 2. Toeplitz es 2-universal: demostración directa

Convención del código: `T[i,j] = s[i-j+n-1]`, `0≤i<m`, `0≤j<n`; la semilla tiene `n+m−1` bits uniformes. Para cualesquiera `x≠x'`, sea `d=x⊕x'≠0` y `j₀=min{j:d_j=1}`. Por linealidad:

\[
T_sx=T_sx' \iff T_sd=0.
\]

En la ecuación de fila `i`, el bit `s[i-j₀+n−1]` aparece con coeficiente uno. Los demás bits que aparecen corresponden a `j>j₀`, por tanto tienen índice menor. Fijados todos los bits de semilla fuera de esos `m` pivotes, las ecuaciones se resuelven sucesivamente para `i=0,…,m−1`: hay exactamente una elección de los pivotes para cada vector de salida objetivo.

Así, para cualquier `z∈{0,1}ᵐ`, existen exactamente `2^(n−1)` semillas con `T_sd=z`, de un total `2^(n+m−1)`. En particular:

\[
\Pr_S[T_Sx=T_Sx']=2^{-m}.
\]

Esto demuestra universalidad de colisiones. **No** demuestra independencia por pares de `(T_Sx,T_Sx')`: `T_S0=0` siempre. No confundir «familia universal₂» con «familia de funciones aleatorias plenamente independientes» ni con resistencia criptográfica a colisiones. La noción de universalidad se remonta a [Carter y Wegman, 1979](https://doi.org/10.1016/0022-0000(79)90044-8).

## 3. LHL clásico: derivación por colisiones

Sea `p(x)` una fuente fija, independiente de `S`, y `q_s(y)=P[T_sX=y]`. Su probabilidad de colisión es `CP(X)=Σ_x p(x)²`. Para una familia universal₂:

\[
\mathbb E_S\sum_yq_S(y)^2
\le \mathrm{CP}(X)+2^{-m}(1-\mathrm{CP}(X)).
\]

Restando `2⁻ᵐ`,

\[
\mathbb E_S\sum_y(q_S(y)-2^{-m})^2
\le(1-2^{-m})\mathrm{CP}(X).
\]

Cauchy–Schwarz y Jensen dan:

\[
\mathbb E_S\operatorname{TV}(q_S,U_m)
\le\tfrac12\sqrt{(2^m-1)\mathrm{CP}(X)}
\le\tfrac12\sqrt{2^{m-H_{\min}(X)}}.
\]

La media izquierda es exactamente la distancia conjunta incluyendo `S`. Para `E` clásico, aplicar el argumento condicionado en `e`, promediar y usar Jensen junto a `CP(X|e)≤max_x p(x|e)` produce:

\[
\epsilon\le\tfrac12\,2^{(m-H_{\min}(X|E))/2}.
\]

De ahí la regla de dimensionamiento, con esta convención del factor `1/2`:

\[
m\le k-2\log_2(1/(2\epsilon)).
\]

La regla más conservadora `m≤k−2log₂(1/ε)` también es válida. Omitir toda penalización y tomar `m=k` sólo ofrece la cota `ε≤1/2`, insuficiente para una garantía criptográfica fuerte.

### Una semilla mala no queda excluida

Si `d_s=TV(q_s,U_m)`, Markov da `Pr[d_S>δ]≤ε/δ`. La prueba de segundo momento anterior permite además:

\[
\Pr[d_S>\delta]\le\frac{(2^m-1)\mathrm{CP}(X)}{4\delta^2}.
\]

Es una cota sobre **una fuente fijada antes de muestrear S**. No permite intercambiar los cuantificadores y afirmar que una misma semilla funciona para todas las fuentes de entropía `k`. Seleccionar una semilla «que pasa tests» también cambia su distribución: habría que demostrar la propiedad de la familia condicionada o justificar específicamente la semilla seleccionada.

## 4. Reutilización: un teorema suficiente que admite dependencias

**Proposición de composición para un horizonte finito.** Sea un proceso clásico `X₁,…,X_t` y una información lateral `E` fijados conjuntamente. Sea `S` uniforme e independiente de **todo** `(X₁,…,X_t,E)`. Para cada `i`, sea `Ext_i` una familia strong tal que:

\[
H_{\min}(X_i\mid X_{<i},E)\ge k_i,
\quad
\epsilon_i=\tfrac12 2^{(m_i-k_i)/2}.
\]

Cada llamada utiliza la misma `S` —o proyecciones uniformes de una semilla común que implementen la familia requerida— y produce `Y_i=Ext_i(X_i,S)`. Entonces:

\[
\operatorname{TV}(S,E,Y_1,…,Y_t;\ S,E,U_{m_1},…,U_{m_t})
\le\min(1,\sum_i\epsilon_i).
\]

**Prueba.** Aplicar el LHL al bloque `i`, considerando `(E,X_<i)` información lateral. La independencia de la semilla sigue siendo válida porque `S` es independiente del proceso completo. Se obtiene cercanía de `(S,E,X_<i,Y_i)` a `(S,E,X_<i,U_mi)`. Procesar `(S,X_<i)` mediante las funciones que generan `Y_<i` no aumenta TV; por tanto la misma cota vale con el prefijo de salidas real. Definir híbridos `H_i=(S,E,Y_≤i,U_>i)` para `i=0,…,t`. Las variables uniformes añadidas son independientes. Cada transición `H_i→H_(i−1)` cuesta como máximo `ε_i`. La desigualdad triangular demuestra el resultado. ∎

Esta prueba es una derivación de composición, no una atribución de ese enunciado exacto a AIS. Los bloques no necesitan ser IID ni independientes entre sí. La hipótesis condicional es exigente y suficiente, no una caracterización necesaria de todas las arquitecturas seguras.

**Caso independiente.** Si los `X_i` son independientes entre sí y de `E,S`, basta su minentropía individual. Condicionado en `S=s`, las salidas son independientes, y la cota también sigue de `TV(⊗P_i,⊗U_i)≤Σ TV(P_i,U_i)`. Si hay `E`, la independencia marginal de los `X_i` por sí sola no garantiza independencia condicionada en `E`.

**Lo que no debe hacerse.** Después de observar `Y_<i`, generalmente `S` y `X_i` ya no son independientes condicionados en ese transcript. No debe invocarse a ciegas el LHL «condicionado en las salidas previas». La prueba anterior usa `X_<i` y un híbrido que evita ese paso inválido.

La formulación habitual sobre reuso aparece en [Ma et al., 2013, sección III](https://arxiv.org/abs/1207.1473v2); su utilidad práctica depende de explicitar las hipótesis de la fuente que el resumen verbal puede ocultar. Un ejemplo experimental que contabiliza un término creciente con los usos de la semilla es [Gehring et al., 2021](https://doi.org/10.1038/s41467-020-20813-w). Aquí no se transfieren sus parámetros ni su modelo de dispositivo a otra arquitectura.

### Presupuesto de vida útil

Con `t` bloques, error total objetivo `ε_life` y costos adicionales `ε_seed, ε_model, ε_est`, una asignación suficiente es:

\[
\epsilon_i\le(\epsilon_{life}-\epsilon_{seed}-\epsilon_{model}-\epsilon_{est})/t.
\]

Con `k=1024`, `m=768`, el LHL da `ε_i=2⁻¹²⁹`; con `t=10¹²`, la suma es aproximadamente `1.47×10⁻²⁷`. Aumentar a `m=896` da `ε_i=2⁻⁶⁵`, y la suma sube a aproximadamente `2.71×10⁻⁸`. La reserva de entropía afecta el error exponencialmente.

El horizonte debe contar todos los bloques de todos los dispositivos que compartan semilla cuando se reclama una garantía conjunta para la flota. Reinstanciar el software no reinicia una prueba criptográfica. Una parada que depende del transcript exige analizar el evento de selección; una cota para un máximo fijo permite incluir un procedimiento de parada mediante procesamiento de datos, pero condicionarse en una aceptación rara puede degradar las cotas por su probabilidad.

## 5. Cuatro contraejemplos

### 5.1 Bloques idénticos: marginales casi uniformes, salida conjunta mala

Tomar `X₂=X₁=U_n`, independientes de `S`. Cada entrada tiene `n` bits de minentropía marginal, pero `Hmin(X₂|X₁)=0`. Reutilizar `S` implica `Y₂=Y₁` exactamente. El evento de igualdad tiene probabilidad uno, mientras dos salidas ideales de `m` bits coinciden con probabilidad `2⁻ᵐ`. Por tanto la distancia conjunta es al menos `1−2⁻ᵐ`.

Para una matriz fija de rango completo, cada `Y_i` es perfectamente uniforme y la distancia de la pareja es exactamente `1−2⁻ᵐ`. Esto refuta cualquier argumento que sume minentropías marginales sin controlar dependencias.

### 5.2 Fuente adaptada a una semilla pública: núcleo de la matriz

Después de observar `s`, tomar `X_s` uniforme en `ker(T_s)`. Como `rank(T_s)≤m`,

\[
H_{\min}(X\mid S=s)=n-\operatorname{rank}(T_s)\ge n-m,
\qquad T_sX_s=0.
\]

La salida tiene cero entropía aunque `Hmin(X|S)` pueda ser muy grande. Falta la independencia de `S` y `X`; no es una refutación del LHL.

Para una función determinista arbitraria `f:{0,1}ⁿ→{0,1}ᵐ`, alguna fibra contiene al menos `2^(n−m)` entradas. La fuente uniforme sobre esa fibra da salida constante. Para destruir sólo un bit basta elegir la mayor preimagen de ese bit: tiene al menos `2^(n−1)` entradas. Así, ninguna función determinista fija extrae un bit casi uniforme de **todas** las fuentes con minentropía `n−1`. Este argumento también aplica a SHA-256 fijo; no cuestiona su seguridad en modelos computacionales adecuados.

### 5.3 Independencia por pares insuficiente

Sean `A,B` uniformes independientes de `m` bits y `C=A⊕B`. Cada variable es uniforme y cada pareja es independiente. Sin embargo `A⊕B⊕C=0` siempre, frente a probabilidad `2⁻ᵐ` ideal. La distancia conjunta es `1−2⁻ᵐ` y la última variable tiene minentropía cero dado el pasado. Autocorrelaciones de orden dos no excluyen dependencia de orden superior.

### 5.4 Semilla fija de por vida no significa error constante de por vida

Sea `X_i` IID y una matriz fija produzca un bit con probabilidad `p≠1/2`. Para `t` usos, la frecuencia de unos converge a `p`, mientras en el ideal converge a `1/2`. Un distinguidor de frecuencias tiene ventaja que tiende a uno. El reuso de un extractor strong no ofrece una cota constante uniforme en un horizonte infinito.

No toda instancia empeora hasta uno: si la fuente es exactamente uniforme y la matriz tiene rango completo, sus salidas independientes son exactamente uniformes. «Siempre seguro» y «siempre inseguro» son ambos enunciados incorrectos sin modelo y horizonte.

## 6. Semillas imperfectas y cambios de familia

Si la distribución real de `S` es `δ`-cercana a uniforme e independiente de toda la fuente, se aplica el mismo canal al mundo real y al ideal. Comparando la salida real con `P_S⊗U` puede usarse la cota `2δ+ε` por triángulo directo; una cota más ajustada `δ+ε` se obtiene porque, para fuentes independientes, el error es `E_s d_s` con `0≤d_s≤1`, cuyo cambio bajo TV es como máximo `δ`. Esto se paga **una vez** para un experimento completo con semilla común cuando ya se tiene el error ideal conjunto.

Si sólo se sabe `Hmin(S)≥d−r`, entonces `p_s≤2^r/2^d` y

\[
\mathbb E_{S\,real}d_S\le2^r\mathbb E_{S\,uniforme}d_S.
\]

Es una penalización multiplicativa, no «sólo restar r bits» sin más. Con la cota de segundo momento puede mejorarse a `2^(r/2)` sobre la cota L2 original mediante Cauchy–Schwarz. Toda variante exige mantener la independencia fuente–semilla. Para correlación residual cuantificada del estado conjunto con `U_S⊗ρ_XE`, un híbrido general puede costar hasta dos veces esa distancia si se mantiene el marginal real lateral; debe especificarse el criterio exacto.

Una semilla expandida desde `r` bits por un PRG a `d≫r` bits tiene soporte como máximo `2^r`; su TV respecto de uniforme en `d` bits es al menos `1−2^(r−d)`. Puede ser computacionalmente adecuada bajo una hipótesis PRG y un modelo de fuente apropiado, pero no satisface la premisa informacional de una semilla uniforme de `d` bits.

Una semilla seleccionada por rechazo para asegurar rango completo ya no es uniforme sobre **todas** las matrices Toeplitz. En el laboratorio Monte Carlo se hace eso sólo para aislar la dependencia de bloques; no se aplica a esa familia condicionada la constante universal₂ original sin una nueva prueba.

## 7. Información lateral cuántica: qué cambia

Si `X` es clásico y `E` cuántico, la garantía adecuada usa

\[
D(\rho_{SYE},\rho_S\otimes\tau_Y\otimes\rho_E)
=\tfrac12\|\rho_{SYE}-\rho_S\otimes\tau_Y\otimes\rho_E\|_1.
\]

`Hmin(X|E)` se relaciona con la mejor probabilidad de adivinar `X` mediante una medida sobre `E`; no se obtiene automáticamente de un histograma de `X`. Universal₂ hashing es quantum-proof: para semilla uniforme independiente del estado cq y minentropía adecuada, el error no suavizado está acotado por `½2^((m−k)/2)`. La prueba de [Tomamichel, Schaffner, Smith y Renner](https://arxiv.org/abs/1002.2436) proporciona el resultado; aquí se referencia, no se reproduce su demostración matricial.

**Convenciones de suavizado.** El artículo define una distancia optimizada sobre el estado lateral. Para evitar mezclar convenciones, usamos en este dossier el marginal lateral real y una cota conservadora

\[
D_{\rm real}\le 2\eta+\tfrac12 2^{(m-H_{\min}^{\eta}(X|E))/2}.
\]

El factor `2η` procede de comparar tanto el estado cq como el marginal lateral antes/después del suavizado; no debe copiarse el `η` de una definición optimizada a otra sin comprobarla. Para estados normalizados, la prueba no suavizada sigue del argumento de norma ponderada del artículo (Lemma 4 y Theorem 6); el suavizado requiere la métrica especificada, aquí distancia purificada y estados cq subnormalizados admisibles.

El teorema de composición de §4 se extiende usando `Hmin(X_i|E,X_<i)`, canales cuánticos de procesamiento y distancia de traza, con las mismas hipótesis globales de independencia y el costo de suavizado correspondiente a cada bloque. No basta que `E` se haya medido en una base conveniente; conservar información cuántica puede mejorar la adivinación futura.

## 8. Relación con el modelo QRNG genérico

El [simulador del agente QRNG](../05_qrng_model/README.md) incluye feedback que puede imponer pares `01/10`: las marginales son equilibradas y sólo hay un bit aleatorio por pareja. El extractor debe dimensionarse contra la entropía **del bloque condicionado en la historia y en la información adversaria**, no `n` veces la entropía marginal de un bit.

Si el controlador de umbral depende sólo de datos físicos brutos y estados independientes de `S`, el feedback no destruye por sí mismo la independencia global de la semilla. Sí puede destruir IID o reducir la entropía condicional. Si el controlador recibe `Y=T_SX` o ajustes derivados de `S`, la fuente puede volverse adaptada a la semilla: hay que cambiar la prueba o utilizar semillas frescas independientes tras adquirir cada bloque.

La estacionariedad local, la mezcla rápida y una cota numérica de correlación no equivalen por sí solas a una cota de minentropía condicional. La fuente real, el controlador, el adversario y la interfaz de extracción tienen que pertenecer al mismo modelo.


### Telemetría posterior y secreto final

La [demostración transversal del coordinador](../00_coordination/feedback_leakage/README.md) prueba que, sin banda muerta ni saturación y con precisión suficiente, el transcript público de umbrales revela los conteos de las ventanas de control. Para ventana y actualización de un bit revela todos los bits. Para ventanas solapadas de tamaño fijo y actualización cada bit, la ambigüedad del bloque queda limitada por la elección de los primeros bits; la tasa de minentropía secreta puede tender a cero.

Esto no contradice una cota de impredecibilidad **causal** antes de generar el bit. La información lateral `E` del teorema de extracción debe representar lo que conoce el adversario cuando se evalúa la seguridad final, no sólo lo conocido justo antes de cada muestra. Si `E` revela `X`, ningún extractor determinista con semilla pública puede devolver secreto.
