# Revisión cruzada y trazabilidad de afirmaciones

Fecha: 2026-11-14. Revisión por agentes de la misma sesión; no representa revisión externa por pares ni aprobación de un laboratorio.

## Revisión recibida de verificación formal

El agente de la misión 03 revisó `theory.md`, secciones 4 y 7, y `fixed_matrix_methods.md`:

- Confirmó la composición clásica con semilla común bajo independencia del proceso completo y minentropía condicionada en el pasado bruto y E.
- Confirmó que los híbridos de prefijo real y sufijo uniforme evitan una aplicación inválida del LHL condicionada en salidas previas.
- Confirmó la extensión cq mediante procesamiento de información lateral clásica y distancia de traza.
- Consideró consistente la cota conservadora `2η+½√(2^(m−k))` para suavizado con distancia purificada y marginal lateral real.
- Revisó sin detectar fallos las identidades de Fourier/transferencia y las cotas basadas en el enumerador de pesos.

Es revisión conceptual; no convierte estos teoremas en pruebas mecanizadas. La misión 03 mantiene sus propios artefactos Lean y su registro de revisión.

## Revisión realizada sobre otros entregables

Se revisó el análisis de `00_coordination/feedback_leakage`:

- Recuperación algebraica del conteo a partir de umbrales exactos: correcta bajo ausencia de saturación/banda muerta y ganancia conocida no nula.
- Fórmula `J[W−log₂(W+1)]` para minentropía condicional promedio de bits uniformes con conteos disjuntos: correcta.
- Recurrencia para ventanas de actualización por bit y límite de soporte por primeras W muestras: correcto para cualquier distribución compatible.
- La enumeración usa la probabilidad de adivinación promedio adecuada y no promedia logaritmos puntuales.

Se revisó `05_qrng_model/MODEL_AND_PROOFS.md`:

- Linealización, varianza y covarianza del error de bloques coherentes con la recurrencia declarada.
- Frontera `a_crit=2K sin²(π/(2K))` y signo de cruce del círculo unidad correctos para la dinámica lineal con ventanas de K intervalos.
- Tasa de minentropía por máximo promedio de ciclo válida para la cadena finita sobre una línea con etiqueta binaria que determina trayectoria.
- Distinción entre predictor causal y secreto frente a telemetría final incorporada explícitamente.

No se revisó toda implementación numérica de la misión 05 ni se certificó el redondeo de sus números.

## Registro de validación propio

- Dieciocho tests de `unittest`, incluido cotejo de transferencia/Fourier contra enumeración completa y contra probabilidades racionales directas.
- Enumeración exacta de diferencias/semillas en familias pequeñas: confirma la implementación del teorema universal₂, no demuestra el teorema para todas las dimensiones.
- Inspección visual de la figura PNG: ejes, etiquetas y curvas corresponden a los datos guardados.
- Resultado Monte Carlo separado y marcado como sintético; no interviene en las afirmaciones exactas.
- Fuente BSI oficial archivada y huella SHA-256 conservada.


## Revisión adicional del prototipo intervalar

El agente QRNG revisó el uso de racionales y el certificado de partición. Confirmó las cotas del certificado actual y el argumento de cobertura por prefijos/Kraft. Detectó dos límites de API: aceptación accidental de floats en extremos y ausencia de cotejo de cifras de entropía derivadas. Se corrigieron ambos antes del cierre: la API rechaza floats; el checker recalcula y coteja logs aproximados, exige versión de esquema y declara el campo narrativo como informativo. Un test adversarial cubre estas regresiones.
