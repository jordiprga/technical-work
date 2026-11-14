# Modelo estocástico y demostraciones

Fecha: 2026-11-14. Las demostraciones de este documento son analíticas; no han sido formalizadas en Lean. El código verifica casos numéricos y contraejemplos finitos. La física se representa mediante hipótesis explícitas.

## 1. Variables, causalidad e información lateral

Sea `Xₜ = A cos(Φₜ) + Cₜ`, `A>0`, y `Bₜ = 1{Xₜ>θₖ}` durante el intervalo de control k. Las unidades de amplitud son arbitrarias. `Cₜ` es ruido clásico más un offset/deriva opcional; se trata como información revelada al adversario en el cálculo condicional. La fase se genera mediante dos modelos alternativos:

1. **Fase IID**: `Φₜ ~ Unif(-π,π]` independientes de todo el pasado, del ruido clásico y del controlador. Esta es una hipótesis sobre el proceso latente. Los bits producidos con feedback no se presuponen IID.
2. **Difusión circular**: `Φₜ = wrap(Φₜ₋₁ + Δₜ)`, con `Φ₀` uniforme y `Δₜ ~ N(0,sφ²)` independientes. La distribución marginal de la fase sigue siendo uniforme exactamente: una traslación aleatoria de una variable uniforme en el círculo es uniforme. Sin embargo, `E[cos Φₜ cos Φₜ₊ₗ] = (1/2) exp(-ℓ sφ²/2)`. Esto se obtiene usando `E[e^{iΔ}]=exp(-sφ²/2)` y la ortogonalidad de Fourier. Por tanto un histograma arcsine no distingue estas dos dinámicas.

El ruido gaussiano sigue `Nₜ = ρNₜ₋₁ + σ√(1-ρ²) Zₜ`, `|ρ|<1`, inicializado con `N₋₁~N(0,σ²)`. Así cada marginal es `N(0,σ²)` y `Cov(Nₜ,Nₜ₊ₗ)=σ²ρ^ℓ`. La secuencia de fases y el ruido usan flujos de PRNG independientes en el simulador. `Cₜ=Nₜ+offset+D sin(2πt/P)`.

El estado completo contiene fase, ruido, umbral, ventana de bits y fase del reloj de control. Ignorar cualquiera de estas memorias no convierte el proceso observado en IID. El umbral es una función determinista del historial y de la configuración. Las métricas numéricas revelan el estado causal actual, pero EXCLUYEN el transcript futuro de control. Revelar después todos los umbrales puede filtrar los bits ya generados: véase la sección 9. No debe confundirse una predicción causal con seguridad offline.

## 2. Arcsine, convolución y comparador

Para `Q=A cos Φ`, fase uniforme,

`f_Q(x)=1/[π√(A²-x²)]` para `|x|<A`, y cero fuera.

Prueba: cada `x` interior tiene dos preimágenes por periodo; el jacobiano absoluto es `A|sin Φ|=√(A²-x²)`. Sumando ambas densidades uniformes se obtiene la expresión. `E[Q]=0`, `Var(Q)=A²/2`.

Si `N` es gaussiano independiente, `f_X=f_Q * φσ`, incluso cuando las muestras de Q o N tienen correlación temporal. Es una afirmación de **distribución marginal**. El código integra en fase, evitando evaluar la singularidad de la densidad arcsine:

`f_X(x) = (1/2π)∫₀²π φσ(x-A cos φ) dφ`.

Con fase IID, ruido clásico revelado `c` y umbral público θ:

`p(c,θ)=Pr(B=1|C=c,θ)=arccos(clip((θ-c)/A,-1,1))/π`.

En θ=0, la densidad marginal centrada tiene expresión `f_X(0)=exp(−a) I₀(a)/(σ√(2π))`, con `a=A²/(4σ²)`. Se obtiene escribiendo `cos²φ=(1+cos2φ)/2`. El código usa la función Bessel escalada `i0e`, evitando problemas de resolución de la cuadratura para σ muy pequeño; en σ=0 usa `1/(πA)`. La cuadratura de la densidad completa sigue siendo numérica y requiere aumentar nodos si se cambia mucho la escala de parámetros.

