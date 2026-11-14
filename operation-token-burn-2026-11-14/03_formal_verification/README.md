# Verificación formal para certificación criptográfica

**Resultado ejecutado:** Lean 4.19.0 ha aceptado **47 teoremas** sobre health-tests, control de salida, contador finito, startup, especificación independiente de rachas y reconstrucción por telemetría. Cinco mutaciones incorrectas fueron rechazadas. No se ha probado la entropía de una fuente física ni la conformidad de un producto.

## Artefactos

- `HealthGate.lean`: RCT binario genérico, fallo persistente, bloqueo de salidas, composición por bloques y detección de fuente atascada.
- `SaturatingCounter.lean`: refinamiento de contador ilimitado a `Fin(C+1)`; incremento protegido y condición para evitar overflow en un ancho de palabra elegido.
- `Counterexamples.lean`: límites deterministas de extractores, fuente adaptada a semilla y repetición de entradas.
- `ReferenceRuns.lean`: equivalencia exacta con una referencia que cuenta rachas inspeccionando el historial; excluye una implementación que siempre deniega.
- `StartupGate.lean`: descarte de muestras de startup, persistencia de salud y progreso condicionado a ausencia de fallo.
- `FeedbackLeakage.lean`: identidad de ventanas, reconstrucción e inyectividad del transcript rolling, incluidas observaciones finitas.
- `run_checks.py`: compilación limpia, auditoría transitiva de axiomas, hashes y cinco pruebas de mutación.
- `test_proof_runner.py`: tres regresiones de procedencia; captura única de bytes y recibos fallidos que no conservan un estado VERIFIED anterior.
- `results/verification.json`: evidencia de ejecución, versión exacta, hashes y lista de teoremas.
- `results/mutation_checks.json`: rechazo efectivo de cinco errores de implementación introducidos deliberadamente.
- `RESEARCH.md`, `TRACEABILITY.csv`, `SOURCES.md`: análisis, obligaciones y fuentes.
- `FEEDBACK_REVIEW.md`, `EXTRACTORS_REVIEW.md`: revisión cruzada independiente de los resultados de coordinación y extractores.
- `JARVIS_REVIEW.md`: revisión de autorizaciones y regresión temporal reproducida y corregida por la misión JARVIS.
- `RCT_CALIBRATION.md`, `rct_risk.py`: análisis exacto del riesgo acumulado de alarmas en un modelo IID explícito y cota bajo premisas condicionales; seis tests.

## Reproducción

Con Lean 4.19.0 instalado:

```sh
python3 run_checks.py --lean /ruta/a/lean-4.19.0-linux/bin/lean
```

En este entorno se usó:

```sh
python3 run_checks.py --lean /tmp/cryptosure-lean/lean-4.19.0-linux/bin/lean
```

`lean-toolchain` fija la versión. `lake build` ofrece la compilación convencional; el script adicional audita axiomas y comprueba que regresiones deliberadas invalidan las pruebas. No requiere mathlib ni paquetes Python.

Cada intento crea un recibo con `run_id`; `results/verification.json` es la última instantánea. Empieza como `in_progress`, pasa a `failed` si hay un error y sólo termina `verified` después de los checks solicitados. Las mutaciones pueden omitirse explícitamente, en cuyo caso el campo correspondiente dice `skipped`. Hash, compilación y mutantes usan los mismos bytes capturados; el runner no vuelve a leer una fuente para atribuirle el hash de otra versión.

Las pruebas Python complementarias se ejecutan con `python3 -m unittest -v test_proof_runner.py test_rct_risk.py`. Las tres pruebas del runner usan copias temporales; no reemplazan el recibo formal de la entrega.

## Lectura correcta del resultado

Los teoremas cuantifican sobre cualquier secuencia finita de bits y cualquier umbral natural. Para relacionar el RCT con SP 800-90B se usa un umbral operativo `C ≥ 2`. La política local clasifica todo fallo como persistente dentro de una época sin reset. La especificación normativa admite diseños que distinguen fallos intermitentes y persistentes; el modelo no pretende cubrirlos todos.

El contador `Fin(C+1)` demuestra representabilidad y saturación en el modelo. El teorema `guarded_increment_fits` exige `C < 2^w` y que sólo se evalúe `n+1` bajo la guarda `n<C`. Aún falta probar correspondencia con una implementación C/Rust/RTL y con su semántica de memoria, concurrencia e interfaces.

Los supuestos probabilísticos de una fuente y la independencia de la semilla de un extractor son obligaciones distintas. Pasar un health-test no demuestra aleatoriedad; probar su lógica tampoco.
