# Propuesta técnica y empresarial

## La decisión de producto

CryptoSure debería empezar como una **mesa de trabajo para evidencia de certificación criptográfica**. El usuario conecta una versión de producto, requisitos seleccionados y artefactos de ensayo; obtiene una matriz de trazabilidad, hallazgos de consistencia, ejecuciones reproducibles y un paquete que un evaluador puede inspeccionar sin depender del proveedor de software. El valor es saber qué se ha comprobado, bajo qué condiciones y qué deja de estar respaldado cuando cambia algo.

La oportunidad de automatización es real a nivel de actividad: el propio NIST está desarrollando estructuras para reducir la variación entre entregas. La voluntad de pagar por una startup independiente **no está demostrada**. El resumen oficial de ACMVP identifica los Full Submissions como alcance y deja fuera los tracks de actualización de ese proyecto. Esto sugiere investigar mantenimiento de evidencia, pero no demuestra que NIST carezca de otros procesos para actualizaciones. [S1]

Evitar una promesa comercial imposible de controlar: el tiempo total hasta el certificado depende de diseño, ensayos físicos, disponibilidad del laboratorio, observaciones y autoridad. Separar siempre horas de preparación ahorradas, horas de revisión ahorradas y días de cola de terceros.

## Qué problema compra cada participante

| Participante | Trabajo costoso que puede delegar | Comprador / usuario | Lo que no puede prometer CryptoSure |
|---|---|---|---|
| Fabricante de fuentes de entropía | Mantener relación entre adquisición, configuración, modelo, análisis y documentación | Responsable de seguridad / ingeniero de validación | Que una buena estadística demuestre el modelo físico |
| Fabricante de HSM, librería o módulo | Alinear versiones, entornos operativos, pruebas y política de seguridad | Director de ingeniería / compliance lead | Que aprobar tests equivalga a validación FIPS |
| Laboratorio | Reducir artefactos ausentes, referencias rotas y preguntas repetidas | Director técnico / evaluador | Sustituir criterio, acreditación o independencia |
| Integrador de componentes | Justificar aplicabilidad de una evidencia upstream a su configuración | Arquitecto de producto / assurance lead | Transferencia automática de certificados |
| Organismo | Recibir datos estructurados consistentes | Equipo de programa / técnico de esquema | Condicionar o anticipar su decisión |

El usuario diario y el comprador económico pueden ser distintos. Un ingeniero puede valorar una CLI, mientras que el director compra por menor retrabajo y previsibilidad. Los organismos son interlocutores de interoperabilidad a largo plazo, no el primer segmento de ventas: dependencia regulatoria y ciclos de compra harían el lanzamiento frágil.

## Segmento inicial y alternativas

**Hipótesis de segmento inicial:** fabricantes que mantienen fuentes de entropía o componentes criptográficos en varias configuraciones y trabajan repetidamente con laboratorios. Su dolor incluye capturas grandes, versiones de herramienta, variantes de firmware y justificaciones que no se reducen a tests. La especialización de Jordi permite identificar fallos sutiles sin necesitar un producto horizontal completo.

No limitar necesariamente la empresa a fabricantes de QRNG: ese conjunto puede ser pequeño y concentrado. La unidad de expansión es un programa de evidencia reutilizable por componente, versión y configuración, que después admite RBG, módulos y familias de productos.

**Alternativa comercial B:** vender a laboratorios una estación de revisión offline compatible con los paquetes de fabricantes. Ventaja: un laboratorio expone muchos proyectos. Riesgo: herramientas internas, independencia, márgenes por proyecto y concentración. Es probable que una empresa grande de ensayos prefiera desarrollar internamente; probar primero con equipos para los que la plataforma no sea ya diferenciación estratégica.

**Alternativa C:** consultoría especializada con software interno. Puede producir ingresos antes, pero no debe etiquetarse como SaaS escalable si cada entrega depende intensamente del fundador. Registrar horas por proyecto y porcentaje de artefactos generados por conectores reutilizables.

## Competidores y sustitutos reales

