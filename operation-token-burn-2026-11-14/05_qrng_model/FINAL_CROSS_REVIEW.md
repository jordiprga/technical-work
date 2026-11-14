# Segunda revisión independiente: fuga y certificados numéricos

Revisor: misión 05, 14 de noviembre de 2026, 11:53–11:57 UTC. Revisión de lectura y ejecución; no se modificaron archivos de las otras misiones. No es una prueba formal de Python ni una evaluación de un producto.

## Dictamen

No se encontró un error matemático en las fórmulas de fuga ni en las cotas racionales del certificado Markov entregado. Se encontraron dos fronteras de API en el módulo de intervalos; fueron comunicadas al propietario de la misión 04, corregidas por él y verificadas de nuevo durante esta revisión.

## Fuga por telemetría

Revisados [README de coordinación](../00_coordination/feedback_leakage/README.md), [leakage.py](../00_coordination/feedback_leakage/leakage.py) y su suite. Los nueve tests pasaron en una ejecución independiente.

- La recuperación de cuentas a partir de diferencias de umbral es una identidad para el controlador especificado: ganancia conocida no nula, ausencia de clipping/banda muerta, umbrales consecutivos observables y ventana conocida. No necesita IID.
- La fórmula `W−log₂(W+1)` usa correctamente min-entropía condicional promedio y bits uniformes de referencia. El documento distingue explícitamente ese canal de divulgación de una fuente realimentada que podría no ser IID.
- Para U=1, el argumento de soporte de como máximo `binom(W,c₀)` candidatos es correcto; limita la entropía residual a W bits para cualquier distribución compatible. La reconstrucción implementa la recurrencia sin enumerar 2ⁿ palabras.
- Para U divisor de W, la cota sobre cardinalidad de transcripts y la tasa asintótica `1−log₂(U+1)/U` son correctas bajo la hipótesis de palabras uniformes y n múltiplo de U. Las hipótesis se explicitan.
- La generalización con información lateral previa es para min-entropía condicional promedio clásica. No se afirma aquí un teorema de información cuántica a partir del experimento clásico.

**Cuantización: precisión suficiente no equivale a precisión infinita.** Si cada valor publicado de θ tiene error absoluto como máximo ε, la cuenta inferida por diferencias tiene error como máximo `2Wε/g`. La condición suficiente `ε<g/(4W)` permite recuperar la cuenta entera por redondeo. Si la telemetría se redondea al más cercano con paso Δ, basta `Δ<g/(2W)`. Estas son condiciones suficientes, no necesarias: una traza larga podría revelar cuentas incluso con menor resolución, según el modelo. El error de ganancia/objetivo añadiría otros términos.

Esto modela cuantización **de la observación**. Si también se cuantiza el actuador, cambia la ley de actualización y hay que incorporar ese cambio antes de invertirla. La advertencia del README sobre cuantización, clipping y banda muerta es correcta; no afirma seguridad automática por introducirlos.

El código `count_transcript` inicia la primera ventana en W y después avanza U. El simulador QRNG actualiza en múltiplos de U una vez disponible una ventana completa. Las planificaciones coinciden para los casos tratados en los teoremas y tablas, donde U divide W; no debe suponerse esa coincidencia para cualquier W/U sin alinear el reloj inicial.

## Certificado de intervalos Markov

Revisados [interval_markov.py](../04_extractors_entropy/interval_markov.py), sus pruebas y [el certificado](../04_extractors_entropy/results/interval_markov_certificate.json).

El objeto acotado es `sup_(a,b en caja) max_y P(Y=y)` para una matriz fija y un modelo binario Markov con distribución inicial `(1/2,1/2)`. La caja es sintética. No es automáticamente un intervalo de confianza obtenido de datos, una cadena estacionaria —a y b no son iguales— ni una cota condicionada a información lateral adicional que revele el estado inicial.

La aritmética intervalar natural puede ser ancha por reutilizar parámetros; esto reduce precisión, pero no invalida el encierro. Las multiplicaciones consideran todos los signos; la inversión de Walsh combina intervalos de forma conservadora. Fijar el coeficiente de frecuencia cero a uno es correcto por normalización. Intersectar las probabilidades con [0,1] es válido.

La partición se reconstruye con una regla de bisección determinista. Rutas binarias sin prefijos y suma de Kraft igual a uno cubren el dominio; los solapamientos en las fronteras no perjudican la cota superior. El máximo de las cotas superiores de las hojas acota el supremo global. Un punto testigo dentro de la caja aporta una cota inferior; no es necesario que siga siendo el centro de una hoja final después de subdividir.

**Resultado reproducido:** 201 hojas, separación entre cotas de probabilidad aproximadamente 0.00099250369024. Las transformaciones logarítmicas mostradas son aproximadas: la min-entropía mínima sobre la caja queda entre aproximadamente 1.49177259 y 1.49580516 bits. La garantía exacta corresponde a las fracciones racionales de probabilidad, no a todos los decimales impresos.

### Hallazgos corregidos durante la revisión

1. La primera versión de `Interval` aceptaba `float` pese a describirse como racional exacta. Se reprodujo un resultado cuyos extremos eran `float`. **Corregido por misión 04:** los extremos y escalares aceptan únicamente `int` o `Fraction`, convierten enteros a fracción y rechazan flotantes y booleanos. Se comprobó el rechazo independiente de `0.1` y `True`.
2. La primera versión de `verify` verificaba las cotas exactas pero ignoraba los campos de entropía destinados a presentación. Se reprodujo `verified=True` después de cambiar un campo a 999. El certificado racional original seguía siendo correcto; el problema era el alcance ambiguo de verificación del JSON. **Corregido por misión 04:** el verificador exige esquema 1, recalcula los logaritmos, exige finitud y concordancia dentro de 1e−12 y devuelve sus propios valores. La mutación a 999 fue rechazada después del cambio. El campo de texto `meaning` queda explícitamente informativo.

No se ha auditado resistencia frente a consumo adversarial de recursos con certificados gigantes ni toda la superficie de errores de tipos. El resultado está preparado como artefacto de investigación pequeño con entradas controladas, no como servicio que acepte archivos arbitrarios de Internet.

## Trazabilidad de la revisión

Hashes SHA-256 de los archivos de código verificados a las 11:56 UTC:

- `interval_markov.py`: `289d86dd9e3186ca1baeaa7e6270644b2fc24743f58bc61e5a2e50db9e91d488`.
- `leakage.py`: `7de444b134c9b9bacd6c2ec78a414a1a7d93c0eefebd305b6af1c72490ca1527`.

Los cambios posteriores a estos hashes necesitan su propia comprobación. Esta revisión complementa los tests y las demostraciones documentadas; no convierte ejecución Python en verificación por un kernel de prueba.
