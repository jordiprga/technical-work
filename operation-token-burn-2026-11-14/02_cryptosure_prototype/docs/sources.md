# Fuentes primarias consultadas

Consulta: 2026-11-14. No se usaron documentos privados. Los comentarios de diseño,
amenazas y decisiones de arquitectura son análisis propio, no prescripciones de NIST.

| Fuente | Uso concreto y límite |
|---|---|
| [NIST SP 800-90B, página oficial](https://csrc.nist.gov/pubs/sp/800/90/b/final) | Contexto de fuentes de entropía y existencia de erratas señaladas en mayo de 2025; obliga a versionar interpretación y edición |
| [NIST SP 800-90B, PDF oficial](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-90B.pdf) | Referencia pública para health tests; el prototipo sólo demuestra mecánicas parametrizadas, sin calibración ni dictamen |
| [Código NIST EntropyAssessment](https://github.com/usnistgov/SP800-90B_EntropyAssessment) | Implementación pública a integrar de forma fijada y reproducible en el futuro; no descargada ni ejecutada en este prototipo |
| [NCCoE: automatización CMVP](https://www.nccoe.nist.gov/automation-nist-cryptographic-module-validation-program) | Confirma una iniciativa pública existente de automatización; no demuestra aceptación de CryptoSure ni sustituye el proceso CMVP |
| [Git: documentación de status](https://git-scm.com/docs/git-status) | Formatos para scripts, refresh del índice y fsmonitor; motivó escoger una captura de metadatos más conservadora |

Los vectores SHA-256 de la demo son los mensajes vacío y `abc`, usados como casos
conocidos para comprobar la biblioteca del runtime. No proceden de una sesión ACVP
ni acreditan un producto. El stream alternante es un contraejemplo sintético propio.

No se afirma conformidad normativa de Common Criteria, EUCC, AIS 31 ni CCN-MEGA
a partir de este código. Sus posibles adaptadores son propuestas que requieren fuentes
autorizadas, versión exacta, revisión de especialistas y validación del flujo con el
evaluador correspondiente.