| Oferta / actor | Evidencia pública observada | Implicación para CryptoSure |
|---|---|---|
| NIST ACMVP, ACVP y ESV | Esquemas y protocolos públicos de automatización de módulos, algoritmos y entropía [S1], [S3], [S4], [S5] | Adaptarse; no vender una copia de un cliente de protocolo como ventaja duradera |
| Lightship Greenlight, grupo Applus+ | Automatización de pruebas CC, reportes y oferta on-prem/SaaS [S6], [S7] | Competencia directa. Su afirmación comercial de reducción de tiempo no es benchmark independiente |
| atsec / ACVP Proxy y Parser | Herramientas públicas para ciclo de vectores, respuestas y resultados; soporte ESVP/AMVP en el repositorio [S8], [S9] | Los conectores básicos pueden ser gratuitos y de alta calidad. Evaluar licencia e integración antes de reimplementar |
| jtsec, grupo Applus+ | Herramientas propias para facilitar evaluación y transición a esquemas [S10], [S11] | Mismo grupo que Lightship: no contar ambos como clientes independientes sin analizar centros de compra |
| sec-certs / CRoCS, Masaryk | Investigación y herramientas de análisis de certificados públicos [S12] | La búsqueda documental y dashboards de certificados ya tienen sustitutos abiertos |
| Herramientas internas de laboratorios | Existencia inferida de su trabajo y de ofertas públicas; capacidades no auditadas | Pedir demostración del flujo real antes de suponer hojas de cálculo ineficientes |
| Git + scripts + hojas de cálculo + gestor documental | Sustituto técnico plausible y barato; adopción concreta no medida | CryptoSure debe superar un sistema bien mantenido, no una caricatura de manualidad |

No se ha localizado evidencia suficiente para comparar precios, número de clientes, cobertura efectiva, ingresos o márgenes de estos productos. No asignar cuotas de mercado inventadas. La lista no es exhaustiva y no equivale a una búsqueda de patentes.

## Clientes potenciales y selección de cuentas

Las categorías son prospectos teóricos, no leads cualificados. Las listas oficiales de laboratorios y productos certificados permiten construir un universo inicial sin recurrir a información privada. [S13], [S14] Ejemplos públicos de componentes con esfuerzos de validación incluyen RNG90 y ATECC608C de Microchip. [S15] La presencia de certificaciones demuestra actividad técnica; no demuestra dolor, presupuesto o intención de comprar software.

Priorizar cuentas con cuatro señales: varias versiones/configuraciones, dos o más programas de evaluación, equipo de assurance identificable y necesidad de revisar cambios. Despriorizar clientes de una sola certificación sin roadmap, entornos que obliguen a una instalación completamente singular y cuentas que exijan una declaración de conformidad del software.

El primer canal debería ser relación técnica fabricante–laboratorio: exportación gratuita para revisar un paquete y licencia de pago para generarlo y mantenerlo. Permitir que un laboratorio examine un paquete sin enviar su documentación a una SaaS reduce fricción. No crear un marketplace de acreditación hasta tener una función básica valiosa.

## Qué automatizar por esquema

| Familia | Automatización razonable | Parte que exige justificación o juicio |
|---|---|---|
| SP 800-90B / ESV | Validación de formato y metadatos, hashes, ejecución de herramienta fijada, captura de logs, referencias al dataset y revisión de integridad del paquete | Modelo de fuente, mecanismo de generación, representatividad, límites ambientales, fallos, confianza en adquisición y aplicabilidad |
| SP 800-90C | Trazar componentes y construcciones declaradas; controlar versiones y supuestos | Afirmaciones de composición y entropía; interpretación del esquema y revisión del laboratorio |
| FIPS 140-3 | Inventario de evidencias, correspondencias de test, consistencia de versiones y datos para payloads | Delimitación del módulo, adecuación de evidencias y ensayos físicos/operacionales según alcance |
| Common Criteria / EUCC | Matriz TOE–requisitos–evidencia–configuración, referencias, gestión de cambios | Análisis de vulnerabilidad, adecuación del ST/PP, profundidad del aseguramiento y decisión de continuidad |
| CCN-MEGA / MEMeC | Registro de tareas, parámetros y supuestos; relación entre modelos y ensayos; paquetes revisables | Evaluación matemática/física, mecanismos autorizados, interpretación y decisión del organismo |

