# Revisión de procedencia: Lean → recibo → CryptoSure

Revisión independiente de JARVIS, 2026-11-14. Alcance: lectura de `03_formal_verification/run_checks.py`, recibo actual y `02_cryptosure_prototype/examples/demo_formal_bridge.py`; comparación SHA-256 de las seis fuentes. No se ejecutaron servicios externos ni se modificaron archivos de esas misiones.

## Conclusión de publicación

El bridge es publicable como **demostración de consistencia de un recibo**, conservando sus límites actuales. No ejecuta Lean, no autentica el productor, no verifica hardware y deja el requisito en `REVIEW` incluso cuando los checks de campos/hashes pasan. El recibo histórico no debe presentarse como ejecución nueva de Lean por CryptoSure ni como conformidad certificada.

La inspección de la evidencia disponible a las 11:54 encontró recibo `verified` fechado `2026-11-14T11:45:39.894263+00:00`, 47 teoremas y **6/6 hashes de fuentes coincidentes** con los archivos revisados. Esto confirma vinculación de bytes del recibo existente; la autenticidad de quién generó el recibo sigue fuera del bridge.

Se detectaron dos defectos del generador de recibos, comunicados al propietario y corregidos antes del cierre. El estado definitivo se registra al final de este documento. No son prueba de que la ejecución histórica conservada fuera falsa.

## FB-01: hash y compilación podían leer versiones distintas

La versión inspeccionada hacía `text = source.read_text()`, después `sha256(source)` abriendo el archivo otra vez, y compilaba una copia de `text`. Si otro escritor cambia el archivo entre ambas lecturas, se puede registrar hash de B mientras Lean compiló A. Es una carrera de asociación de evidencia, independiente de la corrección del kernel de Lean.

Corrección requerida: leer bytes una única vez, validar esos bytes, calcular su digest y escribir esos mismos bytes al directorio de compilación. Para mutaciones, partir del mismo snapshot revisado, no releer una fuente que pudo cambiar. Preservar hashes del runner y toolchain mejora la reproducción, pero no arregla por sí solo una carrera de lectura.

**Clasificación:** defecto real por inspección de flujo; no se realizó una explotación end-to-end ni se alteraron fuentes ajenas. Recomendado corregir antes de anunciar el runner como generador fiable de asociaciones fuente→prueba. El owner aceptó esta corrección.

## FB-02: un intento fallido podía dejar un recibo anterior visible

La versión inspeccionada no sustituía el recibo al comenzar. Un fallo previo a determinadas escrituras —por ejemplo en `source_sanity` o auditoría de axiomas— podía conservar un `verification.json` previo con `status=verified`. Además escribía `verified` antes de terminar la campaña de mutaciones. Un consumidor que mirase sólo ese estado, ignorando tiempo, proceso y logs, podía interpretar el último fichero como éxito del último intento.

Una prueba histórica sigue siendo histórica; no se invalida matemáticamente porque falle después una campaña diferente. El problema es la semántica de **último intento** y de **campaña completa**. Recomendación: ID de intento, estado inicial `in_progress`, escritura de fallo/incompleto y promoción a `verified` únicamente al terminar el alcance prometido. A largo plazo conservar recibos por run y un puntero latest explícito, sin sobrescribir historia.

**Clasificación:** defecto de estado/UX del runner; no demuestra una prueba Lean falsa. El owner anunció que retrasaría `verified` hasta terminar auditoría y mutaciones y evitaría conservar un éxito anterior como estado del intento nuevo.

## Límites explícitos que no bloquean esta demostración

- Un JSON inventado con `status=verified` y hashes correctos puede superar los checks literales del bridge y quedar en `REVIEW`. El propio perfil advierte que no autentica al productor. No promoverlo a `proof` de forma automática.
- Los timestamps del recibo no son sellos de tiempo confiables. Su antigüedad no puede decidirse como política de seguridad sin reloj/autoridad y criterio de vigencia.
- El digest del binario Lean y su versión no representan necesariamente todos los archivos de biblioteca/toolchain. Para una cadena reproducible completa se necesita manifest de distribución o imagen y dependencias, además del runner.
- `source_sanity` es una defensa conservadora para este corpus revisado, no un lexer completo ni sandbox. El script lo declara. Fuentes Lean hostiles necesitan aislamiento y revisión antes de ejecutarse.
- El bridge enumera fuentes leyendo el recibo y después importa éste al store. Una sustitución concurrente del recibo puede cambiar la lista entre lecturas; los checks posteriores usan los bytes importados y comparan los nombres enumerados, pero no garantizan que se haya enumerado toda la lista del recibo nuevo. Mantener entrada inmutable o enumerar desde el recibo ya importado sería el siguiente endurecimiento. La salida actual cuenta fuentes vinculadas y mantiene `REVIEW`; no declara exhaustividad normativa.
- Los bundles anteriores a una nueva ejecución son snapshots históricos válidos si sus propios hashes y replay coinciden. Conservarlos y etiquetarlos es correcto; una demo final puede importar el recibo nuevo sin borrar los anteriores.

## Contrato recomendado para una integración de producción

Separar `receipt_integrity`, `source_binding`, `producer_authenticated`, `toolchain_reproduced`, `kernel_check_reexecuted`, `mutations_passed`, `normative_mapping_reviewed` y `implementation_refinement_proved`. No resumir todos esos estados como un único PASS.

El recibo debería incluir run ID, inicio/fin, digest del runner, snapshot exacto de fuentes, manifest de toolchain, argumentos, entorno relevante, axiomas permitidos y observados, salida/exit status y alcance de mutaciones. La revisión humana debe conservar supuestos y propiedades exactas. Una firma autentica al productor del recibo; no demuestra que el modelo formal corresponda al dispositivo físico.

## Cierre

**FB-01 y FB-02 cerrados por inspección independiente del código corregido y su nuevo recibo.** El runner ahora captura bytes una vez y utiliza el mismo snapshot para hash, compilación y mutaciones. Publica un recibo `in_progress` por run antes de comprobar toolchain/fuentes, conserva recibos por ID, publica `failed` ante excepciones y sólo escribe `verified` tras completar el alcance solicitado. El campo `mutation_check_status` distingue una campaña omitida con `--skip-mutations` de una ejecutada.

Nuevo recibo: run `e6aec6d2dc1c4ef0ad741ae2a5cf4b4b`, inicio `2026-11-14T11:56:15.907932+00:00`, `verified`, kernel `passed`, mutaciones `passed` (5), 47 teoremas y 6/6 hashes de fuentes coincidentes. Evidencia estructurada: [formal-bridge-check.json](formal-bridge-check.json), incluyendo hashes del runner y recibo. El revisor no volvió a ejecutar Lean; comprobó la corrección del flujo y comparó los archivos del recibo generado por el propietario.

No queda un bloqueo de publicación dentro de este alcance, siempre que se mantenga `REVIEW` en el bridge y las limitaciones declaradas. Persisten requisitos de una cadena de producción: autenticación del productor, procedencia completa de toolchain, verificación de fuentes inmutables y vínculo del modelo con implementación y norma. La escritura atómica de cada recibo evita JSON parcial, pero dos ficheros separados no constituyen una transacción distribuida ni resuelven fallo total de disco; consumidores deben validar run ID, exit status y fecha.
