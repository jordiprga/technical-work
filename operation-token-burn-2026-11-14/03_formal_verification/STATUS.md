# Estado de misión 3 — entregable operativo

- Lean 4.19.0 oficial aislado en `/tmp/cryptosure-lean`; hashes registrados en TOOLCHAIN.md.
- **47 teoremas comprobados por kernel**, seis módulos, sin sorry/axiomas propios/evaluación nativa como prueba.
- **5 mutaciones erróneas rechazadas**, incluidas implementación siempre-deniega y contador que ignora cambios de símbolo.
- RCT/gate: composición, detección, latch exacto, ausencia de alarmas espurias y bloqueo de la muestra que falla.
- Contador finito: refinamiento `Fin(C+1)`, guarda y cota de palabra.
- Referencia independiente: equivalencia con historial de rachas.
- Startup: descarte durante N muestras y progreso condicionado a salud.
- Feedback: reconstrucción por ventanas e inyectividad, versión finita incluida.
- Revisión independiente de feedback: 36 escenarios, 7.938 palabras, 4.086 transcripts, caso no uniforme 7/8.
- Revisión JARVIS: discrepancia temporal de start/replay reproducida; corrección validada con hashes del código.
- Calibración RCT: DP racional exacta y seis tests PASS; riesgo por ventana diferenciado del acumulado.
- Runner endurecido tras revisión cruzada: captura única de bytes, recibo por ejecución y estados fail-closed; tres regresiones PASS, incluida carrera artificial entre lectura y hash.
- Fuentes primarias, investigación, trazabilidad de 14 filas y revisiones cruzadas guardadas.
- Alcance: propiedades del modelo y derivaciones públicas; no certificación, estimación de entropía física ni refinamiento a código de producto.
- Pendiente fuera de esta ventana: APT, reset/on-demand completos, vínculo C/Rust/RTL, checker independiente.
