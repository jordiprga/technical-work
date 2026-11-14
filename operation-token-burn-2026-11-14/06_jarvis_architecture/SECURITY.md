# Seguridad y argumentos de corrección

El diseño protege la autorización de Jordi y la integridad de sus proyectos frente a entradas maliciosas, fallos de agentes y reintentos. No presupone que un modelo pueda distinguir siempre instrucciones legítimas de prompt injection. La frontera de seguridad está en procesos, credenciales, políticas y validadores ajenos al modelo.

## Activos y adversarios

Activos: conocimiento revisado, secretos de futuros conectores, presupuesto, reputación, integridad de código, historial de decisiones y capacidad de revocar acciones. No forman parte del sistema el PC local, los sistemas de Quside ni sus datos privados.

Adversarios/modelos de fallo: documento web hostil; paquete o repositorio malicioso; agente que alucina o obedece instrucciones inyectadas; worker comprometido; canal móvil comprometido; proveedor caído; duplicación y reorder de mensajes; reloj incorrecto; operador con acceso al host; error de configuración. La protección ante un administrador hostil requiere controles fuera del VPS y queda fuera de lo demostrado por el prototipo.

| Escenario | Control propuesto | Evidencia actual / pendiente |
|---|---|---|
| Documento ordena exfiltrar | Contenido marcado como dato, herramientas de salida ausentes, proxy y ACL por conector | Test inbox no crea acciones; aislamiento real pendiente |
| Agente se atribuye identidad de Jordi | Caller proviene de mTLS/sesión autenticada del broker; plan sólo declara actor | Test de caller mismatch; autenticación real pendiente |
| Cambio del diff después de aprobación | Digest exacto de plan, inputs y política; revalidación al ejecutar | Tests de todos los campos y política |
| Repetición de una aprobación | Nonce único consumido transaccionalmente y clave de idempotencia | Tests de replay, colisión y duplicado |
| Dos workers gastan el último cupo | Reserva bajo transacción y CAS/locking | Test con 12 threads; gateway de coste pendiente |
| Crash después de enviar acción | Estado indeterminado, recibo/idempotencia del destino, no retry ciego | Test de reserva retenida; ningún destino externo implementado |
| Path traversal/symlink | Identificadores virtuales; executor futuro con dirfd, nofollow y mount acotado | Traversal léxico probado; symlinks no aplican al kernel |
| Política cambia con una tarea en cola | Hash de política y expiración reevaluados al despacho | Tests de revocación y caducidad al start |
| Registro manipulado | Hash chain + checkpoints autenticados fuera del host | Alteración/truncación probadas; anclaje externo no implementado |
| VPS cae o se pierde | Backup consistente, objetos por digest, restore ensayado | Export JSON funcional; restore operativo pendiente |
| Dependencia ejecuta código al instalar | Imagen fijada, lockfile, build sin secretos, egress mínimo | Prototipo stdlib; sandbox deployment pendiente |
| Telegram repite o suplanta interacción | Dedup update ID, verificación webhook, sesión web para decisión protegida | Sólo diseño; bot ausente |

## Capacidades y permisos

Una capacidad es un conjunto acotado `(principal, acción, proyecto, recurso, límites, vigencia)`. No se acepta una descripción textual del agente como permiso. Un grant de lectura no permite cambiar políticas, importar conectores o crear un grant hijo. Las delegaciones tienen profundidad, alcance y presupuesto no mayores que los del padre.

Clases iniciales:

| Clase | Ejemplos | Política |
|---|---|---|
| A: lectura pública/datos ya autorizados | Buscar papers, leer artefactos del proyecto | Permiso permanente acotado; no preguntar por cada lectura |
| B: trabajo reversible en staging | Generar nota, parche o simulación | Permiso de proyecto y presupuesto; revisión para promover según política |
| C: cambios protegidos | Promoción a rama revisada, cambio de política, habilitar conector | Mostrar resultado concreto y aprobar alcance exacto |
| D: efectos externos | Mensajes, publicación, compras, operaciones financieras | Ausentes/denegados en esta operación; habilitación futura independiente |
| E: acceso excluido | PC local, Quside privado | No hay mount, credencial, agente ni ruta de acceso |

