# Versiones y decisiones de interpretación

Consulta pública: 14 de noviembre de 2026. Este inventario identifica documentos; no certifica que todos sean aplicables a cualquier producto. Antes de una evaluación se debe fijar el esquema, alcance, fecha de solicitud, clase, configuración y versiones exactas.

| Familia | Base observada | Consecuencia para CryptoSure |
|---|---|---|
| SP 800-90B | Final enero de 2018; la página oficial señala dos erratas pendientes desde mayo de 2025 | Versionar el texto base y las erratas separadamente; un resultado de estimación no demuestra el modelo físico |
| SP 800-90C | Final 25 de septiembre de 2025 | No basar un producto nuevo en el cuarto borrador sin justificar esa elección |
| NIST IR 8446 | Final 29 de enero de 2026 | Usar como comparación de terminología y supuestos NIST/BSI, no como equivalencia automática de certificados |
| FIPS 140-3 / CMVP | IG anunciada el 19 de agosto de 2026; Management Manual del 9 de abril de 2026 | Mantener versiones de IG, manual, SP 800-140 y normas referenciadas, además de FIPS 140-3 |
| CC / CEM | CC:2022 Release 1 y CEM:2022; errata e interpretación v1.2 listada como última | Un identificador como «CC2022» no congela por sí solo todos los requisitos aplicables |
| EUCC | Reglamento 2024/482; ENISA lista modificaciones 2024/3144 y 2025/2462 | No confundir el texto original de 2024 con la base regulatoria consolidada |
| MEMeC | El portal lista CCN-STIC-2100 v1.3.2, pero el PDF público consultado lleva v1.3.3 | Registrar la discrepancia; no declarar una edición aplicable única por el título del portal |
| MEGA | El portal lista CCN-STIC-2110, versión 1.0, con matriz de evidencias y cuestionarios anexos | Automatizar referencias y coherencia de la matriz sin convertir enlaces en juicios de suficiencia |
| AIS 20/31 | La misión 04 verifica el documento técnico y las condiciones de aplicación | No deducir versión por el año del nombre del archivo ni confundir documento de interpretación y anexo técnico |

Fuentes primarias consultadas:

- [SP 800-90B, publicación y erratas](https://csrc.nist.gov/pubs/sp/800/90/b/final).
- [SP 800-90C final](https://csrc.nist.gov/pubs/sp/800/90/c/final).
- [NIST IR 8446 final](https://csrc.nist.gov/pubs/ir/8446/final).
- [Anuncios IG FIPS 140-3](https://csrc.nist.gov/Projects/cryptographic-module-validation-program/fips-140-3-ig-announcements) y [Management Manual](https://csrc.nist.gov/projects/cryptographic-module-validation-program/cmvp-fips-140-3-management-manual).
- [Portal oficial CC/CEM](https://www.commoncriteriaportal.org/cc/index.cfm) y [errata v1.2](https://www.commoncriteriaportal.org/files/ccfiles/CCMB-2025-001-v1_2-Errata_Interpretation_CC_CEM_2022.pdf).
- [ENISA: EUCC, modificaciones y documentos SotA](https://certification.enisa.europa.eu/certification-library/eucc-certification-scheme_en).
- [Organismo CCN: criterios y metodologías](https://oc.ccn.cni.es/tipos-de-certificacion/certificacion-criptologica/criterios-y-metodologias).
- [PDF público MEMeC con cabecera v1.3.3](https://www.ccn-cert.cni.es/es/series-ccn-stic/guias/series-ccn-stic/2000-organismo-de-certificacion/7263-ccn-stic-2100-cryptographic-mechanisms-evaluation-methodology/file.html), consultado directamente: edición noviembre de 2024, 240 páginas. La discrepancia con el portal queda abierta para decidir aplicabilidad en cada proyecto.

## Regla de producto propuesta

Un paquete normativo debe registrar `publisher`, `document_id`, `edition`, `publication_date`, `effective_date`, `retrieved_at`, `canonical_url`, `content_sha256`, `errata`, `applicability_decision` y `reviewer`. La fecha efectiva puede quedar desconocida; jamás se rellena con la fecha de descarga. Los campos desconocidos se conservan como desconocidos.

Un cambio de norma no implica invalidar todo el expediente: obliga a identificar las afirmaciones que dependen del texto cambiado, su interpretación y su alcance. Un grafo de dependencias permite proponer la revisión; el responsable decide suficiencia y aplicabilidad.

## Distinciones que deben sobrevivir a toda exportación

1. **Integridad de archivo:** los bytes coinciden con un hash esperado.
2. **Autenticidad:** una identidad confiable produjo o aprobó esos bytes.
3. **Reproducibilidad:** una ejecución descrita puede repetir un resultado dentro de tolerancias declaradas.
4. **Validez del experimento:** el diseño experimental responde a la pregunta planteada.
5. **Validez del modelo:** las hipótesis describen el sistema y adversario relevantes.
6. **Conformidad:** se satisfacen los requisitos aplicables, con las evidencias aceptadas por el esquema.

Ninguna de estas seis propiedades implica automáticamente la siguiente. Esta es una decisión de arquitectura del proyecto, no una cita normativa.
