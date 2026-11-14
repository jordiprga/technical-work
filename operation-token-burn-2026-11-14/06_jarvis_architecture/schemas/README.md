# Contratos

`plan.schema.json` describe el formato de propuesta del prototipo. La implementación Python sigue siendo el validador de autorización: comprueba relaciones entre campos, caller, permisos, presupuesto y tiempo que JSON Schema no expresa. La serialización para hashes es JSON UTF-8 con claves ordenadas y separadores compactos de Python; no se afirma implementar RFC 8785/JCS ni compatibilidad de firmas entre runtimes sin vectores adicionales.

`evidence-ref.schema.json` es un contrato propuesto para interoperabilidad con CryptoSure. Comparte `artifact_id`, `sha256`, `size_bytes`, `media_type`, `source_name`, `imported_at`, `claim_kind` y `limitations`. Añade metadatos de productor, sujeto y alcance. No existe todavía un importador entre ambos prototipos ni validación completa de este schema en el kernel.

Los campos `format` de JSON Schema pueden ser anotaciones dependiendo del validador: URI/fecha requieren validación explícita al implementar la API. Nunca resolver un `source_uri` automáticamente sin política de egress y clasificación del dato.

La clave HMAC de la demo no forma parte del schema ni de los exports. Un valor `approved_by` no autentica por sí mismo a una persona. Las referencias por digest no atribuyen verdad a un artefacto.