Esta fórmula acredita sólo la incertidumbre del componente de fase supuesto independiente. La probabilidad marginal del comparador, integrando también ruido clásico desconocido, sería distinta y podría sobreestimar el recurso útil ante quien conoce C.

Para difusión circular se evalúa adicionalmente un adversario que conoce `Φₜ₋₁`. Si `α=arccos(clip((θ-c)/A,-1,1))` y `μ=Φₜ₋₁`,

`p = Σⱼ [ ΦN((α+2πj-μ)/sφ) − ΦN((-α+2πj-μ)/sφ) ]`.

La suma se trunca más allá de diez desviaciones típicas. Las pruebas la contrastan con Monte Carlo y con el límite uniforme. Este adversario es más fuerte que uno que sólo ve bits; el cálculo no es un análisis general de información lateral cuántica.

## 3. Ley de control y orden causal

Sea U el número de muestras entre actualizaciones y W el número de bits de la ventana. El umbral se mantiene constante durante U muestras. Después de producir el último bit del intervalo, se calcula

`eₖ = (1/W) Σ últimos W bits − q`.

Si la ventana está completa:

`θₖ₊₁ = clip(θₖ + g eₖ 1{|eₖ|>d}, -L, L)`.

Si todavía no hay W bits, no se actualiza. g es ganancia **por actualización**, d la banda muerta en fracción de unos y L el límite del actuador. La decisión actual no utiliza muestras futuras. Aumentar θ reduce la probabilidad de 1; el signo positivo corrige exceso de unos.

Cambiar U manteniendo g modifica el ancho de banda en unidades de tiempo físico. No es una comparación a igual ancho de banda. Para aproximar un integrador continuo de ganancia κ con frecuencia de muestreo `fs`, la ganancia discreta escala como `g≈κU/fs`. La comparación debe declarar qué magnitud permanece constante.

## 4. Linealización para ventanas independientes

**Supuestos de esta sección:** fase IID, ruido clásico blanco independiente, offset cero, sin deriva ni banda muerta, q=1/2, θ cerca de cero, actuador lejos de los límites, W=U. Sea `f=f_X(0)>0`, `a=gf`, `ηₖ` el error de estimación a umbral cero con varianza aproximada `s²=q(1-q)/W`.

La expansión `p(θ)=1/2-fθ+O(θ³)` produce

`eₖ≈-fθₖ+ηₖ`, `θₖ₊₁≈(1-a)θₖ+gηₖ`.

**Resultado local:** el equilibrio de la dinámica media lineal es asintóticamente estable si y sólo si `0<a<2`. El tiempo de relajación en muestras es aproximadamente `-U/log|1-a|` cuando `a≠1`; para a pequeño, `U/a`.

Si además se usa la aproximación de innovaciones blancas,

`Var(θ)≈g²s²/[1-(1-a)²]=g q(1-q)/[W f(2-a)]`.

La salida por bloques no queda independiente. Sustituyendo el estado:

`eₖ=(1-Lag)/(1-(1-a)Lag) ηₖ`.

De aquí, para ℓ≥1,

`Cov(eₖ,eₖ₊ₗ)≈-[a s²/(2-a)](1-a)^{ℓ-1}`,

`Var(eₖ)≈2s²/(2-a)`,

`Corr(eₖ,eₖ₊ₗ)≈-(a/2)(1-a)^{ℓ-1}`.

La anticorrelación entre bloques es una consecuencia del control. Una prueba de frecuencia de largo plazo puede mejorar precisamente porque el controlador suprime la componente de frecuencia cero. Esto no demuestra mayor entropía por bit.

