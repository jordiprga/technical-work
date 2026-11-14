# Registro de revisión independiente

## R01 — MEMeC: portal y PDF no coinciden

- Observación: el portal CCN muestra v1.3.2; el PDF oficial enlazado consultado por agente 1 y coordinador muestra v1.3.3.
- Resultado: baseline corregida para preservar ambas observaciones. No se infiere aplicabilidad por fecha de rastreo.
- Estado: discrepancia documental identificada; decisión de esquema pendiente para un proyecto real.

## R02 — Modelo QRNG: dominio de la linealización

- Observación: las primeras fórmulas de varianza/correlación usan densidad en cero y ruido de observación blanco, aunque el simulador permite offset, objetivo distinto de 1/2, deriva y memoria.
- Acción: solicitado al autor marcar aplicabilidad y supuestos o adaptar el punto de equilibrio. Los resultados de escenarios fuera de hipótesis no pueden interpretarse como confirmación/refutación de esas fórmulas.
- Estado: en revisión de implementación.

## R03 — JARVIS: persistencia SQL

- Observación: en un borrador intermedio, INSERT de runs mostraba nueve placeholders y ocho valores.
- Acción: aviso al autor antes del cierre de su suite. No es conclusión sobre el entregable final.
- Estado: pendiente de comprobar versión final.

## R04 — Lean: frontera entre modelo y implementación

- Observación: prueba inicial sobre contador Nat; no cubre desbordamiento de un contador físico.
- Acción: solicitado refinamiento hacia contador saturado acotado y composición de las salidas, además del estado.
- Resultado comunicado por autor: extensión aceptada por Lean; coordinador verificará los artefactos finales.
- Estado: resultado formal adicional disponible, integración pendiente.

Este registro conserva hallazgos intermedios. Los resultados de cierre se documentarán en VALIDATION.md y no deben inferirse de estos estados provisionales.

## Cierre

R02, R03 y R04 quedaron resueltos y comprobados en las suites finales. R01 se conserva como discrepancia documental real, sin inferir edición aplicable. Ver [VALIDATION.md](VALIDATION.md) para correcciones adicionales y ejecución final.
