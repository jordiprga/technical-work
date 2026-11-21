# Informe de revisión científica

Revisión interna de la nota publicada el 20 de noviembre de 2026, realizada el 21 de noviembre de 2026. Se leyeron el PDF renderizado, el manuscrito y las reducciones enlazadas. Este informe registra las objeciones y sus cambios en el manuscrito.

| Objeción | Modificación aplicada |
|---|---|
| El título podía leerse como una clasificación otorgada al producto. El resumen anunciaba una conservación «para la vista especificada» sin precisar la condición que determina su validez. | El título identifica diseños candidatos. El resumen enuncia longitud fija, estado inicial y vista común, permite correlación entre entradas y adelanta el límite ante compromiso en CTR. |
| La primera tabla atribuía «la cardinalidad de 2²⁴⁶ clases» al perfil CTR. El resultado real es una cota inferior probabilística sobre una familia ideal. | Se incorporaron el cuantificador «al menos», la probabilidad de fallo inferior a 2⁻¹⁴⁸ y la distinción con justificar la fuerza del AES concreto. El §998 se cita como conclusión que el BSI atribuye al ejemplo AES/SHA. |
| La API puede descartar peticiones o variar su longitud. Una afirmación de error promedio para todos los intentos no fija por sí sola el error de las respuestas entregadas. | Se incorporaron indicador de éxito y longitud en la vista. Para longitud fija se deriva la cota ε/Pr[éxito] desde la distancia conjunta y se aporta un contraejemplo de selección con un bit. Esta precisión vale para ambos puertos. |
| El tratamiento NIST repetía XOR y RS en tres lugares y dejaba ambiguo qué «nueva clave» se concedía al observador. | Se centralizó la comparación por puerto y se precisó que la cota 2ε se refiere a la clave resembrada que genera la salida. El estado persistente tras el Update define otra vista. |
| La formulación de pruebas de fallo en presente podía dar a entender que se había ensayado un dispositivo físico. Los conteos de teoremas escritos a mano podían quedar desactualizados. | Los ensayos de fallo se describen como evidencia exigible al producto. Los resultados formales remiten al recibo reproducible con el alcance y los hashes. |
| Una lectura del máximo general PTG.3.5 sugería un objetivo normativo mayor para el caso 1:1 con PTG.2. | Se coordinó con la revisión AIS la segunda selección de §375 y el límite especial del §398. El objetivo matemático adicional y la evaluación de NIST se identifican explícitamente. |
| La comparación del referente Hash_DRBG y las tasas de bits y entropía eran difíciles de localizar desde el resumen. | La guía de lectura enlaza ambas secciones, junto a las matrices normativas y las derivaciones de cada puerto. |

## Límites de esta revisión

La revisión científica evalúa el alcance de las afirmaciones y su trazabilidad. La entropía condicionada de la fuente, el coste del selector real y las hipótesis de dureza de las primitivas requieren la evidencia de la instancia. La verificación del código y la confrontación normativa se documentan en sus revisiones especializadas.
