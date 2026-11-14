# CryptoSure — informe de evidencia

**DEMOSTRADOR. No constituye certificación, validación ni decisión de conformidad.**

Perfil: cryptosure.synthetic-demo / 2026.11.14-demo.1
Ejecución UTC: 2026-11-14T11:36:45+00:00
Resultado técnico: **REVIEW**

PASS sólo indica que los checks implementados aprobaron sobre los bytes incluidos.
REVIEW requiere evaluación humana. BLOCKED señala evidencia ausente, inválida o plugin desconocido.
FAIL señala al menos una comprobación fallida. Ningún estado sustituye al laboratorio u organismo.

La verificación de hashes demuestra consistencia con un root digest confiable, no autoría, verdad o adecuación.
El root.sha256 dentro del mismo bundle no es por sí solo un ancla de confianza externa.

## Matriz de requisitos

| Requisito | Cláusula de referencia | Estado | Checks | Evidencias |
|---|---|---|---|---|
| DEMO.HASH.001: Verificar una implementación de biblioteca frente a vectores suministrados | DEMO únicamente; sin mapeo normativo | PASS | hash-vectors:PASS | sha256-vectors |
| DEMO.HEALTH.001: Ejecutar algoritmos de health tests configurados sobre datos sintéticos | Demostración conceptual; SP 800-90B 4.4 requiere análisis adicional | REVIEW | rct-check:PASS, apt-check:PASS | binary-samples, source-model |
| DEMO.BUILD.001: Comprobar metadatos declarados de un build | Ejemplo extensible a evidencia de gestión de configuración | REVIEW | synthetic-marker:PASS | build-manifest |
| DEMO.DOC.001: Revisar el modelo de la fuente y la adecuación de las evidencias | Ejemplo de juicio humano: presencia no implica adecuación | REVIEW |  | source-model |

## Detalle de comprobaciones

- hash-vectors: **PASS**. Comparación con vectores proporcionados; no validación CAVP/ACVP.
- rct-check: **PASS**. Alarma cuando longitud de racha &gt;= cutoff; no estima entropía ni valida el cutoff.
- apt-check: **PASS**. Cada ventana toma su primer símbolo como referencia y lo cuenta; umbrales no calibrados.
- synthetic-marker: **PASS**. Comparación literal de un campo JSON; no evalúa expresiones.

## Límites del perfil

Ejemplos inventados, no transcripción normativa. Los checks RCT/APT usan umbrales sintéticos sin justificación de entropía ni tasa de falsas alarmas. Los vectores SHA-256 no son una campaña ACVP. Documentos y propiedades de diseño requieren revisión humana.

## Proveniencia

- Tool version: 0.1.0
- Tool source SHA-256: `bf67e8d968c7324d642b37332cdd18a74b434f651f291e296a18a422dbf5f6df`
- Profile SHA-256: `bd4afd4386e4f39c057f48f89808b82667569b71a0cb02519f64bcac24f90831`
- Git: `{'requested': False, 'status': 'not_captured'}`
