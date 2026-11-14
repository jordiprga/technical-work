# Fuentes primarias y registro de alcance

Consultadas el **14 de noviembre de 2026**, sólo mediante lectura pública. Las referencias no representan aprobación del producto, acuerdo comercial ni aceptación del formato propuesto. Las fechas de rastreo de buscadores no se usan como fecha de publicación. Las afirmaciones propias de arquitectura, precios y estrategia se identifican como propuestas o hipótesis.

## Registro

| ID | Fuente | Qué respalda | Qué no respalda |
|---|---|---|---|
| S1 | [NIST ACMVP: Executive Summary](https://pages.nist.gov/ACMVPDocs/home/executivesummary.html) | Modernización, alcance FS del proyecto y actividad de integración en 2026 | Disponibilidad de todas las funciones para toda clase de módulo ni ausencia de otros procesos de actualización |
| S2 | [NIST ACMVP: Overview](https://pages.nist.gov/ACMVPDocs/home/overview.html) | Relación entre laboratorio, programa y líneas de automatización | Sustitución de laboratorios por una SaaS |
| S3 | [NIST ACVP Documentation](https://pages.nist.gov/ACVP/) | Protocolos y repositorio oficial de validación algorítmica | Conformidad integral FIPS por pasar un algoritmo |
| S4 | [NIST ESV Protocol](https://github.com/usnistgov/ESV-Server/blob/main/Entropy%20Source%20Validation%20Protocol.md) | Datos y documentación de soporte; flujos de entropy source/RBG | Que un estimador por sí mismo valide el modelo de una fuente |
| S5 | [NIST SP800-90B EntropyAssessment](https://github.com/usnistgov/SP800-90B_EntropyAssessment) | Implementación pública de métodos y condiciones de uso | Ausencia de bugs, certificación de un dataset o garantía de una implementación propia |
| S6 | [Lightship Greenlight](https://lightshipsec.com/conformance-automation/) | Oferta anunciada de automatización CC, reportes, on-prem y SaaS | Cobertura real, ahorro causal, precio o cuota de mercado; las métricas comerciales no se adoptan como benchmark |
| S7 | [Applus+: Lightship](https://www.appluslaboratories.com/global/en/about-us/inbrief/applus-lightship-security) | Pertenencia al grupo y servicios descritos | Que compraría un producto de terceros |
| S8 | [ACVP Proxy](https://github.com/smuellerDD/acvpproxy) | Herramienta pública, flujos de vectores/resultados, soporte atsec y referencias ESVP/AMVP | Compatibilidad universal o licencia de todos sus componentes sin revisión |
| S9 | [atsec: ACVP support](https://atsec.com/automated-cryptographic-validation-protocol-acvp-support-from-atsec/) | Participación y herramientas publicadas | Capacidades actuales no verificadas en una prueba de producto |
| S10 | [jtsec: Tools](https://jtsec.es/tools) | Existencia de herramientas propias anunciadas y áreas de interés | Pricing, madurez o funcionalidad no descrita |
| S11 | [Applus+: jtsec](https://www.applus.com/global/en/about-us/our-brands/jtsec) | Relación corporativa y actividad de laboratorio | Independencia de presupuesto frente a Lightship |
| S12 | [sec-certs, CRoCS](https://sec-certs.org/) | Proyecto de investigación y análisis de certificados públicos | Exhaustividad o exactitud normativa de cada dato extraído |
| S13 | [NIST: CST lab accreditation](https://csrc.nist.gov/Projects/cryptographic-module-validation-program/cst-lab-accreditation-and-fees) | Papel de laboratorios acreditados y entrega al programa | Número de compradores o demanda de software |
| S14 | [Common Criteria: laboratorios](https://www.commoncriteriaportal.org/labs/index.cfm) y [productos](https://www.commoncriteriaportal.org/products/index.cfm) | Fuentes para construir universo público de actividad | TAM, ingresos o centros de compra deduplicados |
| S15 | [Microchip RNG90](https://www.microchip.com/en-us/product/rng90) y [ATECC608C, RNG certifications](https://onlinedocs.microchip.com/oxy/GUID-37C348DA-53FC-45CB-A3A3-9163D81C42E4-en-US-2/GUID-5ADB6607-BC38-440E-894C-14051A658FD2.html) | Ejemplos de fabricantes/componentes con contexto público de validación | Cliente potencial cualificado o voluntad de pago |
| S16 | [CCN-STIC 2110 MEGA, PDF público](https://www.ccn-cert.cni.es/es/series-ccn-stic/guias/series-ccn-stic/2000-organismo-de-certificacion/7339-ccn-stic-2110-mega-metodologia-de-evaluacion-de-generadores-aleatorios/file.html) | Identidad de metodología, v1.0, edición noviembre 2025 y categorías de tareas | Una evaluación del prototipo o equivalencia con 90B |
| S17 | [CCN-STIC 2100 MEMeC, PDF público](https://www.ccn-cert.cni.es/es/series-ccn-stic/guias/series-ccn-stic/2000-organismo-de-certificacion/7263-ccn-stic-2100-cryptographic-mechanisms-evaluation-methodology/file.html) | Metodología de mecanismos, estructura y aviso de derechos; cabecera observada v1.3.3 | Edición aplicable a cualquier proyecto sin confirmar baseline |
| S18 | [NIST FIPS 140-3 standards](https://csrc.nist.gov/Projects/cryptographic-module-validation-program/fips-140-3-standards) | Referencias ISO/IEC y papel de laboratorios | Derecho a redistribuir normas ISO |
| S19 | [NIST Cost Recovery Fees](https://csrc.nist.gov/projects/cryptographic-module-validation-program/nist-cost-recovery-fees) | Tabla 2026, actualizada 5 enero 2026, tasas del programa | Precio de laboratorio, coste completo o ahorro alcanzable por CryptoSure |
| S20 | [ENISA EUCC scheme](https://certification.enisa.europa.eu/certification-library/eucc-certification-scheme_en) | Esquema, enmiendas, estado final/draft de documentos de apoyo | Que sólo citar el reglamento inicial defina baseline actual completo |
| S21 | [Reglamento de ejecución (UE) 2024/482](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R0482) | Norma inicial del EUCC | Texto consolidado con todas las enmiendas posteriores |
| S22 | [CCN-STIC 2101, anuncio oficial](https://www.ccn.cni.es/es/actualidad-ccn/1266-nueva-guia-ccn-stic-sobre-el-procedimiento-de-autorizacion-de-laboratorios-para-evaluaciones-memec) | Existencia del procedimiento de autorización MEMeC | Autorización de CryptoSure o de un laboratorio no comprobado |

## Discrepancias y controles de actualidad

La cabecera del PDF MEMeC descargable/visualizado dice v1.3.3 y edición noviembre 2024; el coordinador observó que el [portal de criterios del CCN](https://oc.ccn.cni.es/tipos-de-certificacion/certificacion-criptologica/criterios-y-metodologias) lista otra revisión. Se conserva esta discrepancia como hallazgo de control de baseline, sin decidir por la etiqueta del enlace ni por la fecha de rastreo. Antes de crear un perfil comercial se debe confirmar edición aplicable y conservar hash de la copia autorizada.

La página ENISA lista enmiendas de diciembre 2024 y diciembre 2025, además de documentos finales y borradores. Un perfil EUCC debe almacenar esa composición y contexto de aplicabilidad. El mapa normativo consolidado lo mantiene la misión de coordinación; esta misión no pretende congelar una baseline legal universal.

No se han copiado las normas ni grandes fragmentos. Los documentos proponen estructuras originales y enlazan fuentes. No se ha accedido a documentación privada de Quside, credenciales ni sistemas de fabricantes/laboratorios.

## Qué falta investigar antes de lanzar

Precios y contratos de competidores; disposición a pagar; coste real de mantener cada perfil; aceptación de exportaciones por evaluadores; licencias precisas de dependencias; derechos sobre documentos normativos; landscape de patentes; requisitos de responsabilidad/seguro; tamaño del universo de compradores deduplicado. La ausencia de estos datos no se rellena con cifras estimadas presentadas como hechos.