**Límite decisivo:** la estabilidad local no garantiza estabilidad global, jitter pequeño ni seguridad. Para arcsine la densidad crece al acercarse a los extremos; excursiones grandes pueden salir de la región donde la pendiente f(0) describe la respuesta. El experimento g=5 exhibe una discrepancia material respecto de la predicción lineal.

## 5. Ventanas solapadas y retardo

Para W=KU con K entero, la ventana contiene K intervalos completos. Bajo los mismos supuestos locales,

`θₖ₊₁ = θₖ − (a/K) Σⱼ₌₀^{K−1} θₖ₋ⱼ + ruido`.

El polinomio característico es

`λᴷ−λᴷ⁻¹+(a/K)(λᴷ⁻¹+…+λ+1)=0`.

El código calcula todas las raíces; radio espectral <1 significa estabilidad de esta linealización. Para hallar el primer cruce del círculo unidad, fijar `λ=e^{iω}` en

`λ−1=−(a/K)Σⱼ₌₀^{K−1} λ^{−j}`.

Usando la suma geométrica, la primera solución con ganancia positiva tiene `ω=π/K` y

`a_crit=2K sin²(π/(2K))`.

Para K=1 resulta 2; K=4, 1.1716; K=16, aproximadamente 0.3074. Para K grande, `a_crit≈π²/(2K)`. La estabilidad estricta de esta dinámica lineal se cumple **si y sólo si** `0<a<a_crit`. En a=0 existe una raíz 1; en a=a_crit existen raíces de módulo uno, de modo que no hay estabilidad asintótica estricta.

Para completar la prueba, en a=0 las otras K−1 raíces están en cero; para a positivo pequeño todas quedan dentro del disco y la raíz próxima a 1 se desplaza como `1−a+O(a²)`. En el círculo unidad, el valor necesario de la ganancia se escribe

`a=2K sin²(ω/2)[1−i cot(Kω/2)]`.

Por tanto los cruces con ganancia real positiva ocurren en `ω=(2r+1)π/K`; el primero tiene el menor valor de a. Los puntos donde la suma geométrica se anula no resuelven la ecuación, y z=1 no es raíz para a>0. No hay reentrada posterior que cree otra zona estable: poniendo `w=log z`, en un cruce se verifica `Re(da/dw)=aK/2>0`, porque la parte real de la media geométrica ponderada de índices es `(K−1)/2`. Entonces `Re(dw/da)=Re(da/dw)/|da/dw|²>0`; el módulo de cada raíz que cruza aumenta con a. Esta argumentación incluye z=−1 cuando corresponde. Las raíces numéricas son una verificación independiente de casos finitos, no la base de la afirmación general.

No se aplica esta fórmula cuando W/U no es entero ni a controladores que actualicen una estimación analógica distinta de la ventana de bits. El simulador admite esos cocientes, pero omite la fórmula correspondiente.

## 6. Banda muerta, límites y estacionariedad

En la dinámica media sin ruido, una banda muerta permite cualquier umbral cuyo `|p(θ)-q|≤d`. Cerca del equilibrio, la incertidumbre de umbral permitida es aproximadamente `d/f`. No fuerza un sesgo persistente igual a d: con ruido, el umbral puede seguir moviéndose. Reduce actualizaciones pequeñas, pero puede conservar offsets residuales y cambiar el tiempo de recuperación.

Limitar θ evita divergencia numérica, pero puede crear periodos en saturación. No demuestra calidad de salida. Para parámetros constantes, fases/ruido estacionarios y reloj fijo de actualización, el proceso ampliado a escala de bloques es homogéneo; el proceso por muestras puede ser ciclostacionario con periodo U. Inicializar θ=0 normalmente no equivale a inicializar la distribución invariante del controlador.

