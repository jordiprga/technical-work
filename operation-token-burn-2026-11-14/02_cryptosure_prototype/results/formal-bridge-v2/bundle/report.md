# CryptoSure — informe de evidencia

**DEMOSTRADOR. No constituye certificación, validación ni decisión de conformidad.**

Perfil: cryptosure\.formal\-bridge\-demo / 1\.0
Ejecución UTC: 2026\-11\-14T11:52:29\+00:00
Resultado técnico: **REVIEW**

PASS sólo indica que los checks implementados aprobaron sobre los bytes incluidos.
REVIEW requiere evaluación humana. BLOCKED señala evidencia ausente, inválida o plugin desconocido.
FAIL señala al menos una comprobación fallida. Ningún estado sustituye al laboratorio u organismo.

La verificación de hashes demuestra consistencia con un root digest confiable, no autoría, verdad o adecuación.
El root.sha256 dentro del mismo bundle no es por sí solo un ancla de confianza externa.

## Matriz de requisitos

| Requisito | Cláusula de referencia | Estado | Checks | Evidencias |
|---|---|---|---|---|
| DEMO\.FORMAL\.001: Revisar teoremas, axiomas, toolchain y vínculo con implementación | Demostración de integración; ninguna cláusula normativa | REVIEW | receipt\-status\-declared:PASS, source\-digest\-0:PASS, source\-digest\-1:PASS, source\-digest\-2:PASS, source\-digest\-3:PASS, source\-digest\-4:PASS, source\-digest\-5:PASS | formal\-receipt, formal\-source\-0, formal\-source\-1, formal\-source\-2, formal\-source\-3, formal\-source\-4, formal\-source\-5 |

## Detalle de comprobaciones

- receipt\-status\-declared: **PASS**. Comparación literal de un campo JSON; no evalúa expresiones\.
- source\-digest\-0: **PASS**. Comparación literal de un campo JSON; no evalúa expresiones\.
- source\-digest\-1: **PASS**. Comparación literal de un campo JSON; no evalúa expresiones\.
- source\-digest\-2: **PASS**. Comparación literal de un campo JSON; no evalúa expresiones\.
- source\-digest\-3: **PASS**. Comparación literal de un campo JSON; no evalúa expresiones\.
- source\-digest\-4: **PASS**. Comparación literal de un campo JSON; no evalúa expresiones\.
- source\-digest\-5: **PASS**. Comparación literal de un campo JSON; no evalúa expresiones\.

## Límites del perfil

Se verifica consistencia de hashes y campos declarados\. CryptoSure no ejecuta Lean, no autentica al productor del recibo y no demuestra correspondencia con hardware o requisitos normativos\.

## Proveniencia

- Tool version: 0\.1\.0
- Tool source SHA-256: `0ac8a6abaf155978ee5315d16e135b891da7218f3453bcc012229f3df80da583`
- Profile SHA-256: `c73ede951be3b9fda9b0694e1275649de38bdfa186732d907edebb24e766c176`
- Git: \{'requested': False, 'status': 'not\_captured'\}
