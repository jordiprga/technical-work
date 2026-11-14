# Qué mide ENTROPY ORACLE

Este prototipo realiza ataques predictivos de un paso sobre símbolos discretos.
Una mayor precisión fuera de muestra constituye evidencia de estructura
explotable. **Un predictor entrenado no certifica una cota inferior conservadora
de la min-entropía real de una fuente.** El programa tampoco implementa una
evaluación normativa SP 800-90B o AIS 31.

## Entropías y probabilidades: objetos diferentes

Sea \(C\) el contexto observado y \(p_c(x)=P(X=x\mid C=c)\). Todos los
logaritmos de las métricas están en base dos. Definimos:

\[
H_\infty(X)=-\log_2\max_xP(X=x),\qquad
h_\infty(X\mid C=c)=-\log_2\max_xp_c(x).
\]

La segunda expresión depende del contexto particular; no es un único número
asociado a la distribución conjunta. Dos convenciones agregadas importantes son:

\[
H_\infty^{\mathrm{worst}}(X\mid C)
=-\log_2\mathop{\mathrm{ess\,sup}}_c\max_xp_c(x),
\]

\[
\widetilde H_\infty(X\mid C)
=-\log_2\mathbb E_C[\max_xp_C(x)]
=-\log_2 p_{\mathrm{guess}}^*(X\mid C).
\]

El supremo esencial excluye contextos de probabilidad cero. La segunda es la
*average conditional min-entropy*, definida mediante la probabilidad óptima de
acierto promedio. **No** equivale a
\(\mathbb E_C[-\log_2\max_xp_C(x)]\). Por Jensen, esta última cantidad es
mayor o igual que \(\widetilde H_\infty\). Además,

\[
H_\infty^{\mathrm{worst}}(X\mid C)
\leq\widetilde H_\infty(X\mid C)\leq H_\infty(X).
\]

En una fuente con marginal binaria uniforme y transición
\(P(X_t=X_{t-1})=0.99\), la min-entropía marginal es 1 bit, pero las dos
nociones condicionales anteriores valen \(-\log_2(0.99)\), aproximadamente
0.0145 bits por símbolo. Uniformidad marginal no implica independencia.

Para un proceso, la tasa de entropía de Shannon y la tasa de min-entropía de
bloques, cuando existen, son respectivamente

\[
h=\lim_{n\to\infty}\frac1nH(X_1^n),\qquad
h_\infty=\lim_{n\to\infty}-\frac1n
\log_2\max_{x_1^n}P(X_1^n=x_1^n).
\]

Son límites diferentes. En un proceso estacionario sobre alfabeto finito,
\(h=H(X_0\mid X_{-1},X_{-2},\ldots)\); no existe una identidad general
análoga que convierta una precisión de un paso, su logaritmo negativo o la media
de min-entropías puntuales en \(h_\infty\). En cadenas de Markov finitas,
las probabilidades máximas de caminos y los ciclos de máximo peso gobiernan
la tasa de min-entropía de bloques, mientras que la entropía de Shannon promedia
las transiciones con la distribución estacionaria.

## Modelo probabilístico, clasificación y log-loss

El modelo produce una masa normalizada \(q_\theta(x\mid c)\). Su decisión
determinista es \(g_q(c)=\arg\max_xq_\theta(x\mid c)\); los empates se
resuelven por el índice de símbolo más pequeño. La probabilidad real de éxito
es

\[
p_{\mathrm{succ}}(q)=P(g_q(C)=X)
=\mathbb E_C[p_C(g_q(C))]
\leq\mathbb E_C[\max_xp_C(x)]=p_{\mathrm{guess}}^*.
\]

El campo `guess_probability_model` guarda \(n^{-1}\sum_t\max_xq(x\mid C_t)\).
Es la confianza que declara el modelo. No es una probabilidad de éxito
empíricamente demostrada ni una estimación automáticamente calibrada de
\(p_{\mathrm{guess}}^*\).

La *cross-entropy* es el funcional poblacional

\[
L(p,q)=\mathbb E[-\log_2q(X\mid C)]
=H_p(X\mid C)+\mathbb E_C D_{\mathrm{KL},2}(p_C\Vert q_C).
\]

El *log-loss* de test es su promedio muestral. Cuando el contexto es una ventana
finita, el término de Shannon anterior también condiciona solamente sobre esa
ventana; puede exceder la entropía condicional dada toda la historia. Ni ese
promedio ni la cross-entropy son min-entropía. El log-loss puede mejorar sin que
cambie el argmax, y viceversa. La pérdida de Brier es
\(n^{-1}\sum_t\sum_x(q_t(x)-\mathbf1\{x=X_t\})^2\).