En dominios compactos para los componentes de control y bajo regularidad apropiada puede investigarse existencia de una distribución invariante. Aquí **no se demuestra** unicidad, velocidad de mezcla ni ergodicidad del proceso completo. Burn-in y comparación de tramos son diagnósticos. La deriva sinusoidal introduce dependencia explícita del tiempo: sólo al incluir su fase como estado se obtiene un sistema homogéneo ampliado. Una deriva no periódica puede impedir una distribución estacionaria adecuada.

## 7. Entropías: cantidades que no deben confundirse

Se calculan cantidades distintas:

- `−log₂ max(p̂,1−p̂)`: min-entropía marginal empírica; ignora historial e información lateral.
- `−log₂ E[max(p(Z),1−p(Z))]`: min-entropía condicional promedio de **un símbolo** frente al estado causal Z, excluyendo umbrales futuros. La expectativa se aproxima por Monte Carlo; no lleva cota estadística conservadora.
- `E[−log₂ max(p(Z),1−p(Z))]`: media de min-entropías puntuales, diferente de la anterior; por Jensen es mayor o igual.
- `E[h₂(p(Z))]`: entropía condicional Shannon de un paso bajo el modelo.
- `−log₂ max_{bⁿ} Pr(Bⁿ=bⁿ)`: min-entropía conjunta de un bloque, calculada sólo por enumeración para el ejemplo pequeño sin ruido.

Las claves del código usan `model_causal_sideinfo_*` para explicitar que no se incluye el transcript futuro. La media temporal del primer cálculo condicional puede describir un índice temporal elegido al azar bajo el modelo. No debe multiplicarse sin más por n para obtener una cota de min-entropía de bloque. Si existe una cota uniforme `max_b Pr(Bₜ=b|B<t,E)≤rₜ` para **todo historial e información lateral permitidos**, entonces la regla de la cadena de probabilidades demuestra `Pr(Bⁿ=bⁿ|E)≤∏rₜ` y la correspondiente cota `Hmin≥Σ−log₂rₜ`. Esto requiere un modelo del condicionamiento completo y cotas uniformes, no promedios observados.

Con ruido gaussiano clásico revelado de soporte no acotado, puede haber valores de C que hagan un comparador determinista aunque θ sea acotado. Una cota uniforme puntual positiva en todos los valores de C no se obtiene de este modelo. Esto no implica que la min-entropía condicional **promedio** deba ser cero: si C se distribuye según la ley legítima supuesta, los valores extremos pueden tener poco peso. Un adversario que conoce C es distinto de uno que puede fijarlo arbitrariamente sin límites; este último podría forzar determinismo. Puede emplearse una región de buena operación con probabilidad de fallo explícita, o una formulación de entropía suave/promedio adecuada; hay que contabilizar la cola y demostrar la composición que se utilice.

## 8. Contraejemplo exacto: balance perfecto con media tasa de entropía

Tomar A=1, C=0, fase IID uniforme, W=U=1, g=2, θ₀=0, q=1/2, banda muerta cero y límites al menos ±1.

En θ=0 el bit es uniforme. Si B=1, el umbral siguiente es +1 y el siguiente bit es 0 con probabilidad uno; si B=0, el umbral es −1 y el siguiente bit es 1 con probabilidad uno. En ambos casos el umbral vuelve a cero. Los extremos `cos Φ=±1` tienen medida cero y no alteran la afirmación.

Por inducción, cada par es 01 o 10 equiprobable, y los pares son independientes. Cada bit marginal tiene exactamente p=1/2. Para n=2m existen `2^m` palabras equiprobables, así que

`Hmin(B¹…B²ᵐ)=m`.

La tasa es 1/2 bit por muestra, aun con balance marginal perfecto. En los pasos alternos, las probabilidades óptimas de acierto son 1/2 y 1; la min-entropía condicional promedio de un paso con fase de reloj revelada es `−log₂(3/4)≈0.415`, mientras que la media de min-entropías puntuales es 1/2. Ninguna igualdad accidental entre métricas debe asumirse en otros modelos.

