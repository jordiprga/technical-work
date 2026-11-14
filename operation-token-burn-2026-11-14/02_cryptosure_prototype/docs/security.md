# Modelo de amenazas y límites

## Activos y frontera de confianza

Se protegen la correspondencia entre bytes ensayados y exportados, la honestidad de
los estados técnicos y la capacidad de reconstruir una decisión. El autor del perfil,
los plugins instalados, Python, la biblioteca criptográfica, Git y el sistema operativo
pertenecen a la base de confianza. Ni un modelo de lenguaje ni un archivo importado
pueden convertirse por sí mismos en autoridad de certificación.

El adversario considerado puede entregar perfiles/JSON/artefactos malformados,
modificar una copia de un bundle e introducir rutas o contenido de presentación
malicioso. La implementación también detecta corrupción accidental de blobs.
No es un servicio multiusuario ni un sandbox contra otro proceso con el mismo UID.

## Controles implementados y probados

| Amenaza | Control | Evidencia de verificación |
|---|---|---|
| Rutas fuera de una raíz | Rechazo de rutas absolutas, `..`, segmentos vacíos y backslashes | Tests traversal |
| Symlinks | Rechazo en raíz, componentes y archivos; bundle sin symlinks | Tests import/bundle |
| Sustitución de entradas después de ingesta | Content-addressed store y snapshot de bytes antes de ejecutar | Test de modificación del origen |
| Alteración del store | Recalcular digest y tamaño antes de utilizar | Test store tampering → BLOCKED |
| Reescribir informe sellado | Verificación de todos los hashes | Test report tampering |
| Reescribir informe y todos los hashes | Pin externo del root; replay coteja también vistas derivadas | Test reseal + pinned root |
| Ejecución desde requisitos | Selección de plugins estáticos; no eval/exec/shell/subprocess en perfiles | Test tipo `shell` no ejecuta marker |
| Ambigüedad JSON | Rechazo duplicados, NaN/Infinity/overflow a infinito, schema types estrictos | Tests de parser |
| Falso PASS por checks ausentes | Requisitos documentales exigen revisión; ausencias/plugin desconocido → BLOCKED | Tests de estados |
| Inyección de Markdown/HTML | Escapado de datos dinámicos | Test de imagen remota, HTML y backticks |
| Fórmulas en CSV | Prefijo de texto ante `=`, `+`, `-`, `@`, incluyendo whitespace inicial | Test formula injection |
| Filtros Git configurados | No ejecutar `status`, `diff` ni comandos sobre el working tree; sólo rev-parse e índice | Fixture con fsmonitor/clean filter centinela |
| Consumo de recursos | Límites por archivo, total de snapshots, entradas a checks y bundle | Tests con límites reducidos |
| Sustitución del bundle tras verificar | Replay y diff consumen el mismo snapshot que se verificó contra el root | Tests que sustituyen el directorio completo después de verificar |

El control de rutas no es resistente a un atacante concurrente que sustituya
componentes entre comprobación y apertura (TOCTOU). Tampoco bloquea hardlinks,
dispositivos o montajes gestionados por otro actor fuera del modelo de confianza.
Los archivos importados y leídos deben ser regulares; el filesystem y su escritor
único son confiables. Producción necesita `openat`/`O_NOFOLLOW` o aislamiento
equivalente, UID dedicado y límites del sistema operativo.

La carrera específica entre verificar un bundle y volver a abrir sus datos sí está
eliminada: `read_verified_bundle` conserva los bytes cotejados con el sello original,
y replay/diff no vuelven a leerlos del disco. Sustituir después el directorio no cambia
el contenido sobre el que se informa. Esto no elimina las carreras generales de
apertura de rutas ni convierte el filesystem en un sandbox.

## Integridad no es autenticidad

Un hash conserva una relación matemática entre bytes y digest. No identifica a la
persona que creó el documento, la herramienta real ejecutada, el dispositivo medido
ni la legitimidad de un requisito. `root.sha256` viaja junto al bundle y puede ser
reescrito por el mismo adversario. `verify` sólo acredita autenticidad cuando se añade
un mecanismo externo, que esta versión no implementa; por ello devuelve siempre
`authenticity_verified:false`, incluso con un pin externo.

Un pin recibido por un canal fiable permite detectar cambios respecto de ese pin,
pero todavía no afirma quién aprobó la baseline. Un sistema de producción debe ligar
identidad, firma, propósito, versión de perfil, sujeto y caducidad de la aprobación.
No basta con añadir una firma a un JSON sin definir lo que firma el revisor.

## Proveniencia Git conservadora

Se registra HEAD, árbol e índice. El working tree no se inspecciona; `dirty:null` y
`working_tree_status:not_assessed` impiden confundir desconocimiento con limpieza.
La razón es práctica: inspecciones aparentemente inocuas pueden activar herramientas
configuradas por el repositorio. El prototipo no requiere una captura exacta del estado
para verificar los artefactos importados, que ya tienen hashes independientes.

El binario Git y la configuración del repositorio siguen formando parte de la base
de confianza; esta función no aísla un Git comprometido ni promete que la lectura de
configuración carezca de todas las rutas de inclusión. Sólo deben seleccionarse
repositorios públicos/sintéticos o explícitamente autorizados y confiables.

## Lo que queda fuera

- Exactitud, exhaustividad, licencia y vigencia del catálogo normativo.
- Corrección de modelos físicos, condicionamiento, estimación de entropía o resistencia
  a adversarios con información lateral.
- Firma/HSM, revocación, timestamping externo y transparencia de attestations.
- Concurrencia multiusuario, control de acceso, cifrado de repositorios y separación
  entre organizaciones o proyectos.
- Sandboxing de plugins arbitrarios: sólo se admite código incorporado y revisado.
- Cadena de suministro del toolchain y comparación bit a bit entre plataformas.
- Una decisión oficial de laboratorio, organismo o esquema de certificación.

## Criterios para pasar a piloto

Un piloto debe partir de datos públicos/sintéticos y una única familia de evidencia.
Se necesita revisión independiente del perfil, un entorno de ejecución aislado y
versionado, firma de las baselines por un responsable identificado, trazabilidad de
cambios y pruebas de restauración. La aprobación de un laboratorio se registra como
evidencia externa, nunca se infiere de los resultados técnicos de la herramienta.
