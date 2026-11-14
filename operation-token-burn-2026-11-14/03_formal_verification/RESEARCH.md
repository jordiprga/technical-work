# Dónde aporta valor la verificación formal

Fecha de investigación: 14-11-2026. Alcance: fuentes públicas y modelos originales; ningún dato de Quside. Las propuestas de ingeniería se distinguen de los resultados ya ejecutados.

## Decisión recomendada

Empezar con **contratos de control y refinamiento de implementaciones pequeñas**, donde una prueba universal descubre clases enteras de fallos y el vínculo con evidencias de evaluación es corto. Health-tests, bloqueo de salida, contadores, serialización y política de reseeding tienen mejor relación esfuerzo/valor inicial que intentar verificar de una vez toda una fuente física o una prueba completa de extractor cuántico.

No elegir un único lenguaje para todas las capas. Lean resulta adecuado para definiciones matemáticas, invariantes y teoremas reutilizables. Un flujo de verificación de C/Rust puede necesitar SAW, hax/Aeneas, F*, Rocq/Coq o análisis específico de código máquina. El valor comercial reside en conservar la correspondencia entre requisito, modelo, implementación y evidencia, con una revisión explícita de los supuestos.

## Qué se ha demostrado aquí

Los fuentes Lean se compilan de cero en un directorio temporal. El script audita todas las declaraciones `theorem`, no sólo ejemplos seleccionados. Los 47 teoremas resultantes usan exclusivamente los axiomas lógicos estándar `propext`, `Classical.choice` y `Quot.sound`, o ninguno. No usan `sorry`, axiomas propios ni evaluación nativa como oráculo de prueba. La lista exacta y hashes figuran en `results/verification.json`.

### Control del health-test

El estado abstracto contiene último símbolo, longitud de racha y fallo persistente. Sea `T_C(s,x)` la transición que actualiza la racha y activa el fallo si alcanza `C`. Sea `T*_C(s,xs)` la iteración.

1. **Persistencia:** `s.failed = true` implica que el estado final de cualquier traza permanece fallado.
2. **Ausencia de salida:** desde un estado fallado, cualquier traza produce una lista de `none` de igual longitud. La propiedad cuantifica sobre todos los sufijos finitos.
3. **Fronteras de bloque:** procesar `a ++ b` equivale a procesar `a`, conservar su estado y procesar `b`. Se prueba tanto para estado final como para secuencia de salidas.
4. **Cuenta exacta:** si el último símbolo ya es `x`, añadir `n` copias incrementa la racha abstracta exactamente en `n`.
5. **Detección:** `n>0 ∧ C≤n` implica fallo después de `n` símbolos idénticos desde el estado inicial.
6. **Apagado de fuente atascada:** después de `C>0` símbolos iguales, ninguna muestra posterior se libera durante esa época.

Esto cubre trazas arbitrarias, incluidas las correlacionadas, adversariales y no estacionarias. **No** se necesita IID para una propiedad determinista de control. En cambio, calibrar la probabilidad de falso positivo del umbral exige un modelo probabilístico distinto.

### Refinamiento finito y overflow

Un contador de racha matemático ilimitado no basta como evidencia de un circuito. Definimos un estado cuyo contador pertenece a `Fin(C+1)`, es decir, sólo puede valer entre cero y `C`. La función de abstracción conserva último símbolo y fallo, y reemplaza `run` por `min(C,run)`.

Se demuestra la conmutatividad:

```text
estado Nat ─── paso abstracto ───> estado Nat
    │ saturar                        │ saturar
    ▼                                ▼
estado Fin ─── paso saturado ────> estado Fin
```

Por inducción, la relación se mantiene para toda traza. El refinamiento conserva detección de fuente atascada y el fallo persistente. Además, la versión protegida sólo calcula `n+1` si `n<C`; se demuestra que `C<2^w` hace ese incremento representable en `w` bits. El contador requiere representar **C**, por lo que un diseño binario necesita al menos `ceil(log2(C+1))` bits, no simplemente `ceil(log2 C)` cuando C es potencia de dos.

**Límite actual:** `Fin` y la guarda son un modelo del diseño; todavía no se ha verificado código C/Rust/RTL ni el compilador que lo traduce. Tampoco se ha modelado corrupción del registro por fault injection. Una implementación debe preservar el orden actualizar→evaluar fallo→decidir salida; un pipeline necesita especificar qué muestras pendientes se invalidan.

### Errores que el paquete detecta

Los cinco mutantes de regresión son rechazados por Lean en ejecución real:

