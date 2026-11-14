# Archivos completos de predicciones y auditoría

La traza incluida en el JSON conserva como máximo los primeros 1024 objetivos
de test para una visualización rápida. Esa traza no basta para reconstruir las
métricas de una evaluación más larga. El archivo comprimido `.npz` almacena las
etiquetas, índices y probabilidades de **todo** el test para cada modelo,
incluidos `selected`, `ensemble` y el oráculo cuando existe.

El backend entrega transitoriamente estos datos en `result['_audit']`. Al
guardar el resultado, esa estructura NumPy debe extraerse del JSON y escribirse
con `write_prediction_archive`. El JSON enlaza el archivo mediante el objeto
`prediction_archive` devuelto por esa función. No se convierte el archivo
completo en listas JSON ni se trunca para ajustarlo a la vista interactiva.

## Formato

Un NPZ de versión 1 contiene exactamente las siguientes matrices:

| Campo | Tipo | Forma | Significado |
|:---|:---|:---|:---|
| `format_version` | int64 | escalar | Versión 1 |
| `y` | int64 | `(n_test,)` | Símbolos objetivo codificados como 0,…,A−1 |
| `target_indices` | int64 | `(n_test,)` | Índices originales, crecientes y sin duplicados |
| `model_names` | Unicode NumPy | `(n_models,)` | Orden de los modelos |
| `probabilities` | float64 | `(n_models,n_test,A)` | Masas predictivas completas |

Los índices pueden tener saltos; su orden temporal se conserva. Todas las
matrices probabilísticas tienen el mismo alfabeto. Se comprueba que sean
finitas, no negativas y normalizadas dentro de la tolerancia numérica de la
función de puntuación. Se preservan los valores completos sin reducirlos a
float32 ni renormalizarlos al guardar.

El lector usa siempre `allow_pickle=False`: no se aceptan matrices de objetos
Python. El archivo se escribe primero en un temporal del mismo directorio y
se reemplaza atómicamente al finalizar. Un NPZ no es un checkpoint de PyTorch
ni contiene código ejecutable del modelo.

La metadata del JSON contiene `format`, `format_version`, `filename`, `sha256`,
`models`, `n_test`, `alphabet_size` y `bytes`. `filename` se interpreta respecto
al directorio del JSON cuando se utiliza desde la interfaz de línea de comandos.
El hash SHA-256 cubre todos los bytes del archivo comprimido.

## Verificación independiente

Ejemplo de lectura y recálculo desde Python:

```python
import json
from pathlib import Path
from entropy_oracle.artifacts import load_prediction_archive, verify_prediction_metrics

result_path = Path('results/my_run.json')
result = json.loads(result_path.read_text())
archive_path = result_path.parent / result['prediction_archive']['filename']
report = verify_prediction_metrics(result, archive_path)
assert report['verified'] and report['sha256_verified']
audit = load_prediction_archive(archive_path)
print(audit['y'].shape, list(audit['probabilities']))
```

El verificador compara el hash cuando hay metadata, el número de objetivos,
los nombres de todos los modelos y los extremos temporales declarados. Recalcula
**accuracy, log-loss en bits y Brier** sobre el test completo mediante
`score_predictions(..., bootstrap=0)`, con tolerancia absoluta por defecto
`1e-10` y tolerancia relativa cero. La implementación del log-loss conserva el
suelo numérico declarado de `1e-15`. También contrasta la traza parcial del JSON
con el prefijo correspondiente del archivo.

Una alteración de métricas, un archivo sustituido, probabilidades mal formadas o
una discrepancia de índices produce una excepción explícita. Los resultados sin
metadata de archivo todavía pueden compararse si se proporciona el NPZ
manualmente, pero el informe devuelve `sha256_verified=False`; no existe en ese
caso un vínculo de integridad previo. Los JSON históricos que solo contienen la
traza parcial no permiten regenerar las probabilidades de test omitidas: hay que
volver a ejecutar el experimento para producir un archivo completo.

La consistencia de un hash y de las métricas no demuestra que el entrenamiento
haya ocurrido como se declara, que el split no tenga fuga, o que la fuente sea
auténtica. Tampoco firma el archivo ni identifica a su autor. El verificador no
reanuda entrenamientos ni reestima los intervalos bootstrap: hace auditable la
relación entre predicciones guardadas y métricas informadas. Los datos completos
permiten realizar aparte nuevos contrastes pareados y análisis de calibración.

## Datos externos y publicación

Un archivo de auditoría incluye etiquetas reales del conjunto retenido y las
probabilidades de los modelos. Para fuentes importadas, esos símbolos pueden
ser datos sensibles aunque estén codificados como enteros. El guardado es local;
no implica consentimiento para publicarlos. Los archivos de experimentos con
fuentes externas no deben añadirse ni subirse automáticamente al repositorio.
La publicación de código y resultados sintéticos debe distinguirse de la
publicación de fuentes y predicciones externas. El hash permite enlazar un
archivo conservado localmente sin revelar por sí mismo su contenido completo.