ESV solicita documentación explicativa además de datos: un wrapper estadístico no cubre toda la obligación. [S4] MEGA y MEMeC son metodologías diferentes, con identificadores 2110 y 2100, respectivamente; el software debe preservar ese contexto. [S16], [S17] Los términos equivalencia y «cumple también» requieren justificación específica; una misma evidencia puede servir de entrada a dos evaluaciones sin que sus conclusiones sean intercambiables.

## Modelo de producto y distribución

**Núcleo:** CLI local, esquema abierto de manifest, validador offline, grafo de dependencias y export HTML/JSON. **Producto pagado:** gestión de programas, biblioteca de adaptadores mantenidos, evaluación de impacto, colaboración y soporte. **Edición privada:** instalación del cliente o laboratorio, actualizaciones verificables y export sin dependencia de un servicio externo.

Tres capas de ingresos a experimentar, sin afirmar demanda:

1. Piloto de alcance fijo, 8–15 k€, con criterios de éxito y conjunto de artefactos acordados. Debe poder funcionar con información sintética o una captura controlada aprobada por el cliente.
2. Licencia anual por programa/equipo, hipótesis 12–36 k€; límites transparentes por proyectos activos o capacidad, no por número de requisitos para no penalizar rigor.
3. Edición laboratorio/enterprise, hipótesis 60–120 k€ cuando hay múltiples proyectos, entornos privados y soporte. Integración inicial se factura aparte y sus horas no se esconden dentro de ARR.

No vender por consumo de tokens: el cliente compra evidencia verificable, no actividad de agentes. No condicionar la salida del cliente a mantener una suscripción: un paquete exportado debe seguir verificándose con herramientas abiertas y versiones conservadas.

## Prueba de disposición a pagar

Un piloto no debe medirse sólo por satisfacción. Antes de empezar, fijar número de requisitos, documentos, configuraciones, herramientas y preguntas del evaluador. Un evaluador no involucrado en la construcción debe localizar evidencia, reproducir una prueba y detectar una modificación deliberada.

Medidas primarias: tiempo mediano de localizar evidencia; horas de preparación; número de solicitudes adicionales por ausencia o inconsistencia; tiempo de detectar evidencias obsoletas; tasa de errores de clasificación. Guardar complejidad y experiencia de quien evalúa para no atribuir todo al software. El tiempo total de certificación queda como medida secundaria contaminada por colas.

**Criterios propuestos de continuación:** al menos tres pilotos de pago entre ocho conversaciones con clientes del segmento; dos laboratorios aceptan revisar exportaciones sin rehacer el paquete; ahorro comprobable de al menos 30% en tareas delimitadas; al menos 70% del trabajo de incorporación reutiliza conectores existentes; valor anual de ahorro directo ≥3× precio anual. Son umbrales de decisión propios, no benchmarks de mercado.

**Criterios de abandono o replanteamiento:** nadie compra después de ver el paquete; el ahorro sólo existe porque el fundador hace consultoría oculta; clasificación automática crea falsos «satisfecho»; clientes no pueden compartir ni siquiera metadatos con la arquitectura elegida; cada revisión normativa obliga a reescribir el producto.

## Posición defensible y propiedad intelectual

El conocimiento de normas públicas no es una barrera exclusiva. El código de un wrapper, un prompt o un buscador documental tampoco. Una ventaja puede acumularse en pruebas de regresión adversarias, adaptadores fiables, semántica de cambios, historial de revisiones, interoperabilidad aceptada y reputación de precisión. Es una hipótesis de ejecución, no un derecho de exclusión.

Separar cuatro activos: código propio con cadena de titularidad; corpus propio de ejemplos sintéticos; interpretaciones documentadas revisadas por especialistas; datos del cliente que pertenecen al cliente. Nunca entrenar con evidencia privada por defecto. Las licencias de normas, tablas y herramientas se revisan individualmente: el acceso público no implica permiso de redistribución de su contenido. FIPS 140-3 referencia estándares ISO; no incluir sus textos sin derechos. [S18] Las guías CCN consultadas también contienen avisos de reproducción: trabajar con localizadores y resúmenes propios, no copiar corpus enteros.

