# Verificación consolidada

Ejecutada: 2026-11-14T11:58:49.062274+00:00

| Misión | Estado | Tests Python | Teoremas Lean | Mutantes rechazados |
|---|---|---:|---:|---:|
| business | PASS | 9 | — | — |
| cryptosure | PASS | 49 | — | — |
| formal_runner | PASS | 9 | — | — |
| extractors | PASS | 18 | — | — |
| qrng | PASS | 16 | — | — |
| jarvis | PASS | 48 | — | — |
| feedback_disclosure | PASS | 9 | — | — |
| formal | PASS | — | 47 | 5 |

**Total: 158 tests Python aprobados; 47 teoremas Lean y cinco mutantes incorrectos rechazados.**

Cada suite se ejecutó sobre una copia temporal. Todos los fuentes originales coincidían con los hashes del snapshot al terminar. El empaquetador vuelve a cotejarlos antes de crear el release. Los resultados completos, comandos, hashes y logs están en [results/checks/summary.json](results/checks/summary.json).

## Qué comprueba y qué no

- Tests unitarios, casos adversarios, enumeraciones finitas, invariantes y compilación de pruebas.
- No certificación, autenticidad de productor, validez del modelo físico ni demanda comercial.
- El verificador no descarga Lean: se utilizó la instalación aislada Lean 4.19.0.
- Las cinco mutaciones introducen errores concretos; no constituyen una medida completa de cobertura.
- Los tests Python formales comprueban el runner y cálculos de riesgo; la aceptación de los teoremas procede del kernel Lean.

## Resultados que se conservan

- CryptoSure: demo final-v2 y puente formal-v3; ambos preservan REVIEW donde hace falta juicio humano.
- QRNG: 24 escenarios × cuatro semillas × 524288 muestras, con parámetros sintéticos y cinco figuras.
- Extractores: enumeración exacta, modelo Markov y certificado de intervalos racionales de 201 hojas.
- JARVIS: 48 tests, concurrencia, replay, frontera temporal, reservas y exportación verificable.
- Fuga de feedback: nueve tests y probabilidades racionales exactas.

## Revisiones que produjeron correcciones

1. CryptoSure: límite agregado de snapshots; lectura única desde verificación hasta replay/diff; procedencia Git sin ejecutar filtros de working tree.
2. JARVIS: timestamp único para decisión y registro; replay independiente de materialización del ledger.
3. Runner Lean: mismos bytes para hash y compilación; estados por ejecución y VERIFIED sólo tras completar la campaña.
4. QRNG: dominio de aplicación de fórmulas lineales; distinción información causal/transcript completo.
5. Intervalos Markov: rechazo de floats en API exacta y verificación de campos derivados.
6. Empaquetado: rechazo de colisiones de archivo y enlace de fuentes publicados con hashes de pruebas.

Las revisiones son entre agentes. Queda pendiente revisión humana antes de emplear estos prototipos o interpretar los resultados como evidencia de un producto real.