Para evitar infinitos en los archivos de resultados, el log-loss reportado usa
\(\max(q_t(X_t),10^{-15})\); `log_loss_clipped_count` cuenta las probabilidades
afectadas. Si ese contador es distinto de cero, la pérdida exacta puede ser mayor
o infinita. La precisión no utiliza ese truncamiento.

`empirical_predictor_surprisal_bits` es solamente
\(-\log_2(\widehat p_{\mathrm{succ}})\). Se conserva como diagnóstico de
predictibilidad, nunca como «min-entropía certificada». Cuando no hay aciertos,
el campo vale `null`, representando una cantidad infinita no informativa.

## Intervalos válidos con dependencia temporal

Antes del test se fijan los modelos, sus hiperparámetros, el checkpoint, los
pesos del ensemble y el procedimiento de comparación. Sea \(\mathcal F_{t-1}\)
la información disponible antes de observar \(X_t\), incluyendo todo el
entrenamiento, validación y el pasado ya observado del test. La predicción
\(g_t\) debe ser \(\mathcal F_{t-1}\)-medible. Definimos

\[
Z_t=\mathbf1\{g_t=X_t\},\qquad
p_t=\mathbb E[Z_t\mid\mathcal F_{t-1}],\qquad
\bar p_n=\frac1n\sum_{t=1}^np_t.
\]

\(Z_t-p_t\) es una diferencia de martingala; sus extremos condicionales son
\(-p_t\) y \(1-p_t\), cuya anchura es 1. El lema condicional de Hoeffding y
la propiedad de la torre dan

\[
\mathbb E\exp\!\left(\lambda\sum_t(Z_t-p_t)\right)
\leq\exp(n\lambda^2/8),
\]

\[
P\!\left(\left|\widehat p_n-\bar p_n\right|\geq\epsilon\right)
\leq2e^{-2n\epsilon^2}.
\]

Por tanto `success_ci_low/high` contiene

\[
\left[\widehat p_n-\sqrt{\frac{\ln(2/\alpha)}{2n}},\quad
\widehat p_n+\sqrt{\frac{\ln(2/\alpha)}{2n}}\right]\cap[0,1]
\]

con cobertura al menos \(1-\alpha\). No se requiere IID, estacionariedad ni
una estimación de «tamaño efectivo». El precio es una cota relativamente
conservadora y un objetivo preciso: **el promedio de probabilidades
condicionales a lo largo de la trayectoria de test realizada**. Ese promedio es
aleatorio. No es sin más el rendimiento poblacional en otra sesión futura,
otra temperatura o una distribución estacionaria hipotética.

La cota es de horizonte fijo. Repetirla hasta obtener significación no preserva
su cobertura; se necesitarían cotas uniformes en el tiempo o un procedimiento
secuencial válido. En particular, no es una *confidence sequence*.

Para dos predictores elegidos antes del test, se usan exactamente los mismos
índices y \(D_t=Z_t^A-Z_t^B\in[-1,1]\). La anchura es 2 y la cota bilateral
para el promedio condicional de la diferencia tiene radio

\[
\sqrt{\frac{2\ln(2/\alpha)}{n}}.
\]

Un extremo inferior positivo demuestra una ventaja en ese objetivo, al nivel
de confianza declarado. La prueba es pareada, y no consiste en comparar el
solapamiento de dos intervalos individuales. Si se inspeccionan \(m\)
comparaciones y después se anuncia la ganadora, se debe preasignar el contraste
o aplicar, por ejemplo, \(\alpha/m\). Los intervalos individuales de una tabla
no constituyen intervalos simultáneos de toda la tabla.

El intervalo de Clopper–Pearson se ofrece como función separada y no se aplica
automáticamente. Requiere indicadores de acierto IID Bernoulli con probabilidad
común; una fuente IID con predictores de ventanas solapadas no garantiza esa
hipótesis por sí sola.

## Bootstrap de bloques: diagnóstico con hipótesis adicionales

Los intervalos `bootstrap_ci_low/high` remuestrean bloques circulares del
proceso de aciertos, o de diferencias pareadas. Su semilla y longitud de bloque
son explícitas. Su justificación es asintótica bajo estacionariedad,
dependencia suficientemente débil y condiciones apropiadas de longitud de
bloque (típicamente \(\ell_n\to\infty\), \(\ell_n/n\to0\)). Un bloque fijo
de 32 no garantiza cubrir dependencias de orden superior. Se muestran como
diagnóstico exploratorio, no como garantía universal de cobertura.

