# AIS 20/31, Toeplitz y conditioning criptográfico

## Baselines y alcance de esta lectura

La fuente normativa examinada directamente es **Matthias Peter y Werner Schindler, *A Proposal for Functionality Classes for Random Number Generators*, versión 3.0, 10-09-2024**, referencia matemática-técnica de AIS 20/31. El título conserva la palabra *Proposal*; la portada de esta versión no dice *DRAFT*. No debe confundirse con v2.35 de 2022 ni con los números de versión de los documentos de esquema AIS 20 y AIS 31.

Se descargó el PDF oficial de BSI y se extrajo texto localmente. URL: [PDF BSI de 2024](https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Certification/Interpretations/AIS_31_Functionality_classes_for_random_number_generators_e_2024.pdf?__blob=publicationFile&v=3). SHA-256: `50625ddbe8b8a34ebd11b54ed7c0a57490bcc760ae4825061864f9598d1ae029`.

Como comparación oficial conjunta se usa [NIST IR 8446, final de enero de 2026](https://csrc.nist.gov/pubs/ir/8446/final). Este informe cita los documentos de esquema AIS 20/31 versión 4 de 2025 y la referencia matemática v3.0 de 2024. No reemplaza los requisitos normativos. Para NIST, la base es [SP 800-90B final de 2018](https://csrc.nist.gov/pubs/sp/800/90/b/final), sus erratas/guías aplicables y [SP 800-90C final de 2025](https://csrc.nist.gov/pubs/sp/800/90/c/final).

## Qué pide la ruta de universal hashing en AIS

Localizadores de BSI v3.0, con numeración de página impresa:

| Localizador | Contenido relevante, resumido |
|---|---|
| Párr. 337–338, pp. 65–66 | Selección aleatoria de función por número interno; ley fuerte para la calidad por índice; límite de probabilidad de quedar bajo el umbral de entropía; índices secretos; familia de tamaño mínimo `2²⁰⁰`; restricciones de dependencia entre índices. |
| Párr. 341, p. 66 | Obtiene una cota de probabilidad de mala calidad a partir de la entropía media; reconoce que la cota es gruesa. |
| Párr. 342, pp. 66–67 | Una función fija permanente no se justifica sólo invocando LHL: se evalúa como postprocesado algorítmico con el modelo estocástico. También restringe cómo generar los índices. |
| Párr. 645–651, pp. 133–135 | LHL bajo independencia fuente–índice; garantía media sobre índices; generalización a índices no uniformes. |
| Párr. 652, p. 136 | Ejemplo numérico con matrices Toeplitz e índices de entropía imperfecta. |
| Párr. 947–955, pp. 195–198 | Discusión de índices malos y construcción de refresco bajo supuestos explícitos de independencia/mezcla. |

Estos requisitos son específicos de esa vía de argumentación. **No** equivalen a una prohibición absoluta de matrices Toeplitz fijas en cualquier diseño; el propio párr. 342 describe una vía alternativa basada en el modelo.

## Por qué no contradice a los strong extractors

Un teorema matemático puede afirmar: «para una fuente fijada independientemente de `S`, la distribución conjunta de `S` público y de un transcript finito de salidas está cerca del ideal». Un régimen de evaluación puede exigir además una calidad por operación, protección permanente de índices, un mecanismo de refresco o una prueba específica del postprocesado fijo.

La necesidad de mantener la semilla secreta **no se deduce** del LHL strong estándar: la definición incluye la semilla pública. La exigencia AIS es un requisito de la metodología y de su objetivo de seguridad. La motivación del documento es evitar explotar funciones débiles y reducir la persistencia de índices malos. No debe transformarse esa motivación en el falso teorema general «publicar la semilla destruye siempre la extracción».

Tampoco se deduce de la literatura que «una semilla pública reutilizada es siempre aceptable en AIS». La separación correcta es:

1. **Prueba informacional:** fuente, información lateral, semilla, horizonte, métrica y error.
2. **Argumentación de seguridad del producto:** fugas, control activo, selección de dispositivos, reinicios, fuentes correlacionadas y semilla comprometida.
3. **Conformidad del esquema:** versión, clase funcional, requisitos adicionales y evidencia aceptada.

El contraejemplo de la fuente adaptada al núcleo explica un riesgo real cuando publicar una semilla permite al adversario cambiar la distribución física. El LHL no protege ese experimento, aunque la misma semilla fuera válida para una fuente no adaptativa. Secrecía sola tampoco prueba independencia: canales laterales, feedback o una semilla derivada de los mismos datos pueden correlacionarlos.

## Afirmaciones demostradas y elecciones de modelo

| Afirmación | Naturaleza | Qué falta para aplicarla a un dispositivo |
|---|---|---|
| Toeplitz uniforme tiene colisiones `2⁻ᵐ` para entradas distintas | Teorema algebraico | Implementación correcta; muestreo de la familia prevista. |
| LHL produce cercanía conjunta con semilla | Teorema condicionado | Independencia y minentropía frente a toda información lateral relevante. |
| Entropía promedio sobre semillas implica un límite sobre una fracción de semillas malas | Teorema probabilístico; a menudo cota conservadora | Definir qué se condiciona, el horizonte y cómo se seleccionan dispositivos/transcripts. |
| Refrescar índices hace desaparecer memoria anterior | Dependiente del proceso de refresco | Distribución, independencia, tasa de mezcla y modelo de fuga. |
| Una semilla pública conocida permite adaptar cualquier fuente física a su núcleo | No demostrado en general | Capacidad física concreta de control del adversario. El núcleo es un contraejemplo abstracto, no una vulnerabilidad demostrada de un QRNG. |
| Guardar secreto el índice elimina todos los ataques | Falso sin hipótesis adicionales | Confidencialidad, independencia, robustez física y protección de estado siguen separadas. |
| Una cota de minentropía marginal basta para el stream | Falso | Hace falta una cota conjunta/condicional compatible con dependencias. |

No se identificó un error en el LHL expuesto en BSI. La diferencia relevante está en el objetivo y las hipótesis de aplicación, no en que «el estándar esté matemáticamente equivocado».

## Del error estadístico a la minentropía exigida

Si para una semilla concreta `s` se tiene `TV(Y_s,U_m)≤δ_s`, entonces:

\[
\max_y P(Y_s=y)\le2^{-m}+\delta_s,
\quad H_{\min}(Y_s)\ge-\log_2(2^{-m}+\delta_s).
\]

Por ejemplo, una garantía `δ=2⁻⁶⁴` sobre una salida de 512 bits sólo da, mediante esta conversión genérica, aproximadamente 64 bits de minentropía no suavizada. Puede ser una garantía composable muy fuerte para ciertos protocolos y, aun así, no demostrar una tasa de minentropía no suavizada próxima a uno. Para garantizar `Hmin(Y_s)≥q m` mediante esa cota suficiente se necesita `δ_s≤2^(−qm)−2^(−m)`.

No es una contradicción: TV permite concentrar una pequeña masa excepcional, mientras minentropía no suavizada la penaliza por el máximo de probabilidad. El suavizado, una afirmación promedio y una cota de peor caso son objetos distintos. Esta diferencia ayuda a entender por qué las cifras de compresión exigidas por distintas metodologías no son intercambiables.

Además `E_s[Hmin(Y_s)]` y `Hmin(Y|S)` difieren por Jensen:

\[
H_{\min}(Y|S)=-\log_2\mathbb E_S[p_{\rm guess}(Y|S=s)]
\le \mathbb E_S[-\log_2p_{\rm guess}(Y|S=s)].
\]

Una afirmación de entropía media **no** debe etiquetarse automáticamente como secreto condicional promedio frente a un adversario que conoce `S`.

## Comparación práctica

| Propiedad | Toeplitz seeded con prueba | Hash criptográfico fijo | Conditioning/DRBG con estado |
|---|---|---|---|
| Hipótesis principal | Semilla y modelo de minentropía; universalidad | Modelo de fuente y supuestos sobre la construcción/función | Entropía entrante, estado, construcción y supuestos criptográficos |
| Garantía típica | Distancia estadística/traza bajo hipótesis | Dependiente del modelo; no extractor determinista para toda fuente de alta entropía | Seguridad computacional y propiedades de estado; entropía no creada de la nada |
| Semilla pública | Compatible con LHL strong si independiente | No hay semilla nueva en una función fija | Depende de qué sea clave, nonce, estado o entrada adicional |
| Fuente adversaria adaptativa | No cubierta por LHL estándar | Tampoco cubierta por mera resistencia a colisiones | Exige modelo concreto de compromiso, reseed y recuperación |
| Fallo total de fuente | No mantiene impredecibilidad por sí solo | Función sin estado de entrada conocida produce salida conocida | Puede conservar seguridad computacional si estado previo sigue secreto; depende de la construcción |
| Vía NIST 90B | No automáticamente vetted | Sólo construcciones y parámetros aceptados | Requiere distinguir componente conditioning, DRBG 90A y construcción 90C |
| Vía AIS | Según ruta y argumento específico | Tratamiento según función/modelo | PTG.3 añade propiedades de postprocesado criptográfico con memoria |

La investigación de [Dodis et al., CRYPTO 2004](https://doi.org/10.1007/978-3-540-28628-8_30) muestra por qué una propiedad PRF/MAC y una propiedad extractora necesitan hipótesis diferentes. No se infiere una prueba para una implementación moderna concreta simplemente por usar el nombre HMAC.

La [lista oficial NIST de conditioning vetted](https://csrc.nist.gov/projects/random-bit-generation/sp-800-90-updates) diferencia construcciones aprobadas y no aprobadas para esa categoría. Un buen teorema sobre Toeplitz no convierte automáticamente el componente en vetted, y pasar pruebas de salida tampoco lo hace. El concepto de *full entropy* normativo y sus aproximaciones deben leerse con [NIST IR 8427](https://csrc.nist.gov/pubs/ir/8427/final), sin equipararlo a una prueba incondicional universal para toda fuente adversaria.

## Recomendaciones condicionadas

- **Objetivo de privacidad informacional/quantum-proof:** especificar un estado cq, justificar minentropía condicional, controlar independencia de la semilla y reservar error para toda la vida útil. Toeplitz es una opción defendible bajo esas premisas.
- **Objetivo PTG.2 con Toeplitz fijo:** preparar análisis específico del postprocesado y fuente; no basar el expediente sólo en «strong extractor ⇒ seed reusable».
- **Objetivo PTG.3:** la matriz universal aislada no sustituye las propiedades de estado exigidas al postprocesado criptográfico.
- **Objetivo 90B/90C y comercialización multiesquema:** mantener ramas de evidencia separadas. Una arquitectura puede compartir datos brutos y health tests, pero debe argumentar cada componente y construcción según su baseline.
- **Semilla de una misma fuente física:** justificar independencia efectiva entre datos usados para semilla y datos extraídos; separar intervalos no demuestra independencia sin un modelo de memoria/mezcla.

Estas son recomendaciones de diseño y preparación de evidencia. No son un dictamen de un laboratorio ni una equivalencia de certificaciones.
