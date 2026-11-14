# Export, verificación y recuperación

El kernel genera exports JSON **versión 2**, con política, ledger, inbox, runs, nonces consumidos y eventos. `verify_snapshot.py` comprueba una cadena contra checkpoint y reconstruye la proyección de ledger/estados. No escribe una base restaurada ni autentica a un humano; es un verificador previo a restauración.

## Ejecutar el verificador

```bash
python3 src/verify_snapshot.py results/demo-final/export.json \
  --expected-head DIGEST_DE_UN_CHECKPOINT_CONFIABLE \
  --expected-policy DIGEST_DE_LA_POLITICA_APROBADA
```

Los argumentos son hashes hexadecimales de 64 caracteres. Copiarlos del propio export sólo comprueba consistencia interna; no establece autenticidad. En producción se obtienen de un checkpoint firmado o almacenamiento protegido fuera del dominio del VPS que se restaura.

La prueba guardada en `results/snapshot-verification.json` usa los propios ficheros de demo como checkpoint. Su alcance es deliberadamente una prueba de consistencia y reconstrucción; no evidencia de anclaje externo.

## Qué verifica

1. El hash de la política coincide con el esperado externamente.
2. Los eventos están numerados, encadenados y su último hash coincide con el checkpoint.
3. Cada inbox materializado coincide con el digest registrado y conserva estado `untrusted`.
4. Cada run tiene plan válido, digest correspondiente, proyecto, idempotency key, reserva y permiso coherentes con su evento de admisión.
5. No hay IDs de idempotencia ni nonces repetidos, perdidos o añadidos sin evento.
6. Las transiciones son `admitted→started→completed/failed`; el despacho precede a expiración.
7. Recalculando reservas y liquidaciones, no se excede el cupo en ningún prefijo de eventos y el ledger final coincide exactamente.
8. No hay filas operativas sin explicación en el historial ni eventos que referencien filas ausentes.

El verificador soporta **una revisión de política por export**. Un historial con varias políticas requiere conservar y verificar un registro de revisiones, sus aprobaciones y fechas; rechazarlo actualmente es una limitación explícita. Tampoco verifica recibos externos, firma de aprobaciones históricas ni bytes de artefactos que no figuran en este prototipo.

## Protocolo de restauración propuesto

1. Detener nuevas admisiones y despachos; conservar la cola y registrar punto de corte.
2. Exportar bajo transacción y crear backup consistente de SQLite mediante su API de backup. Con WAL no copiar sólo el archivo principal durante escritura.
3. Calcular manifest de export, objetos por digest, versión de código, schema y política. Crear checkpoint con identidad del proyecto, último número de evento y hashes; almacenarlo/firmarlo fuera del VPS.
4. En un host limpio, validar tamaño/formato, checkpoint, hashes de objetos y proyecciones antes de cargar datos. No ejecutar contenido importado como instrucciones o migraciones.
5. Crear nueva DB con migración revisada. Importar eventos y tablas validadas en una transacción; conservar la unicidad de `(project,idempotency_key)` y todos los nonces consumidos.
6. Rotar credenciales si el incidente pudo comprometer el host. Una clave HMAC nueva invalida tokens no consumidos; no elimina el ledger de nonces ni permite repetir efectos.
7. Runs `started` permanecen indeterminados para operación: no vuelven automáticamente a `admitted`. Se reconcilian con recibos/destino o con una decisión humana documentada. Runs `admitted` deben revalidar política, entradas y expiración al despachar.
8. Regenerar índices derivados; no importar embeddings como verdad. Hacer una consulta y una tarea sintética antes de reabrir admisiones.
9. Registrar duración, datos perdidos respecto al último checkpoint y discrepancias. Sólo entonces comparar con objetivos RPO/RTO.

## Versiones conservadas

`results/demo-v1`, `demo-v2` y `demo-v3` son intermediarios anteriores a la forma final del export/evento. Su conservación documenta evolución, no compatibilidad de restauración. `results/demo-final` es la demo correspondiente al verificador actual. No se implementó un migrador automático de esas bases anteriores.

## Límites materiales

Un checkpoint externo que sólo cubre eventos no autentica automáticamente todos los bytes de una base. El verificador reduce ese hueco reconstruyendo las tablas implementadas y contrastando campos ligados al historial, pero una restauración de producción deberá especificar el esquema completo y todas sus invariantes. Tampoco prueba que los eventos describan acciones reales: el productor del evento sigue siendo una raíz de confianza operacional.

La clave HMAC aleatoria de la demo nunca se exporta. Por tanto no se pueden revalidar sus MAC históricos después del proceso; eso es intencionado para no conservar credenciales y obliga a distinguir integridad del historial de autenticidad de una aprobación humana.
