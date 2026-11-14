# JARVIS — Operation Token Burn

Investigación y prototipos preparados para **Jordi Prieto Gallego**, el 14 de noviembre de 2026, mediante seis agentes especializados y un coordinador. Sólo fuentes públicas y parámetros sintéticos; sin acceso al PC local ni a documentación privada de Quside.

Empieza por [el memo de decisiones](00_coordination/DECISION_MEMO.md) y [los resultados de verificación](00_coordination/VALIDATION.md). Se distinguen demostraciones, experimentos, hipótesis comerciales y criterios de certificación.

## Entregables

| Misión | Resultado reutilizable |
|---|---|
| [1. CryptoSure: empresa](01_cryptosure_business/README.md) | Competidores, arquitectura, MVP para tres ingenieros, backlog, escenarios económicos y protocolo de piloto |
| [2. CryptoSure: prototipo](02_cryptosure_prototype/README.md) | CLI, requisitos, trazabilidad, evidencias, hashes, pruebas, informes, replay y procedencia Git |
| [3. Verificación formal](03_formal_verification/README.md) | Lean 4, contador saturado, control de salida, startup, referencia independiente y mutantes rechazados |
| [4. Extractores y entropía](04_extractors_entropy/README.md) | Reuso Toeplitz, AIS, contraejemplos y análisis exacto de matrices fijas sobre fuentes Markov |
| [5. QRNG genérico](05_qrng_model/README.md) | Arcsine + Gauss, feedback, memoria, 24 escenarios con cuatro réplicas, figuras y modelos analíticos |
| [6. JARVIS: arquitectura](06_jarvis_architecture/README.md) | VPS sin PC local, memoria portable, permisos, aprobaciones, presupuesto y kernel offline probado |
| [Resultado transversal: fuga del feedback](00_coordination/feedback_leakage/README.md) | Reconstrucción por conteos de ventanas, minentropía y enumeración exacta |

## Hallazgos que cambian decisiones

- La garantía strong no basta para reutilizar semillas sin independencia respecto del proceso completo, minentropía condicional y presupuesto de error del horizonte.
- Balancear marginales no demuestra entropía conjunta. La telemetría del control puede revelar toda la secuencia; las ventanas solapadas también permiten reconstrucción bajo los supuestos demostrados.
- Una matriz fija puede analizarse sobre una clase de fuentes explícita. Esa prueba no hereda automáticamente la garantía promedio sobre semillas ni equivale a aceptación AIS.
- CryptoSure debe competir en mantenimiento de evidencia revisable: ya existen automatización oficial y productos comerciales.
- Proponer, autorizar y ejecutar acciones necesitan fronteras separadas. El kernel JARVIS implementa admisión y contabilidad; no es un sistema desplegado ni un sandbox.

## Reproducción

Python 3.12 fue la versión usada. Los núcleos analíticos y tests de las misiones 00, 01, 02, 04 y 06 usan biblioteca estándar; las figuras de la misión 04 usan Matplotlib. La misión 05 requiere NumPy, SciPy y Matplotlib; versiones en [run_metadata.json](05_qrng_model/results/run_metadata.json).

```bash
# Desde este directorio:
python3 verify_all.py
python3 verify_all.py --lean /ruta/a/lean-4.19.0-linux/bin/lean --require-lean
```

Si Lean no está disponible, el primer comando lo declara SKIPPED; no lo cuenta como aprobado. El [toolchain](03_formal_verification/lean-toolchain) está fijado. El verificador comprueba copias temporales y conserva hashes de los fuentes ejecutados. Las instrucciones de simulaciones y demos están en cada misión.

## Procedencia

- [Versiones normativas y discrepancias](00_coordination/BASELINE_NORMATIVA.md).
- [Caso de aseguramiento](00_coordination/ASSURANCE_CASE.md).
- [Revisiones](00_coordination/REVIEW_LOG.md).
- [Entorno y límites](00_coordination/ENVIRONMENT.md).
- [Alcance y materiales de terceros](NOTICE.md).

El paquete publicable excluye documentos íntegros de terceros, cachés, toolchains, SQLite de demos y trazas binarias regenerables. Conserva código, resultados tabulares, figuras, fuentes y hashes. No se han enviado artículos, contactado clientes, ejecutado operaciones financieras ni desplegado servicios. Ningún resultado constituye certificación o acreditación de entropía física.