La implementación simplificada concede `research.summarize` y `code.propose_patch` bajo política permanente; `test.run` y `artifact.stage` exigen token sintético de aprobación. Esta separación demuestra el mecanismo, no prescribe que Jordi tenga que aprobar cada prueba en producción. Un proyecto puede preautorizar pruebas seguras en sandbox mediante una política revisada y el mismo ledger.

## Protocolo de aprobación exacta

1. El agente produce un plan tipado y artefactos inmutables. El broker valida esquema, ruta virtual, identidad, capacidades y límites.
2. La UI renderiza una vista canónica del plan y su digest. Para código se muestra el diff completo, base commit y resultados de tests; no sólo el resumen del agente.
3. Un servicio de autoridad autenticado recibe la decisión explícita. Firma `{plan_hash, policy_hash, actor, approved_by, not_before, expires_at, nonce, version}`.
4. El broker verifica firma/MAC, vigencia, identidad, política y digest. Consume nonce, reserva cupo y crea el run en una única transacción.
5. Antes de despachar revalida vigencia y política. El executor comprueba que el material real coincide con los digests y el estado/base version esperado. Si cambió, se reconstruye propuesta.
6. El recibo de ejecución se asocia al run y a su idempotency key; no se interpreta «aprobado antes» como permiso global.

El token no debe contener secretos ni permitir acciones adicionales. La caducidad se compara con reloj del broker, no con tiempo propuesto por el agente. Sincronización temporal y detección de saltos grandes son requisitos operativos. Para deadlines internos de proceso se usa también reloj monótono; timestamps UTC sirven para persistencia y auditoría.

El prototipo usa HMAC-SHA-256 con clave aleatoria en memoria. El signer y verifier comparten poder de emisión: por tanto no hay no repudio ni separación criptográfica entre ambos. Producción puede usar un firmante separado y verificación por clave pública (p. ej. Ed25519 con biblioteca auditada), más autenticación fuerte de la persona. La seguridad de la firma no corrige una UI que muestra otro contenido.

## Aislamiento de ejecución

Cada worker recibe una imagen o sandbox, UID sin privilegios, checkout propio, límite de CPU/RAM/PIDs, filesystem sólo lectura salvo outputs, y sin socket Docker del host. Nunca montar todo `/home`, un gestor de contraseñas o un directorio de credenciales. Los secretos de futuro acceso a modelos/conectores se quedan en gateway; si una herramienta exige uno dentro del worker, se limita a esa tarea y se acepta explícitamente la ampliación del dominio de confianza.

El host bloquea egress no autorizado, incluidas redes privadas, metadata cloud y DNS no autorizado. Un allowlist por dominio debe resolver el problema de redirecciones, rebinding y canales alternativos. El proxy de shell no sustituye políticas para MCP, web search, navegador y apps. Los conectores se registran por capacidades; cualquier herramienta nueva empieza deshabilitada.

Un executor de archivos futuro no debe confiar sólo en `Path.resolve()` seguido de `open()`: existe una carrera TOCTOU si un atacante cambia symlinks entre ambas operaciones. Usar directorio abierto de confianza, operaciones relativas con nofollow/dirfd o primitives específicas del sistema, y comprobar montajes. Los recursos virtuales del prototipo no se traducen a rutas reales; las pruebas no afirman resolver esa carrera.

## Semántica de fallos

La admisión es transaccional; un fallo no deja un nonce consumido sin run ni una reserva sin evento. `start()` es una reclamación única; una segunda llamada falla. Un crash después de `start()` conserva estado y reserva, porque el sistema no sabe si un efecto pudo ocurrir. Liberar esa reserva exige reconciliación fiable.

