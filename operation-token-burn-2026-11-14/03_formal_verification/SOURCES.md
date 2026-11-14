# Fuentes primarias y alcance

Todas consultadas el 14-11-2026. Las fuentes se usan para contexto y mapeo; los teoremas de este directorio son trabajo original. No se reproduce documentación privada.

| ID | Fuente y enlace | Qué se verificó | Qué no permite concluir |
|---|---|---|---|
| N90B | [NIST SP 800-90B, enero 2018](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/nist.sp.800-90b.pdf) | §§4.3, 4.4.1 y 4.4.2; manejo de fallos, RCT/APT | Que nuestro modelo cubra todo 90B o una implementación real |
| N90A | [NIST SP 800-90A Rev.1](https://csrc.nist.gov/pubs/sp/800/90/a/r1/final) | Publicación final junio 2015 y enlace a Rev.2 draft | Que un draft sustituya la final sin decisión de esquema |
| MEGA | [CCN-STIC 2110 anexo 1, v1.0 noviembre 2025](https://www.ccn-cert.cni.es/es/pdf/guias/series-ccn-stic/2000-organismo-de-certificacion/7340-ccn-stic-2110-mega-anexo-1-evidence-matrix-document/file.html) | Páginas impresas 14–15, 25–26, 31–32; destinos de evidencia | Aceptación de un paquete Lean ni correspondencia normativa automática |
| LEAN | [Lean: Validating a Lean Proof](https://lean-lang.org/doc/reference/latest/ValidatingProofs/) | Axiomas, límites de kernel-check y mecanismos de comprobación extra | Que el enunciado formal coincida por sí solo con la intención |
| LEANREL | [Release oficial Lean 4.19.0](https://github.com/leanprover/lean4/releases/tag/v4.19.0) | Descarga binaria oficial usada para esta ejecución | Que sea la versión más reciente o auditoría independiente del binario |
| HMAC | [Ye et al., Verified Correctness and Security of mbedTLS HMAC-DRBG, 2017](https://arxiv.org/pdf/1708.08542) | §§1,3,7–8; separación entre corrección funcional y alcance de seguridad | Seguridad de Instantiate, fork-safety o canales laterales fuera de su alcance |
| HAX | [hax Lean quick start](https://hax.cryspen.com/manual/lean/quick_start/) | Backend Lean, extracción parcial, escenarios y limitaciones | Que este prototipo haya ejecutado ese pipeline |
| HAXP | [Bhargavan et al., hax, IACR 2025/142](https://eprint.iacr.org/2025/142) | Diseño de múltiples backends y objetivos de verificación | Corrección completa de cualquier traducción o programa Rust |
| SAW | [Galois, SAW](https://tools.galois.com/saw) | Propósito e integración con Cryptol | Equivalencia de un producto sin ejecutar pruebas propias |
| CRYPTOL | [Galois cryptol-specs](https://github.com/GaloisInc/cryptol-specs) | Repositorio de especificaciones y existencia de DRBG | Cobertura total de versiones actuales de estándares |
| HACL | [HACL* documentation](https://hacl-star.github.io/) | Biblioteca verificada y toolchain de proyecto | Que cualquier integración preserve todas sus propiedades |
| EASY | [EasyCrypt](https://www.easycrypt.info/) | Razonamiento sobre juegos probabilísticos y adversarios | Evidencia de implementación de nuestro prototipo |
| RECHECK | [lean4checker](https://github.com/leanprover/lean4checker) | Replay de declaraciones usando kernel | Ejecución realizada en este paquete: no se ejecutó |
| COMPARE | [Lean comparator](https://github.com/leanprover/comparator/) | Comparación de enunciados y comprobaciones independientes | Ejecución realizada en este paquete: no se ejecutó |

La búsqueda inicial del artículo HMAC-DRBG en el servidor de Princeton devolvió HTTP 403 al navegador; se consultó el texto público en arXiv. La URL histórica de manual Lean 4.19.0 no fue accesible por el navegador; la ejecución se fijó mediante binario y hashes, mientras que la guía actual se usa sólo para recomendaciones de validación.