La enumeración del código recorre todos los caminos de hasta 16 bits y verifica las marginales y la probabilidad máxima. El argumento inductivo demuestra el resultado para todo m.

## 9. Fuga por el transcript del controlador

**Advertencia matemática, no detalle de implementación:** que `θₖ` sólo dependa del pasado no significa que divulgar `θₖ₊₁` preserve la incertidumbre del bloque k. Sin banda muerta ni saturación y con g conocido no nulo,

`countₖ = W [ q + (θₖ₊₁−θₖ)/g ]`.

Un adversario que recibe después el transcript de umbrales aprende el número exacto de unos de cada ventana, en el modelo de precisión exacta. Para W=U=1, aprende **cada bit**. Entonces `Hmin(Bⁿ | θ₀,…,θₙ)=0`, incluso cuando un predictor que sólo conoce el umbral actual asignaba probabilidad 1/2 al bit antes de verlo. El ejemplo de pares mantiene `Hmin(Bⁿ)=n/2` sin transcript; con la traza completa de control, la entropía condicional es cero.

Para W=U>1 cada ventana tiene W+1 cuentas posibles. La secuencia de umbrales puede filtrar hasta `log₂(W+1)` bits por actualización como cota de alfabeto; esto no significa que siempre filtre exactamente esa cantidad. En el caso especial de bits IID uniformes y una cuenta revelada c, el bloque es uniforme sobre `binom(W,c)` secuencias. Al promediar sobre c, `Pguess(B^W|count)=(W+1)/2^W`, de modo que la min-entropía condicional promedio es exactamente `W−log₂(W+1)`. Este cálculo no se transfiere a bloques con feedback interno o dependencia sin rederivarlo.

Banda muerta, clipping o cuantización del DAC pueden reducir la resolución de la fuga; siguen revelando eventos y restricciones. No se supone que la eliminen. Si el controlador y su telemetría permanecen internos al perímetro protegido, el modelo de amenaza debe documentarlo y considerar canales laterales. Si se publican, la extracción debe condicionarse al transcript completo, no sólo a variables causales. La revisión de coordinación desarrolla esta distinción transversal.

## 10. Una familia con tasa de min-entropía calculable

[finite_state_analysis.py](finite_state_analysis.py) estudia W=U=1, C=0, fase IID, θ₀=0, banda muerta cero y sin divulgación del transcript. Es un caso idealizado más estrecho que el simulador general, pero permite calcular una auténtica tasa de bloque.

Sea `δ=g/2` y `R=ceil(A/δ)`. Los estados alcanzables son `θᵢ=iδ`, `i=−R,…,R`; los extremos tienen probabilidad de retorno uno. En cada estado,

`pᵢ=arccos(clip(iδ/A,−1,1))/π`,

con transición a `i+1` para bit 1 y a `i−1` para bit 0. La cadena es finita, irreducible y de periodo 2; no converge en distribución desde θ₀ fijo a una única distribución estacionaria por simple transcurso del tiempo. Sí tiene una distribución invariante única π, y los promedios de ocupación convergen bajo el teorema de cadenas finitas irreducibles. El periodo debe preservarse en los diagnósticos.

La distribución invariante satisface balance detallado,

`πᵢ₊₁/πᵢ=pᵢ/(1−pᵢ₊₁)`.

La tasa Shannon es `Σᵢπᵢ h₂(pᵢ)`. Para la tasa de min-entropía, cada palabra de bits determina una única trayectoria desde θ₀ y tiene probabilidad producto de las probabilidades de sus aristas. Todo ciclo simple de este grafo lineal tiene dos aristas. Su producto es `pᵢ(1−pᵢ₊₁)`.

**Teorema para este modelo:**

`limₙ Hmin(B¹…Bⁿ)/n = −(1/2) log₂ maxᵢ [pᵢ(1−pᵢ₊₁)]`.

