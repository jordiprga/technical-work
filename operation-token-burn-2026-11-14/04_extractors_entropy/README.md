# Extractores, entropía y reutilización de semillas Toeplitz

Fecha de investigación: **14 de noviembre de 2026**. Sólo fuentes públicas y datos sintéticos.

La reutilización de una semilla Toeplitz puede tener una garantía matemática conjunta, pero exige hipótesis explícitas sobre toda la fuente y una contabilidad del error acumulado. La propiedad *strong* por sí sola no justifica bloques correlacionados, fuentes adaptadas a la semilla, una semilla determinista arbitraria ni un horizonte infinito.

La ruta de certificación AIS 20/31 tiene además requisitos propios: el documento oficial de 2024 **no permite justificar una función fija permanente únicamente con el leftover hash lemma**; exige entonces analizarla como postprocesado algorítmico mediante el modelo estocástico. Véanse los párrafos 338 y 342, y la distinción explicada en [AIS y conditioning](ais31_and_conditioning.md).

## Entregables

- [Teoría y demostraciones](theory.md): universalidad Toeplitz, LHL, composición de bloques, semillas imperfectas y contraejemplos.
- [AIS 20/31 y conditioning criptográfico](ais31_and_conditioning.md): requisitos localizados, versiones, fundamentos y decisiones de arquitectura.
- [Análisis exacto de matrices fijas](fixed_matrix_methods.md): Fourier/Walsh y modelos Markov, con garantías para clases de fuentes restringidas.
- [Revisión de seguridad y plan de investigación](security_review.md): afirmaciones aceptables, evidencia necesaria y tareas pendientes.
- [Laboratorio reproducible](extractor_lab.py), [tests](test_extractor_lab.py), [resultados exactos y simulados](results/results.json), [registro de tests](tests.log).
- [Cotas robustas por intervalos y plan de investigación](INTERVAL_MARKOV_RESEARCH_PLAN.md): branch-and-bound racional con certificado reproducible.
- [Revisión previa a publicación](PREPUBLICATION_REVIEW.md).
- [Revisión cruzada](REVIEW_NOTES.md) y límites de validación.
- [Fuentes primarias](sources.json), con URL, versión, alcance y fecha de consulta.
- [Resultados visuales](results/README.md).

## Reproducir

Python 3.10 o posterior; el laboratorio y los tests usan sólo la biblioteca estándar.

```bash
cd /workspace/operation-token-burn/04_extractors_entropy
python3 -m unittest -v
python3 extractor_lab.py --output results/results.json
python3 fixed_matrix_analysis.py
python3 interval_markov.py
python3 plot_results.py
```

El último comando requiere Matplotlib, instalado en el entorno. `random.Random` se usa únicamente para Monte Carlo sintético reproducible; **no** genera aleatoriedad de seguridad.

## Resultados principales comprobados

En una familia Toeplitz de 6 bits de entrada, 2 de salida y 7 de semilla, enumerada por completo:

| Experimento | Distancia a uniforme, incluyendo la semilla pública |
|---|---:|
| Un bloque uniforme | 9/512 = 0.017578125 |
| Dos bloques independientes, misma semilla | 51/2048 = 0.02490234375 |
| Dos copias del mismo bloque, misma semilla | 1545/2048 = 0.75439453125 |
| Fuente adaptada al núcleo de la matriz | 3/4 = 0.75 |

La fuente adaptada conserva al menos 4 bits de minentropía **condicional en la semilla**, pero produce siempre cero. Eso demuestra por qué sustituir la independencia por una cota de `Hmin(X|S)` es incorrecto en el LHL habitual.

Se comprobaron exhaustivamente familias pequeñas y dieciocho tests sustantivos. Las pruebas matemáticas de este directorio son demostraciones escritas, no pruebas mecanizadas en Lean. Los lemas complementarios mecanizados, si están disponibles, pertenecen a [verificación formal](../03_formal_verification/README.md).

## Límites

No se afirma conformidad de un producto, ni seguridad de una fuente física concreta. Las simulaciones ilustran mecanismos y contrastan fórmulas finitas. No verifican minentropía cuántica ni tasas de entropía de dispositivos. La revisión normativa usa la referencia matemática BSI v3.0 de 10-09-2024 y distingue los documentos de esquema AIS 20/31, que tienen numeración propia.
