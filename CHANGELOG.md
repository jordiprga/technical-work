# Changelog

## 0.2.0 — 2026-11-14

- Instalación editable con setuptools, dependencias científicas declaradas y extras `ui`/`dev`. Comando `entropy-oracle`, ejecución como módulo y wrapper `benchmark.py` equivalentes.
- Entrada de secuencias discretas `.bin`, `.npy`, `.csv` y `.txt` con alfabeto explícito, validación estricta, orden temporal preservado y hash del archivo original. Los binarios admiten `uint8`, `uint16le` y `uint32le`.
- Resultados de fuentes importadas guardados por defecto en `local-results/`, excluido de Git junto con `data/`. La longitud real sustituye a `--n`; repetir semillas sobre un archivo no equivale a réplicas independientes de la fuente.
- Separación explícita en dos etapas: todos los modelos, checkpoints, selección y pesos del ensemble se fijan usando train/validación antes de abrir el test final.
- MLP con actualizaciones solo sobre train, selección por log-loss de validación temporal, early stopping y restauración del mejor checkpoint. Se conserva el presupuesto fijo cuando no se suministra validación.
- Resultados schema 2 con predicciones completas de test en NPZ sin pickle, hashes de integridad, índices originales y procedencia del código. `scripts/verify_results.py` recalcula accuracy, log-loss y Brier y comprueba correspondencia con los JSON.
- Bootstrap de bloques desactivado para fuentes con estacionariedad falsa o desconocida; las cotas martingala permanecen disponibles con su objetivo inferencial declarado.
- Límites preventivos de ejecución: alfabeto máximo 4096 y presupuesto estimado de asignación densa de 2 GiB, sin remapeo automático de símbolos.
- Nuevas ejecuciones reales en `results/v2/`: no lineal, IID y AR(1) cuantizado, semillas 211, 229 y 247; curvas de aprendizaje separadas con semilla 201. Resúmenes y contrastes se derivan de los artefactos guardados.
- Interfaz para datos importados, auditoría y exploración de resultados; pruebas ampliadas de matemáticas, causalidad, parsing, selección temporal, CLI y UI.
- Workflow GitHub Actions para Python 3.11 y 3.12 con PyTorch CPU. Se añadió la configuración; no se presenta como una ejecución remota aprobada ni se afirma publicación del repositorio.

Los artefactos v0.1.0 se conservan. Como las nuevas ejecuciones también utilizan otras semillas, comparar sus cifras directamente no aísla el efecto de las modificaciones de implementación.

## 0.1.0 — 2026-11-14

Primer prototipo, conservado en el commit `bd7e077`:

- Catorce predictores, diez fuentes controladas, evaluación temporal, selección por validación, ensemble probabilístico e interfaz Streamlit.
- GRU, Transformer causal y flujo spline condicional con masas discretas calculadas por diferencias de CDF.
- Experimentos principales con semillas 11, 29 y 47 y curvas de aprendizaje con semilla 101.
- MLP con presupuesto fijo sin checkpoint temporal; esta limitación corresponde al protocolo histórico, no al actual.
- JSON con métricas completas y una traza parcial de hasta 1024 probabilidades; sin archivo completo de predicciones para auditoría posterior.

Ninguna versión es una implementación normativa SP 800-90B/AIS 31 ni certifica una cota inferior de min-entropía de una fuente real.
