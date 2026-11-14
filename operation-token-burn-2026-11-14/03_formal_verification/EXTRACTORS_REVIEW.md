# Revisión cruzada de extractores y composición

Revisión por la misión formal, 14-11-2026. Archivos revisados: `04_extractors_entropy/theory.md`, especialmente §§4 y 7, y `fixed_matrix_methods.md`. No se modificaron archivos de esa misión.

**Resultado:** no se encontró error matemático en los enunciados revisados bajo sus hipótesis explícitas. Esta es una revisión matemática, no una mecanización Lean del LHL ni una validación de parámetros físicos.

## Reutilización de semilla

La prueba por híbridos es válida: `H_i=(S,E,Y_≤i,U_>i)` conserva el prefijo real y sustituye un bloque cada vez. Aplicar el extractor con información lateral `(X_<i,E)` y después transformar ese pasado bruto en salidas pasadas mediante el mismo S es procesamiento de datos. Así se evita el paso inválido de asumir independencia fuente-semilla condicionada en `Y_<i`.

Es esencial que S sea independiente del proceso **completo** `(X₁,…,X_t,E)`, y que la min-entropía condicional se acote bloque a bloque dado el pasado bruto. Entropías marginales, independencia sólo inicial de un sistema adaptativo o ausencia de autocorrelación no bastan. El texto mantiene correctamente estas distinciones.

Usar proyecciones uniformes de una semilla común también es compatible con la prueba: para cada llamada, la parte restante de S puede adjuntarse mediante el canal que muestrea S condicionado en su proyección. La independencia global respecto de fuente e información lateral es lo que justifica ese canal sin alterar la distribución relevante.

El presupuesto por suma de errores es suficiente y conservador. No se presenta como necesario ni óptimo. Un horizonte fijo puede incluir una regla de parada por procesamiento de datos; condicionar después en un evento raro necesita analizar su probabilidad, como ya indica el texto.

## Información lateral cuántica y suavizado

La extensión de composición a un estado cq conserva un registro clásico del pasado bruto y aplica canales que producen el pasado de salidas. La contracción de distancia de traza mantiene el argumento. Las hipótesis globales y los costes de cada llamada siguen siendo necesarios.

La convención declarada de marginal lateral real y cota `2η + ½ sqrt(2^(m−Hmin^η))` es conservadora y coherente con el argumento triangular: la aproximación suavizada afecta tanto al estado real como al marginal ideal de comparación. Es correcto advertir que una definición optimizada sobre el estado lateral puede mostrar otra constante. Deben conservarse conjuntamente métrica, normalización/subnormalización y definición de Hmin suave; copiar una fórmula aislada de otro artículo sería insuficiente.

No se ha implementado una prueba de matrices de densidad ni un tratamiento cuántico del controlador físico. El respaldo de la parte quantum-proof sigue siendo el resultado primario citado por la misión de extractores.

## Matriz fija y modelos restringidos

La identidad `φ_Y(v)=φ_X(Tᵗv)` y su inversión de Walsh son correctas para una matriz fija. La transferencia Markov representa la esperanza de un producto de signos mediante dos pesos de estado; no necesita enumerar todas las palabras de entrada. La complejidad continúa exponencial en el ancho de salida m y los racionales pueden crecer, límites correctamente señalados.

Para bits independientes con sesgos acotados, la cota de coeficientes Fourier por producto de sesgos y la cota TV mediante Parseval/Cauchy–Schwarz son válidas. El enumerador de pesos de las filas combinadas de T permite una garantía para esa matriz y esa clase de fuentes, sin convertirla en un extractor determinista para todas las fuentes de min-entropía k.

La restricción Markov o independencia condicionada es parte del modelo de amenaza. Evaluar exactamente un modelo restringido no demuestra que una fuente física pertenezca a él, y evaluar una malla de parámetros no certifica el peor caso de un intervalo continuo. El documento lo expresa de forma adecuada.
