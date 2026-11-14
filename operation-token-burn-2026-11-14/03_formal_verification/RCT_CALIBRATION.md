# Lógica correcta no equivale a calibración probabilística correcta

Los teoremas Lean de este paquete prueban cuándo se activa un RCT y qué salidas se inhiben. Elegir el umbral C requiere otra obligación: modelar la probabilidad de rachas bajo la fuente nominal y distinguir una ventana de toda la vida operativa.

## Cota suficiente sin presuponer IID

Supóngase que para toda historia de probabilidad positiva y cada valor binario b:

\[
P(B_t=b\mid B_{<t}=h)\le q=2^{-k}.
\]

Para una ventana de C posiciones, después del primer bit quedan C−1 coincidencias que deben ocurrir. Por la regla de la cadena y la hipótesis condicional, la probabilidad de racha es como máximo `q^(C−1)`. No se necesita independencia: se necesita la cota **condicional uniforme sobre las historias**. Una cota de min-entropía marginal por muestra no basta.

En n muestras existen como máximo n−C+1 ventanas candidatas. Aunque se solapan, la unión de eventos da:

\[
P(\text{alguna alarma RCT en }n)\le
\min\{1,\max(0,n-C+1)q^{C-1}\}.
\]

Esta cota suele ser conservadora porque rachas largas generan ventanas solapadas dependientes. No se debe multiplicar probabilidades de ventanas como si fueran independientes.

Contraejemplo a usar sólo marginales: elegir un bit uniforme Z y producir `B_t=Z` siempre. Cada muestra tiene un bit de min-entropía marginal, pero la alarma ocurre con probabilidad uno al alcanzar C. Después de observar el primer bit, la min-entropía condicional de los siguientes es cero.

## Modelo IID de referencia calculado exactamente

`rct_risk.py` mantiene la masa de probabilidad de cada estado vivo `(último_bit, longitud_de_racha)` y absorbe la masa que alcanza C. Usa `Fraction`; no es Monte Carlo ni estima parámetros. Su único modelo de entrada es Bernoulli IID con p explícito.

| n | C | p(1) | Probabilidad de al menos una alarma | Cota por unión |
|---:|---:|---:|---:|---:|
| 21 | 21 | 1/2 | 0.000000953674 | 0.000000953674 |
| 1024 | 21 | 1/2 | 0.000479111171 | 0.000957489014 |
| 4096 | 21 | 1/2 | 0.001942195543 | 0.003887176514 |
| 1024 | 11 | 3/5 | 0.782385838769 | 1 |

El ejemplo C=21, fuente binaria uniforme, corresponde a `q^(C−1)=2^-20` para una ventana. Eso **no** hace que la probabilidad acumulada en 1024 muestras sea 2^-20. La probabilidad exacta del RCT solo es aproximadamente 4.79×10^-4. Un startup completo con más pruebas tiene otra probabilidad conjunta que aquí no se calcula.

La cuarta fila ilustra sensibilidad a parámetros; no propone C=11 como configuración normativa para p=3/5.

## Interpretación y uso

SP 800-90B §4.4.1 relaciona umbral, entropía y probabilidad de falso positivo para su RCT. Un expediente debe conservar el significado exacto del parámetro, la frecuencia de muestras y la política ante alarmas. Esta nota no sustituye la fórmula normativa ni prescribe cambiarla; muestra por qué un riesgo por ventana y un riesgo acumulado son magnitudes distintas. [NIST SP 800-90B](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/nist.sp.800-90b.pdf).

Para una vida finita y una cota condicional válida, puede usarse la unión para presupuestar el riesgo de cualquier alarma. Para operación indefinida de una fuente IID no degenerada, toda racha finita aparece eventualmente con probabilidad uno: considerar bloques disjuntos ya basta para ver que la probabilidad de no observarla tiende a cero. Un diseño debe tratar disponibilidad, recuperación y persistencia de fallos explícitamente.

La calibración no demuestra que una fuente sea segura: una secuencia determinista alternante no activa un RCT con C≥2. Tampoco demuestra que el ruido físico mantenga la cota condicional usada. La verificación formal controla la implementación del test; el análisis estocástico justifica sus hipótesis; las mediciones confrontan el modelo con el dispositivo.

## Reproducción

```sh
python3 -m unittest -v test_rct_risk.py
python3 rct_risk.py
```

Seis tests contrastan la recurrencia con enumeración independiente por ventanas para 81 combinaciones, verifican fórmulas de borde, determinismo, cota de unión y rechazo de probabilidades flotantes. `results/rct_risk.json` conserva probabilidades racionales exactas y representaciones decimales.

Clasificación: derivación matemática propia + cálculo finito exacto + tests ejecutados. No se ha mecanizado esta parte probabilística en Lean.