| Mutación | Fallo de producto que representa | Obligación que impide aceptarlo |
|---|---|---|
| Eliminar OR con fallo anterior | Un símbolo diferente borra el error | Persistencia para todo sufijo |
| Gate consulta estado anterior | Se libera la muestra que dispara el umbral | Semántica de salida posterior a transición |
| Cambiar `C≤count` por `C<count` | Detección una muestra tarde | Detección en exactamente C repeticiones |
| Activar fallo incondicionalmente | Un sistema siempre deniega y satisface seguridad vacuamente | Exactitud del latch y ausencia de alarma espuria |
| Incrementar incluso al cambiar símbolo | Rachas incorrectas producen alarmas espurias | Equivalencia con referencia independiente de historial |

También existen ejemplos comprobados de frontera de bloque: dos bloques de dos unos procesados con reinicialización pasan un umbral 4; concatenados correctamente fallan. El teorema de composición explica por qué mantener estado evita la discrepancia.

### Referencia independiente y progreso

`ReferenceRuns.lean` construye una referencia mediante inspección del historial en orden inverso: cuenta el prefijo de símbolos iguales y comprueba cada racha sin consultar el contador ni el flag del autómata. Se demuestra que el estado de la implementación representa exactamente esa referencia después de toda traza. Esta obligación detecta un contador que simplemente suma muestras y un detector que siempre falla, aunque ambos puedan satisfacer propiedades de bloqueo.

`StartupGate.lean` descarta las primeras N muestras mientras conserva el estado RCT. Se prueba que el contador restante es `max(N−n,0)`, que nunca se entrega una muestra durante ese intervalo, y que, una vez completado, la siguiente se entrega **si y sólo si** el health-test posterior al paso no está fallado. La política es deliberadamente conservadora: descarta también la muestra N. Configurar N=1024 no implementa por sí solo todo el startup normativo: aún falta APT, catálogo de fallos, interfaz y otras condiciones aplicables.

### Reconstrucción mediante telemetría

`FeedbackLeakage.lean` prueba la identidad entre diferencias de conteos de ventanas deslizantes y las muestras entrante/saliente. Dos secuencias con prefijo W idéntico y transcript de conteos idéntico son iguales. La versión finita sólo exige ventanas completas dentro de n muestras y evita asumir telemetría futura inexistente. La revisión independiente en `FEEDBACK_REVIEW.md` conecta esta inyectividad con el argumento de soporte del coordinador; la cota entrópica se mantiene como derivación matemática revisada, no como teorema Lean.

## Qué aporta más que una batería de pruebas

| Candidato | Obligación formal valiosa | Qué deben seguir midiendo las pruebas |
|---|---|---|
| RCT/APT y lógica de alarma | Invariantes para toda traza, umbrales y off-by-one, independencia de chunking | Temporización, pérdidas de muestra, fallos físicos, cobertura de modos de fallo |
| DRBG API | No Generate sin Instantiate; contador sin overflow; reseeding obligatorio; serialización válida | Integración OS, entropy callback, restore/fork, condiciones de carrera |
| Toeplitz | Convención de índices, producto GF(2), equivalencia acelerada/escalar, universalidad bajo semilla uniforme | Calidad y procedencia de semilla, independencia, ancho real, DMA |
| Conditioning criptográfico | Correspondencia exacta con función y padding; límites de entrada/salida | Fuente de entropía, supuestos criptográficos, implementación resistente a canales laterales |
| Máquina de estados del módulo | Sólo transiciones autorizadas; estado de error bloquea servicios; zeroization lógica | Efectos de compilador, memoria física y snapshots, buses/periféricos |
| Motor de evidencias | Ningún PASS sin test y evidencia vigentes; invalidez transitiva por cambio de hash | Integración, autenticidad del runner y revisión humana |

Un test vector prueba una entrada concreta; una prueba de equivalencia bit a bit puede abarcar todas las entradas de una función. Sin embargo, un teorema sobre la función equivocada no resuelve la evaluación. La inversión debe incluir revisión de especificación y correspondencia con el binario, no sólo producción de términos de prueba.

## Extractores: separar álgebra, probabilidad y adversario

Para una familia lineal tipo Toeplitz, conviene dividir el trabajo en cuatro obligaciones independientes:

1. Producto de matrices sobre GF(2) y convenciones de empaquetado/endianidad.
2. Propiedad de universalidad de la **familia** aleatoria. No atribuirla a cada matriz fija por separado.
3. Lema de extracción con distribución conjunta de fuente, semilla y side information explícita.
4. Contrato de integración que justifique esos supuestos para cada bloque consumido.

