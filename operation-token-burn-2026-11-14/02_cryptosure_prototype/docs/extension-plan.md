# Extensión por estándares y backlog

El núcleo trata requisitos, artefactos, ejecuciones y relaciones. Cada estándar añade
un paquete **versionado y revisado** que define alcance, referencias normativas,
reglas de aplicabilidad, evidencias esperadas y qué decisiones siguen siendo humanas.
No se intenta inferir equivalencia normativa por parecido textual de dos cláusulas.

## Adaptadores propuestos, no implementados

| Familia | Automatización razonable del primer piloto | Juicio que permanece humano |
|---|---|---|
| SP 800-90B | Ingesta y formato de datasets; hashes; ejecución aislada de una versión fijada de la herramienta NIST; parseo de resultados; trazabilidad a configuración | Modelo de fuente, justificación IID/no-IID, correspondencia con producción, entorno, fallos y estimación defendible |
| FIPS 140-3 | Inventario de módulos/builds/entornos; resultados de tests; dependencias; evidencias de self-tests y gestión de configuración | Límites del módulo, requisitos aplicables, interpretación de IG, revisión del laboratorio y decisión CMVP |
| Common Criteria / EUCC | Grafo ST → SFR/SAR → diseño → tests → incidencias → revisiones; control de versiones y cobertura declarada | Adecuación del ST, profundidad de análisis, vulnerabilidades, potencial de ataque y aceptación del esquema |
| CCN-MEGA/MEMeC | Catálogo autorizado por versión, inventario de entregables, estado de revisión y exportación offline | Interpretación del alcance y requisitos del proceso aplicable, interlocución con organismos y acceso autorizado |

Estos son diseños de integración, no afirmaciones de que cada esquema acepte el mismo
formato de evidencia. No se han consultado materiales privados o restringidos.

## Backlog ordenado por reducción de incertidumbre

| Prioridad | Trabajo | Criterio de aceptación |
|---|---|---|
| P0 | Acordar un flujo concreto con un evaluador usando material público | Perfil pequeño con revisión firmada, alcance y criterios de evidencia explícitos |
| P0 | Adaptador NIST 90B con versión fijada, container y datasets públicos | Inputs/outputs exactos conservados; resultados coinciden con ejecución manual controlada; fallos y timeouts producen BLOCKED |
| P0 | Manifest de toolchain y build reproducible | Python, librerías, imagen y plugins identificados; runner ajeno reproduce un bundle |
| P0 | Esquema de aprobaciones humanas | Aprobación ligada a root digest, sujeto, ámbito y versión; cualquier cambio relevante invalida la reutilización |
| P1 | Firma y verificación portable de attestations | Cambio de firma, identidad o contenido se rechaza; root de confianza documentado |
| P1 | Store transaccional y aislamiento por proyecto | Concurrencia, crash recovery y restauración ensayados sin mezcla de evidencias |
| P1 | Reglas de aplicabilidad con razones verificables | NOT_APPLICABLE sólo tras razón y aprobación; nunca por silencio del perfil |
| P1 | Diff por grafo de dependencias y versión normativa | Cambiar una entrada enumera sus dependientes; dos requisitos textualmente similares no se fusionan solos |
| P1 | Exportación consensuada con laboratorio | El evaluador reconstruye una revisión sin acceso al servicio del fabricante |
| P2 | OCR/extracción asistida por LLM | Sólo genera propuestas con fragmento y fuente; reviewer debe aceptar el requisito antes de activarlo |
| P2 | UI de revisión y colaboración | Comparación de versiones, comentarios y firmas; el estado técnico sigue separado de la decisión humana |

## Un MVP de tres ingenieros

Propuesta técnica, no estimación contractual: ingeniero A conserva motor, schemas y
proveniencia; B implementa un adaptador 90B y fixtures de referencia; C construye
revisión, diff y exportación. Un especialista de certificación valida alcance y
criterios; no se presupone que tres desarrolladores sustituyan ese rol.

La primera medida de éxito debería ser una revisión de baseline repetible y una
reducción observada de trabajo de preparación/corrección, no «porcentaje de estándar
automatizado». Métricas útiles: tiempo de regenerar un expediente, errores detectados
antes de entrega, revisión humana restante, tasa de evidencia rechazada y reproducción
independiente por el evaluador. Las metas comerciales deben validarse en pilotos.

## Puente con Lean

`examples/demo_formal_bridge.py` importa un recibo producido por la misión de
verificación formal y liga sus digests de fuentes a los bytes importados:

```bash
PYTHONPATH=src python3 examples/demo_formal_bridge.py \
  --formal-root ../03_formal_verification \
  --out /tmp/cryptosure-formal-nuevo
```

El resultado queda REVIEW aunque todos los checks aprueben. El plugin sólo comprueba
campos declarados y consistencia de hashes: no ejecuta Lean ni prueba que los teoremas
describan el firmware, RTL o hardware comercial. El recibo, las fuentes, el log del
kernel y la relación con el requisito son piezas distintas de la evidencia.
