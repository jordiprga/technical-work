# Estado

2026-11-14 11:52 UTC. Código consolidado; documentación completa. Python 3.12.14,
sin dependencias externas para ejecutar. Sin acceso a datos privados, credenciales o PC local.

## Resultado verificado

- 49 tests de unittest aprobados; registro exacto en `results/test-log.txt`.
- Incluyen 3066 comparaciones exhaustivas RCT y 3076 APT contra modelos de referencia.
- CLI: validate, import, run, verify, replay, diff, plugins.
- Demo final: `results/final-demo-v2/bundle`, 1 requisito PASS técnico y 3 REVIEW.
- Root digest de demo final: `daef477740827338cfc490315dd79680f8bfd1490f5a3ac959823ac0d27fe44d`.
- Puente formal: `results/formal-bridge-v3/bundle`, recibo y seis fuentes Lean ligados por hashes;
  resultado REVIEW; CryptoSure no ejecuta Lean.
- Root digest de puente formal: `9544a2fad06b48b306cef8ba58569396d128669ede9042dc82e5c9c3b4209d06`.
- Ambas demos: replay coincide, mismo digest del código actual, verificación con pin externo.

## Revisión independiente incorporada

Root detectó riesgos de Markdown, orden CSV, agregación de estados y números JSON no finitos.
Agente de negocio revisó la consistencia entre perfiles y ejecuciones en diff.
Agente JARVIS detectó límites de recursos omitidos en replay y una carrera al reabrir
el bundle tras verificar. Se corrigieron y se añadieron regresiones.

Replay y diff consumen ahora los bytes exactos de un snapshot verificado, incluso si
después se sustituye el directorio completo. Git conserva sólo HEAD/árbol/índice y
declara `dirty:null`, evitando ejecutar filtros al examinar el working tree.

## Artefactos intermedios

`results/demo/` conserva la primera ejecución antes de cambios del renderer/motor.
Su sello de integridad sigue siendo comprobable, pero el replay con el motor final
puede diferir. La baseline de entrega es exclusivamente `results/final-demo-v2/`.
`results/final-demo/` y `results/formal-bridge/` conservan una consolidación anterior
al último control de coherencia de artefactos en diff; consultar arriba las rutas de las baselines actuales.

En la revisión final se añadió validación artefacto/ejecución también a diff: un blob
alterado y re-sellado con metadatos de ejecución intactos ya no puede aparecer como
baseline sin cambios. El test de regresión está incluido en los 49 ejecutados.

## Límites abiertos

No firma ni identidad autenticada; no dictamen normativo; no estimador 90B completo;
no aislamiento contra filesystem hostil concurrente; no concurrencia multiusuario;
no validación del toolchain completo. La separación entre integridad, experimentos,
juicio humano y decisión oficial está documentada en `docs/`.

Cierre11:57: el recibo formal se regeneró tras endurecer su runner. Se incorporó
como `results/formal-bridge-v3/`; seis fuentes Lean idénticas, recibo con run_id y
estados explícitos de kernel/mutaciones. Las versiones anteriores permanecen históricas.
