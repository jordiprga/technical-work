# Revisión previa a publicación — entropía y conformidad

Revisor: agente de extractores, 2026-11-14. Alcance solicitado por coordinación: README/docs/demo de misión 02, informes de misión 05, `00_coordination/ASSURANCE_CASE.md` y análisis de fuga por feedback. Sólo lectura de esos directorios; ninguna publicación realizada por este agente.

## Resultado

**No se encontraron bloqueantes técnicos en las afirmaciones de entropía o conformidad examinadas.** La revisión no equivale a aceptación de un laboratorio ni a una auditoría completa del código. Las demostraciones ya revisadas anteriormente no se repiten aquí.

## Comprobaciones de mayor importancia

| Área | Comprobación | Resultado |
|---|---|---|
| CryptoSure README y demo | PASS, REVIEW y evidencia documental no se confunden con conformidad | Correcto; el informe generado contiene la restricción antes de sus tablas. |
| CryptoSure health tests | Datos alternantes deterministas pueden aprobar RCT/APT | Está mostrado y correctamente interpretado; umbrales declarados sintéticos. |
| CryptoSure vectores SHA | Comparación de biblioteca no se presenta como validación ACVP/CAVP | Correcto. |
| CryptoSure integridad | Hashes, pin externo, autoría y verdad de evidencia están separados | Correcto; no se promete autenticidad intrínseca. |
| CryptoSure baseline | Demo intermedia conservada no se hace pasar por ejecución del código final | README la identifica como intermedia y remite a STATUS para consolidación. |
| QRNG métricas | Hcausal no se interpreta como tasa de minentropía de bloque ni secreto final | Correcto y visible junto a la tabla de resultados. |
| QRNG física | Fuentes públicas no se usan para atribuir parámetros sintéticos a un dispositivo | Correcto; SOURCES separa explícitamente sustento y límites. |
| QRNG muestreo | Barras de cuatro réplicas no se denominan intervalos de confianza | Correcto. |
| QRNG regulación | Simulador y diagnósticos no sustituyen AIS/90B | Correcto. |
| Assurance case | Propuesta propia no se presenta como plantilla oficial | Correcto. |
| Fuga feedback | Modelos uniformes de divulgación no se presentan como fuente realimentada IID | Distinción explícita y suficiente. |
| Fuga feedback | Precisión, saturación, banda muerta y alcance del transcript | Supuestos y límites declarados. |

Se comprobaron los enlaces Markdown locales de los directorios solicitados en el estado leído, sin referencias de archivo ausentes. No se verificó en esta pasada la disponibilidad HTTP de cada enlace externo; las fuentes primarias ya se documentan en sus registros. No se detectó una atribución que requiriera corrección urgente.

## Observaciones no bloqueantes

1. **Vocabulario del caso de aseguramiento.** `ASSURANCE_CASE.md` usa `ERROR`, `MISSING` y `NEEDS_REVIEW` como estados de diseño, mientras el prototipo emite `PASS/REVIEW/FAIL/BLOCKED` y códigos de salida. Es legible como propuesta, pero una futura especificación de integración debería mapearlos explícitamente y evitar sugerir que todos existen ya en el CLI.
2. **Inmutabilidad del paquete final.** La demo y manifiesto final deben generarse después del último cambio del motor. Es una tarea de consolidación pendiente por naturaleza, no un defecto científico. No actualizar el código después de afirmar que un digest identifica la ejecución publicada sin regenerar o marcar la diferencia.
3. **Contexto de las cifras QRNG.** Una tabla copiada fuera del informe puede perder la definición de Hcausal y las diferencias de información lateral entre escenarios. Para difusión pública posterior, conservar la leyenda adyacente o exportarla dentro de la propia figura/tabla.
4. **Revisión de fuentes normativa.** El inventario de versiones es un registro de consulta y no una decisión de aplicabilidad. La limitación está escrita; debe conservarse si se reutiliza como catálogo de producto.
5. **Derechos de copias fuente.** El PDF BSI conservado es una copia intermedia de investigación. Al publicar código, el repositorio puede conservar URL, hash y localizadores sin necesitar redistribuir el documento de terceros. Esta es una decisión de empaquetado; no se afirma aquí haber auditado una licencia de redistribución.

## Recomendación de cierre

Publicar únicamente después de que coordinación congele el contenido y conserve el registro de checks correspondiente. Mantener las limitaciones junto a los resultados, y describir este paquete como investigación y prototipos reproducibles. No hay un hallazgo de esta revisión que exija detener la consolidación para corregir un teorema o una afirmación de conformidad.


Nota de validación de enlaces: el detector sintáctico encontró una coincidencia espuria en una fórmula inline `1-(1-a)`, que no es un enlace Markdown de documentación. Tras inspección no quedó ningún archivo enlazado ausente entre los 17 Markdown revisados.
