# Revisión de autorización, presupuesto y replay de JARVIS

Revisión independiente el 14-11-2026 de `06_jarvis_architecture/src/jarvis_kernel.py`, `src/verify_snapshot.py` y `SECURITY.md`. No se editaron fuentes de esa misión.

## Hallazgo confirmado y corregido

En la versión revisada inicialmente, `start()` leía el reloj para validar vigencia y `_event()` lo leía otra vez para registrar la transición. Si el primer valor era `expiry−1` y el segundo `expiry`, el kernel aceptaba `start` y guardaba un evento que el verificador independiente rechazaba por caducidad. Era una inconsistencia real de replay en un límite temporal, no una prueba de doble ejecución ni de acceso externo.

La reproducción inicial se conserva en `results/jarvis_time_boundary_review.json`. La misión JARVIS identificó simultáneamente el mismo problema y fijó un único timestamp de decisión para la guarda y el evento. `review_jarvis_boundary.py` reproduce el caso contra el código actual; la nueva evidencia se guarda con hashes de los fuentes en `results/jarvis_time_boundary_after_fix.json`.

## Invariantes examinados

- **Aprobación exacta:** el token liga plan, política, actor y vigencia. Cambiar recurso, argumentos, presupuesto o clave de idempotencia cambia el digest. La identidad del caller y la autoridad son supuestos de confianza del broker, reconocidos explícitamente.
- **Reintentos:** el duplicado con mismo plan devuelve el run existente; una clave reutilizada con plan distinto se rechaza. Un nonce nuevo no permite modificar un plan ya asociado a esa clave.
- **Admisión concurrente:** la reserva y la creación de run ocurren bajo transacción de escritura. La condición de presupuesto se comprueba al actualizar, evitando el patrón lectura→decisión→escritura no atómico.
- **Liquidación:** sólo un run iniciado puede liquidarse y su coste no supera la reserva. El cambio de estado impide una segunda liquidación mediante la misma API. La garantía presupone que nadie altera tablas fuera del broker.
- **Crash:** mantener la reserva tras un estado iniciado indeterminado conserva el límite. La política sacrifica reanudación automática hasta reconciliar efectos, coherente con la ausencia de exactamente-una-vez en sistemas externos.
- **Snapshot:** los checkpoints externos y replay de eventos comparan proyecciones; se informa explícitamente que no se reverifica autenticación humana ni efectos externos.

No se encontró otro bypass de autorización en el subconjunto examinado. Esta revisión no cubre un executor real, aislamiento OS, autenticación de endpoints, UI de aprobación o conectores, porque no existen en el prototipo. El propio módulo advierte que sus métodos de autoridad, start/finish y SQLite no deben exponerse directamente a workers.

## Límite importante para formalización futura

El argumento algebraico de presupuesto necesita una invariante relacional adicional: la reserva agregada debe corresponder a la suma de reservas de runs activos, y cada liquidación debe retirar exactamente un run. La exclusión transaccional y el estado por run son la implementación actual de esa obligación. Una prueba puramente aritmética de `S+R≤C` que asuma `r≤R` no demuestra por sí sola que un scheduler o un restore mantengan esa relación.

Los tests concurrentes son evidencia finita; una prueba universal debería modelar transacciones exitosas como pasos atómicos y verificar refinamiento del storage/restore. La documentación ya separa este nivel de la seguridad del proveedor de modelos y del gasto real.