Esto proporciona **a lo sumo una transición de despacho por run en el broker**, no exactamente una ejecución de un efecto externo. Un sistema remoto puede recibir la solicitud y perder la respuesta; sólo el propio destino puede hacer idempotente ese efecto, o permitir consultarlo por clave. El sistema prioriza evitar duplicaciones sobre disponibilidad automática cuando no hay evidencia suficiente.

## Invariante de presupuesto: argumento algebraico

**Resultado demostrado dentro del modelo del ledger**, con DB transaccional correcta y todas las mutaciones a través de esta API:

Sea `C` el cupo fijo, `S` el gasto liquidado y `R` la reserva. Se mantiene además la correspondencia `R = suma de reserved_run para runs en admitted o started`. Inicialmente no hay runs activos, `S=R=0` y `C>0`.

- Admitir una tarea con `r>0` requiere `S+R+r≤C`; cambia `R` por `R+r`.
- Liquidar una tarea reservada por `r` con coste `0≤a≤r` cambia `(S,R)` por `(S+a,R-r)`. La precondición `started` y la correspondencia con runs activos implican `r≤R`; por tanto la resta no vuelve negativa la reserva. La suma cambia en `a-r≤0`.
- Admitir añade exactamente una reserva a ambos lados de la correspondencia; iniciar sólo cambia `admitted` por `started`; liquidar quita exactamente esa reserva de ambos lados. El estado del run impide segunda liquidación; la transacción serializa admisiones concurrentes.

Por inducción sobre transacciones exitosas, `0≤S`, `0≤R` y `S+R≤C`. La suite concurrente es evidencia experimental adicional, no la prueba de todos los schedules del motor SQLite.

**Lo que no demuestra:** gasto monetario real inferior a `C`; el proveedor puede cobrar más de lo reservado si el gateway no aplica máximos. Tampoco protege frente a un administrador que edite las tablas. La moneda/tarifa y tokens de entrada/salida deben contabilizarse por separado en producción; una unidad sintética «token» no es una unidad de coste universal.

## Integridad, autenticidad y verdad

Un hash demuestra igualdad de bytes respecto a otro hash confiable. No demuestra que la fuente sea correcta, que una persona la haya aprobado ni que un experimento mida lo que afirma. Un hash chain interno puede detectar corrupción accidental, pero un atacante con control total puede reescribir eventos, recalcular la cadena y presentar una historia coherente falsa.

Un checkpoint confiable externo permite detectar divergencia del prefijo/historial que cubre, incluida truncación. El checkpoint también necesita protección de integridad, fecha y asociación al proyecto. Copiar el checkpoint a otra tabla de la misma DB no crea una nueva frontera de confianza.

La verificación `verify_audit()` comprueba sólo la cadena de eventos. El verificador independiente adicional `verify_snapshot.py` reconstruye las proyecciones implementadas (inbox, runs, nonces y presupuesto) y detecta discrepancias respecto al historial y los checkpoints suministrados. Su alcance se limita a un historial con una sola política; no revalida aprobaciones humanas ni recibos externos. El protocolo completo y sus límites están en [RESTORE.md](RESTORE.md).

## Requisitos antes de producción

No exponer este módulo Python a agentes o a HTTP directamente. Añadir autenticación, autorización del endpoint, validación de política, límites de payload, rate limits, migraciones de schema, cifrado/backup y separación real de procesos. `Authority.sign`, `Kernel.start`, `Kernel.finish` y acceso SQLite son interfaces de confianza. Los workers sólo deben poder proponer acciones y enviar resultados, nunca marcarse a sí mismos como aprobados o completados.

Realizar pruebas de integración de sandbox/egress, intento de lectura de mount excluido, prompt injection de corpus sintético, crash entre cada transición, restore desde backup, rotación/revocación de claves, actualización de política con runs activos y reconciliación de efectos. Publicar un threat model no equivale a superar esas pruebas.
