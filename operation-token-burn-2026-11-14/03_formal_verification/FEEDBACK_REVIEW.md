# Revisión independiente: divulgación de conteos mediante feedback

Revisado el 14-11-2026 por la misión de verificación formal. Archivos revisados del coordinador: `00_coordination/feedback_leakage/README.md`, `leakage.py`, `test_leakage.py`. No se modificaron.

## Conclusión

**La identidad de reconstrucción y las cotas de soporte son correctas bajo el transcript especificado.** La distinción entre predicción causal y confidencialidad frente a telemetría posterior es esencial. El documento ya limita adecuadamente las fórmulas IID a una fuente uniforme de referencia separada del modelo físico realimentado.

Se añadió una formalización independiente en `FeedbackLeakage.lean`, compilada y auditada con Lean 4.19.0. La evidencia exacta, hashes y axiomas está en `results/verification.json`.

## Teoremas mecanizados

Se modela una secuencia `samples : Nat → Int`, sin restringir a bits. `windowSum samples W t` suma las W muestras en posiciones t a t+W−1.

1. `rolling_difference`: `C(t+1)−C(t)=B(t+W)−B(t)`, para cualquier W y t.
2. `reconstruct_next`: la muestra nueva se obtiene de la muestra que abandona la ventana y la diferencia de conteos.
3. `rolling_transcript_injective`: para W>0, dos secuencias con el mismo prefijo W y todos los mismos conteos son idénticas.
4. `finite_rolling_transcript_injective`: para una secuencia de n muestras, bastan el prefijo pertinente y los conteos de ventanas completamente incluidas en esas n posiciones. No presupone observar una actualización futura fuera del transcript.
5. `width_one_reveals`: para W=1, cada conteo es exactamente la muestra.

La prueba de inyectividad usa inducción fuerte: la igualdad de la muestra i se reduce a la de i−W, que es estrictamente anterior cuando W>0. Los índices se justifican explícitamente. La identidad de ventana se demuestra por inducción sobre W y álgebra entera; no se asume IID, estacionariedad, distribución arcsine ni seguridad de un extractor.

**No se mecanizó** en Lean la cardinalidad binomial ni la traducción a min-entropía. Esa parte permanece como demostración matemática revisada y enumeración exacta de casos finitos.

## Revisión de las cotas

Para un transcript concreto con primer conteo c₀ y W bits iniciales, cada prefijo compatible tiene c₀ unos. Hay como máximo `binom(W,c₀)` prefijos; por inyectividad, cada uno produce a lo sumo una palabra completa. Algunos prefijos no producen una palabra binaria válida y se descartan. Por tanto, el soporte posterior es como máximo ese número, incluso para fuentes correlacionadas o no uniformes. Para un transcript de probabilidad positiva, toda distribución en M puntos satisface `max p≥1/M`. La cota puntual de min-entropía y la cota promedio ≤W siguen correctamente.

El límite de tasa requiere fijar W mientras n crece. No justifica que una ventana que crece proporcionalmente a n tenga tasa cero. Tampoco permite aplicar la cota de transcript completo a un adversario que sólo conoce conteos esporádicos, redondeados, saturados o truncados. El documento del coordinador ya explicita estas condiciones.

Para ventanas disjuntas y fuente uniforme, la probabilidad de adivinación es `(W+1)/2^W` por bloque: cada posible conteo aporta la misma masa máxima `2^-W`. Para J bloques independientes, el producto genera la fórmula mostrada. No es el promedio de `log binom(W,c)`; el orden de logaritmo y promedio cambia el funcional.

La reconstrucción desde umbrales requiere observar diferencias con precisión que permita identificar conteos enteros, conocer ganancia y objetivo, y que la actualización no contenga clipping, banda muerta u otros términos no observados. No se debe equiparar acceso al estado interno de control con una observación externa real sin un modelo de amenazas.

## Revisión del código y pruebas adicionales

`reconstruct_rolling` usa el índice correcto: en la actualización de índice j, el bit que abandona la ventana ocupa j−1 en la palabra reconstruida. Enumerar sólo los prefijos W evita enumerar todas las palabras de longitud n. Comprobar que el nuevo valor pertenece a {0,1} elimina prefijos inconsistentes.

La revisión adicional comparó reconstrucción con partición exhaustiva para W=1..6 y n=W..W+5, además de verificar la cota binomial en cada transcript. También se probó una distribución no uniforme explícita de cuatro palabras, con probabilidad de adivinación condicional calculada a mano de 7/8. Los recuentos y salida se guardan en `results/feedback_review.json`. Estas pruebas amplían la cobertura finita; la garantía universal de reconstrucción procede de los teoremas Lean.

Observaciones menores de robustez para una futura API pública:

- `measure` acepta probabilidades `float`; los experimentos incluidos usan `Fraction`, pero la API no fuerza aritmética exacta. Rechazar tipos no exactos evitaría resultados etiquetados como exactos por error.
- `recover_counts` presupone objetos compatibles con `Fraction` y no valida de forma completa `window`. Con entradas externas, conviene validar tipos y devolver errores uniformes.
- El límite de enumeración W≤18 controla parcialmente el coste; una API remota también necesitaría un límite de longitud del transcript.

Estas observaciones **no invalidan los resultados entregados**: los ejemplos usan parámetros y distribuciones sintéticas controladas. No se detectó fallo matemático ni error de índices en el algoritmo revisado.