Una patente sólo merece exploración cuando exista un mecanismo técnico nuevo y defendible; no se ha hecho búsqueda de anterioridades ni opinión jurídica. Publicar protocolos y mantener adaptadores propietarios es una opción de negocio, no una recomendación definitiva de licencia.

## Riesgos que deben gobernar el lanzamiento

| Riesgo | Indicador temprano | Respuesta |
|---|---|---|
| NIST/labs absorben la función | Misma exportación disponible sin coste | Especializar en evidencia anterior al submission y ciclo de cambios, o abandonar |
| Servicios disfrazados de SaaS | >30% de horas por cliente en lógica singular | Reducir segmento y cobrar integración |
| Responsabilidad por falsa afirmación | Reporte interpreta PASS como certificado | Semántica separada y revisión humana obligatoria |
| Dependencia de fundador | Sólo Jordi puede corregir perfiles | Doble revisión, corpus de casos y documentación de decisiones |
| Mercado pequeño | Pocos centros de compra repetidos | Expandir por componentes y configuraciones únicamente después de validar nicho |
| Exfiltración / acceso indebido | Conector requiere credenciales amplias | Procesamiento local, permisos mínimos y desconexión por defecto |
| Inconsistencia normativa | Perfil mezcla ediciones o guías | Baselines explícitos, migración revisada y evidencia obsoleta visible |
| Independencia de laboratorio | Confusión entre proveedor y evaluador | Contratos, roles y separación entre preparación y dictamen |

## Relación con reputación internacional de Jordi

La ruta más creíble es producir artefactos públicos útiles: benchmarks sintéticos de fallos de trazabilidad, reproducibilidad de estimadores, ejemplos de contraejemplos de extracción y semántica de evidencias. Una futura publicación debe distinguir investigación de resultados de clientes y pasar revisión. En esta misión no se ha publicado ni contactado a nadie.

El interés comercial y la autoridad técnica se refuerzan si el producto ayuda al evaluador a cuestionar afirmaciones, incluida la del proveedor. Se debilitan si marketing promete eliminar al laboratorio o convierte estadísticas favorables en garantías de seguridad.

[S1]: https://pages.nist.gov/ACMVPDocs/home/executivesummary.html
[S3]: https://pages.nist.gov/ACVP/
[S4]: https://github.com/usnistgov/ESV-Server/blob/main/Entropy%20Source%20Validation%20Protocol.md
[S5]: https://github.com/usnistgov/SP800-90B_EntropyAssessment
[S6]: https://lightshipsec.com/conformance-automation/
[S7]: https://www.appluslaboratories.com/global/en/about-us/inbrief/applus-lightship-security
[S8]: https://github.com/smuellerDD/acvpproxy
[S9]: https://atsec.com/automated-cryptographic-validation-protocol-acvp-support-from-atsec/
[S10]: https://jtsec.es/tools
[S11]: https://www.applus.com/global/en/about-us/our-brands/jtsec
[S12]: https://sec-certs.org/
[S13]: https://csrc.nist.gov/Projects/cryptographic-module-validation-program/cst-lab-accreditation-and-fees
[S14]: https://www.commoncriteriaportal.org/labs/index.cfm
[S15]: https://www.microchip.com/en-us/product/rng90
[S16]: https://www.ccn-cert.cni.es/es/series-ccn-stic/guias/series-ccn-stic/2000-organismo-de-certificacion/7339-ccn-stic-2110-mega-metodologia-de-evaluacion-de-generadores-aleatorios/file.html
[S17]: https://www.ccn-cert.cni.es/es/series-ccn-stic/guias/series-ccn-stic/2000-organismo-de-certificacion/7263-ccn-stic-2100-cryptographic-mechanisms-evaluation-methodology/file.html
[S18]: https://csrc.nist.gov/Projects/cryptographic-module-validation-program/fips-140-3-standards