`Counterexamples.lean` sólo mecaniza consecuencias deterministas: una fuente contenida en una fibra produce salida constante; entrada repetida y semilla repetida dan salida repetida; una pequeña familia lineal admite un selector dependiente de la semilla que anula la salida. No contiene el Leftover Hash Lemma ni una prueba de min-entropía. Los lemas de fibra son elementales deliberadamente: aíslan dónde fallaría un contrato de independencia, sin disfrazarlos de una prueba probabilística profunda.

Una extensión de alto valor sería formalizar en Lean un **presupuesto de extracción**: dadas hipótesis verificables sobre min-entropía condicional y una cota de error, demostrar que las dimensiones configuradas satisfacen la desigualdad elegida. La aritmética de presupuesto puede automatizarse antes de mecanizar el teorema probabilístico entero. La justificación de las premisas seguirá en el expediente estocástico y experimental.

## Conditioning y DRBG: qué dice la literatura existente

Ye y colaboradores verificaron en Coq seguridad y correspondencia funcional de una versión de HMAC-DRBG en mbedTLS, con composición hacia compilación. Es un precedente real para conectar matemática e implementación. Su resultado tiene alcance delimitado: el juego usa estado inicial uniforme y adversario no adaptativo; la prueba de seguridad no cubre Instantiate, entradas adicionales, fork-safety ni canales laterales. La corrección funcional y la seguridad criptográfica cubren capas diferentes. No se debe convertir ese precedente en la afirmación «HMAC-DRBG está formalmente probado en cualquier integración». [Artículo, §§1, 3, 7–8](https://arxiv.org/pdf/1708.08542).

Para CryptoSure la oportunidad inicial sería conservar un contrato de composición: proveedor de entropía→Instantiate/Reseed→Generate→consumidor. Cada arista debe declarar longitud, calidad asumida, frescura, manejo del fallo y quién puede observar o controlar los datos. Un hash o DRBG determinista no crea entropía informacional total; la expansión busca indistinguibilidad computacional bajo supuestos, y no un aumento mágico de entropía física.

No intentaría portar a Lean una gran prueba Coq sólo por homogeneidad. Conservaría el verificador original y un adaptador de evidencias; una migración debe demostrar que compensa el coste de mantener dos formalizaciones.

## Evidencia normativa y límites de mapeo

SP 800-90B §4.3 exige manejo de fallos de health-tests; su §4.4.1 especifica el RCT. El modelo implementa una política conservadora de fallo persistente, bloqueo inmediato y gate genérico de startup. No incluye APT, el conjunto completo de pruebas de startup, pruebas bajo demanda, notificación externa, calificación de la fuente, ni el catálogo completo de modos de fallo. Por eso el estado de trazabilidad es **evidencia parcial de diseño**, nunca «90B conforme». [NIST SP 800-90B](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/nist.sp.800-90b.pdf).

El anexo público CCN-MEGA v1.0 enlaza health-testing con `I_HEALTH`; para DRNG genéricos y EDRNG, `.06` y notas 74–77 identifican modelo, seeding/reseeding, parámetros y vínculo con implementación. Es un lugar natural para evidencias formales, sin que el documento imponga Lean ni sustituya el juicio del evaluador. La propuesta aquí es un mapeo de ingeniería, no una determinación de conformidad. [CCN-STIC 2110, anexo 1, §§3.6, 6.4.1, 7.4.1](https://www.ccn-cert.cni.es/es/pdf/guias/series-ccn-stic/2000-organismo-de-certificacion/7340-ccn-stic-2110-mega-anexo-1-evidence-matrix-document/file.html).

Para FIPS 140-3, Common Criteria y EUCC no inventamos un requisito universal de verificación formal ni una equivalencia automática entre prueba y aprobación. La selección concreta depende de versión, nivel, perfil, objetivo de seguridad, componentes de assurance y decisiones del esquema. El paquete guarda un candidato de evidencia cuyo alcance un responsable técnico debe mapear al expediente concreto.

## Herramientas: elección por capa

| Herramienta | Uso razonable | Límite que conservar en el expediente |
|---|---|---|
| Lean 4 + Std/mathlib | Matemática, FSM, invariantes, parámetros, inducción | Modelo correcto no implica hardware correcto |
| hax/Aeneas→Lean | Vincular subconjunto de Rust a modelos Lean | Auditar traducción, modelos externos y subset soportado |
| SAW/Cryptol | Equivalencia de primitivas e implementaciones, bitvectors | Especificación y backend solver forman parte del argumento |
| Rocq/Coq + VST/FCF | Reusar pruebas existentes C y juegos criptográficos | Versiones, precondiciones y alcance exacto |
| F*/HACL*/EverCrypt | Reusar primitivas con evidencia existente | Adaptador, configuración y ensamblador fuera del alcance concreto |
| EasyCrypt | Juegos y reducciones criptográficas | No sustituye por sí mismo verificación de código de producto |

El manual actual de hax documenta `cargo hax into lean`, extracción parcial y escenarios de prueba. También advierte que compilar el modelo extraído no prueba automáticamente ausencia de panic. Esto permite plantear un puente Rust→Lean, pero el flujo no se ha ejecutado aquí. [hax, guía Lean](https://hax.cryspen.com/manual/lean/quick_start/).

SAW documenta verificación de programas y conexión con especificaciones Cryptol; el repositorio Cryptol incluye DRBG. HACL*/EverCrypt ofrecen otro precedente industrial, y EasyCrypt proporciona lógica para juegos probabilísticos. Son recursos para evaluar y fijar por versión, no dependencias ya integradas en este prototipo. [SAW](https://tools.galois.com/saw), [Cryptol specifications](https://github.com/GaloisInc/cryptol-specs), [HACL*](https://hacl-star.github.io/), [EasyCrypt](https://www.easycrypt.info/).

## Pipeline propuesto para evidencias formales

```text
Requisito versionado → interpretación revisada → propiedad formal → supuestos
                                               ↓
Commit + configuración → extracción/modelo → proof checker → manifiesto
                                               ↓
                        revisión de vínculo con implementación → expediente
```

El manifiesto debe conservar como mínimo: hash del requisito interpretado; commit/código; configuración; fuentes Lean; versión y hash del verificador; dependencias; lista de teoremas y axiomas; comando; código de salida; logs; alcance; exclusiones; fecha; identidad del runner. Un hash demuestra identidad de bytes, no veracidad ni autoría. Un fichero JSON que diga `verified` es una declaración; sólo adquiere fuerza cuando se verifica su procedencia y se reproduce la ejecución o se valida una attestation de un runner autorizado.

Antes de aceptar pruebas generadas por IA: fijar el enunciado esperado, revisar imports y axiomas, compilar en entorno limpio y aislado, y comprobar que el teorema aceptado coincide con la obligación original. Para un nivel superior, evaluar rechecking de artefactos e independent checkers. El manual de Lean diferencia aceptación del kernel, auditoría de axiomas y comprobaciones adicionales; no se ha ejecutado aquí un checker independiente. [Lean, validación de pruebas](https://lean-lang.org/doc/reference/latest/ValidatingProofs/), [lean4checker](https://github.com/leanprover/lean4checker), [comparator](https://github.com/leanprover/comparator/).

El auditor Python entregado **no es un sandbox para Lean hostil**. Es una herramienta específica para fuentes pequeños ya revisados; sus filtros léxicos no cubren todas las formas de metaprogramación, imports ni efectos IO posibles en un proyecto arbitrario.

## Backlog técnico priorizado

| Prioridad | Trabajo | Criterio de aceptación | Estimación orientativa |
|---|---|---|---|
| P0 | Revisión independiente del significado de estos teoremas | Dos revisores pueden relacionar cada variable con diseño y exclusiones | 1–2 días |
| P0 | Fixture Rust/C de RCT y gate | Equivalencia con modelo para todas las entradas dentro del contrato; counter width explícito | 3–10 días con tooling conocido |
| P0 | Completar startup y on-demand | Gate demostrado; añadir APT, interfaz y reset que no eluda política | 3–7 días |
| P1 | APT con índice/ventana y símbolo de referencia | Prueba de contador y fronteras para cualquier traza | 1–2 semanas |
| P1 | DRBG lifecycle | Generate/reseed/error/fork/restore definidos; contador y rechazo probados | 1–3 semanas |
| P1 | Extracción Toeplitz implementada | Equivalencia bitvector entre scalar y acelerada; semilla y dimensiones trazadas | 1–3 semanas |
| P2 | Presupuesto probabilístico | Enunciado de entropía condicional, adversario y composición revisados antes de mecanizar | 2–8 semanas |
| P2 | Runner formal dentro de CryptoSure | Evidencia invalidada por cambio de código, configuración o enunciado | 1–2 semanas |

Las duraciones son hipótesis de planificación para una persona con experiencia, no compromisos ni mediciones. La selección del primer cliente y su implementación pueden alterar completamente el coste. Criterio para detener una inversión: si no se puede obtener una especificación estable, un vínculo reproducible con implementación y una pregunta concreta del evaluador, una prueba más elaborada probablemente no resuelve el cuello de botella.