Demostración: una trayectoria larga se descompone en ciclos y un camino simple residual de longitud acotada por el número de estados. La media del logaritmo de su probabilidad no puede exceder el máximo promedio de ciclo, salvo un término O(1/n). A la inversa, desde θ₀ se llega al ciclo óptimo en tiempo finito y se repite; el prefijo y una posible arista residual contribuyen O(1/n). Ambas cotas tienen el mismo límite. No se sustituye una suma de probabilidades por un máximo: el programa usa programación dinámica de máxima probabilidad por palabra y la contrasta con enumeración exhaustiva pequeña.

Por simetría, las marginales de B son exactamente uniformes en cada tiempo para todas estas ganancias. Aun así, para A=1 se obtienen:

| g | Estados | Tasa Hmin | Tasa Shannon |
|---:|---:|---:|---:|
| 0.10 | 41 | 0.977387 | 0.988177 |
| 0.25 | 17 | 0.944627 | 0.968619 |
| 0.50 | 9 | 0.892402 | 0.924042 |
| 1.00 | 5 | 0.792481 | 0.792481 |
| 1.50 | 5 | 0.688585 | 0.774026 |
| 2.00 | 3 | 0.500000 | 0.500000 |
| 3.00 | 3 | 0.500000 | 0.500000 |

Los números son evaluaciones en coma flotante de fórmulas analíticas; no tienen certificación de redondeo mediante aritmética de intervalos. Si se divulga el transcript, la tasa condicional pasa a cero, como se demostró en la sección 9.

## 11. Coexistencia no lineal: por qué la prueba local no basta

[nonlinear_bifurcation.py](nonlinear_bifurcation.py) reemplaza la estimación de frecuencia por su expectativa condicional y estudia el mapa determinista `F_g(θ)=θ+g[p(θ)−1/2]`, para W=U, sin banda muerta y sin saturación. Es el mapa de deriva condicional; **no** se afirma que `E[θₖ₊₁]=F_g(E[θₖ])` para el proceso aleatorio.

Por simetría, un ciclo `+u,−u` satisface

`g(u)=2u/[1/2−p(u)]`, `u>0`.

Su multiplicador de dos pasos es `[1−g f_X(u)]²`; es localmente estable si dicho valor es menor que uno. El equilibrio cero, por separado, es localmente estable para `g<2/f_X(0)`.

Para A=1 y σ=0.15, una minimización numérica de g(u) y búsqueda de raíces dan:

- nacimiento de dos ciclos simétricos cerca de `g=4.660605`, amplitud `u=1.043167`;
- pérdida de estabilidad local del equilibrio cero cerca de `g=6.209405`;
- para g=5, ciclo interior inestable de amplitud 0.851462 y multiplicador 4.158818; ciclo exterior estable de amplitud 1.234763 y multiplicador 0.311950.

Así, el mapa determinista tiene una región de coexistencia entre el equilibrio nominal estable y una oscilación estable de gran amplitud. Las fluctuaciones de una ventana finita pueden desplazar al sistema entre regiones de atracción; esta es una explicación mecanística compatible con la dispersión del experimento g=5. **No se ha calculado** el tiempo de primer escape, la distribución estacionaria ni una ley de transición entre regímenes.

La identificación de esos valores es numérica con cuadratura de 4096 fases y aritmética de doble precisión. Se conservan las raíces, multiplicadores y parámetros en [nonlinear_bifurcation.json](results/nonlinear_bifurcation.json). Los tests verifican que las raíces de g=5 cumplen `F_g(u)=−u` y que sus multiplicadores están a lados opuestos de uno. La clasificación del nacimiento como saddle-node describe la geometría observada de la curva; no es una prueba formal de todas las condiciones de no degeneración.

La [figura de bifurcación](figures/nonlinear_bifurcation.png) permite escoger márgenes de investigación más informados que una sola ganancia crítica en θ=0. Su uso fuera de este modelo requeriría reestimar la distribución y el mapa del actuador.
