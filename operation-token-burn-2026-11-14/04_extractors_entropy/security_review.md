# Revisión crítica reutilizable

## Decisiones que hay que fijar antes de dimensionar Toeplitz

1. ¿Cuál es la variable secreta final y qué conoce el adversario al terminar? Incluir datos de calibración, contadores, registros de umbral, outputs previos, telemetría, semilla y estado comprometido cuando correspondan.
2. ¿Se busca cercanía estadística, secreto cuántico, impredecibilidad computacional o una afirmación de minentropía no suavizada? Especificar métrica y presupuesto.
3. ¿La fuente puede depender de la semilla? Dibujar dependencias físicas y de software; no sustituir el diagrama por «la semilla es aleatoria».
4. ¿Qué cota de entropía está demostrada: marginal, bloque, condicional en pasado, o condicional frente al transcript final? Sólo la última que corresponda al objetivo puede alimentar la extracción.
5. ¿Qué horizonte conjunto se reclama: llamada, sesión, dispositivo, flota o vida útil? ¿Hay selección por tests, aceptación, reinicio o fallo?
6. ¿Qué requisito del esquema exige algo adicional a la prueba matemática?

## Casos y resolución

| Caso | Evaluación | Próxima evidencia útil |
|---|---|---|
| Semilla uniforme pública; bloques IID independientes de ella | LHL y composición aplicables si entropía lateral también válida | Justificar IID/modelo y presupuesto acumulado. |
| Semilla uniforme pública; bloques correlacionados | Posible, no automático | Cotas `Hmin(Xᵢ|X<ᵢ,E)` o una prueba conjunta alternativa. |
| Semilla pública; adversario configura la fuente después | Prueba estándar inválida | Aislamiento causal, semillas nuevas tras adquisición o modelo extractor adversarial distinto. |
| Semilla fija de fabricación; fuente muy restringida conocida | Puede demostrarse directamente | Analizar imagen/distribución bajo esa matriz y todos los parámetros admisibles. |
| Semilla PRG larga desde secreto corto | Garantía computacional posible | Hipótesis PRG, compromiso de estado y compatibilidad del modelo fuente. |
| Mismo seed en toda flota | El adversario puede seleccionar/combinar dispositivos | Garantía conjunta, número máximo de dispositivos y correlaciones compartidas. |
| Publicar todos los umbrales del feedback | Puede revelar datos aparentemente aleatorios al generarse | Recalcular entropía condicionada en transcript final; véase análisis de coordinación. |

## Evidencias que sí son reutilizables en un expediente

- Especificación bit a bit y convención de matriz; vectores conocidos cruzados entre referencia y RTL/C.
- Prueba de universalidad de la familia efectivamente muestreada; documentar rechazos, subconjuntos, expansión PRG y cualquier sesgo.
- Proveniencia de cada cota de entropía: modelo, intervalo de parámetros, fallo de estimación, información adversaria y tamaño de bloque.
- Política de semilla: generación, distribución, vida útil, cambios, secreto si el esquema lo exige, borrado y tratamiento de fallos.
- Libro de presupuesto de error: extracción, estimación, ADC/modelo, semilla, composiciones y selección de resultados.
- Pruebas de invariantes: no salida sin presupuesto de entropía válido; fallo latched; configuración incompatible rechazada; semilla no reutilizada más allá de política.
- Demostración de que telemetría y control no invalidan los supuestos de privacidad o independencia.

## Afirmaciones que deben rechazarse o reformularse

| Frase | Reformulación aceptable |
|---|---|
| «Toeplitz garantiza aleatoriedad perfecta» | «La familia ofrece una cota de distancia bajo independencia y minentropía justificadas». |
| «Strong significa seed reutilizable indefinidamente» | «Strong permite una semilla pública; la reutilización requiere composición y horizonte». |
| «No hay correlación observada, luego son independientes» | «No se detectó dependencia con esas pruebas y resolución; el modelo requiere evidencia adicional». |
| «90B estima 0.99 por bit, así que tenemos 0.99n bits secretos cuánticos» | «La estimación pertenece a un procedimiento y modelo; debe justificarse su traducción a la minentropía condicional relevante». |
| «SHA elimina cualquier dependencia» | «Una función determinista no crea entropía y necesita hipótesis sobre la fuente y su uso». |
| «La semilla debe ser siempre secreta por el LHL» | «LHL strong admite semilla pública; algunos esquemas/rutas exigen secreto adicional». |
| «Pasar todos los tests certifica el extractor» | «Los tests detectan fallos concretos; la propiedad universal y el modelo se prueban por vías separadas». |

## Investigación posterior con mayor retorno

1. **Un contrato de entropía entre fuente y extractor.** Definir JSON con `source_model_id`, información lateral, `n`, cota condicional `k`, error de estimación, horizonte y presupuesto. Prohibir convertir automáticamente minentropía marginal en condicional. Integrarlo al prototipo CryptoSure.
2. **Prueba formal de Toeplitz universal₂.** Formalizar GF(2), pivotes de semilla y cardinalidad de fibras; después conectar con una librería probabilística y un LHL ya formalizado o verificado. El pequeño laboratorio exhaustivo no sustituye esta prueba general.
3. **Análisis directo de matrices fijas para modelos restringidos.** Para bits independientes sesgados, usar transformada de Walsh y enumeración de pesos del espacio fila. Para fuentes Markov, usar matrices de transferencia. Permite evaluar la vía AIS de postprocesado algorítmico específico.
4. **Semillas de refresco y fuga.** Comparar semilla nueva por bloque, seed persistente con horizonte, acumuladores de índices y fuentes independientes. Evaluar costo físico y supuestos antes del throughput.
5. **Optimización de presupuesto multiesquema.** Explorar una frontera salida/error/minentropía no suavizada/costos de semilla. No asumir que maximizar ratio de extracción minimiza costo de certificación.
6. **Información lateral de control.** Integrar simulador QRNG con un modelo explícito de telemetría pública y privada; distinguir impredecibilidad causal y secreto final.

## Límites pendientes, explícitos

No se ha verificado una implementación FPGA/RTL, no se ha demostrado un modelo físico real y no se ha solicitado interpretación a BSI/NIST. No se ha auditado cada errata/guía de certificación aplicable a un producto específico. El resultado cuántico se apoya en literatura primaria; el código del laboratorio es clásico. No se ha generado ni enviado ninguna comunicación externa.