En fuentes con drift, cambios de régimen no estacionarios, memoria muy larga o
pocos bloques efectivos, esos intervalos no están justificados. La cota de
martingala anterior sigue siendo aplicable al objetivo de trayectoria, siempre
que las decisiones sean predecibles. El bootstrap pareado remuestrea las
diferencias completas, preservando el emparejamiento de los modelos.

## Qué dirección tienen las cotas sobre entropía

Si se obtiene una cota inferior \(L\) de la probabilidad de éxito de un
predictor, la desigualdad \(p_{\mathrm{guess}}^*\geq p_{\mathrm{succ}}(q)\)
implica

\[
-\log_2p_{\mathrm{guess}}^*\leq-\log_2L.
\]

Es una **cota superior** sobre la min-entropía condicional promedio pertinente:
evidencia de que un adversario puede acertar al menos tanto. Cuando se utiliza
la cota de martingala, la interpretación directa es la misma desigualdad para
\(n^{-1}\sum_t\max_xP(X_t=x\mid\mathcal F_{t-1})\), a lo largo de la
trayectoria; identificarla con una esperanza estacionaria requiere argumentos
adicionales.

Una cota superior del éxito de un predictor imperfecto no acota superiormente
el éxito óptimo. Por ello no produce una cota inferior sobre min-entropía. Esta
inferencia solo sería válida tras demostrar que el predictor es óptimo para el
modelo de fuente e información lateral considerado, o mediante otras
restricciones demostradas sobre la clase completa de adversarios/fuentes.
Fracasar en aprender dependencias tampoco demuestra su ausencia. Las fuentes
físicas requieren además justificar el modelo estocástico, el acceso del
adversario y la información lateral relevante.

## Separación temporal y selección adversarial

Las fronteras train/validation/test son temporales. Solo el train ajusta pesos,
conteos y transformaciones; la validación selecciona checkpoints, el predictor
y la combinación probabilística. El test final no participa en esas decisiones.
Una ventana de test puede contener símbolos previos de validación o del propio
test, pues ya son observables cuando se predice el símbolo siguiente. Nunca
puede contener ese símbolo objetivo ni símbolos futuros.

«Test independiente» significa aquí independiente del procedimiento de
selección, no que sus observaciones sean probabilísticamente independientes
del train o entre sí. La dependencia restante está contemplada en la cota de
martingala. Seleccionar el mejor modelo en validación y evaluar esa regla fijada
en test evita el sesgo de seleccionar el ganador por sus aciertos de test.
Comparar exploratoriamente todas las filas de test sigue requiriendo atender a
la multiplicidad al formular conclusiones.

Las múltiples semillas describen variabilidad por realizaciones y por ajuste;
una desviación estándar entre tres semillas no se convierte automáticamente en
un intervalo de confianza preciso. Las curvas de aprendizaje deben usar
prefijos de entrenamiento y conjuntos posteriores fijos; no deben utilizarse
para ajustar retrospectivamente decisiones sobre un test que luego se presente
como confirmatorio.

## Relación experimental con SP 800-90B

Los métodos de frecuencia, Markov, PPM y memoria de esta aplicación exploran
familias de dependencias relacionadas con los predictores MultiMCW, Lag,
MultiMMC y LZ78Y de la suite no-IID. Esa relación es conceptual y experimental.
Aquí no se reproducen sus especificaciones exactas, reglas de desempate,
actualización online, estadísticos globales/locales, correcciones normativas ni
requisitos de longitud y tratamiento del alfabeto. Tampoco se ejecuta una
batería AIS 31.

Para comparar con una herramienta normativa hay que ejecutar su implementación
validada sobre la misma secuencia y documentar versión, parámetros y condiciones
de uso. Un predictor PPM o un modelo de compresión genérico no es LZ78Y. Las
tasas asintóticas de compresión universal se relacionan principalmente con
entropía de Shannon bajo sus propias hipótesis; no son certificados generales
de min-entropía.

Los oráculos sintéticos deben distinguir condicionales dados símbolos
observados de condicionales con acceso a estados latentes. Una referencia que
conoce el estado continuo exacto previo de un AR(1) cuantizado tiene información
privilegiada y no es necesariamente alcanzable por un predictor que solo ve
bins. La coincidencia con un oráculo simulado valida el experimento bajo ese
modelo, no la adecuación del modelo a un TRNG físico.
