# QRNG fotónico genérico con comparador y control de umbral

Simulador reproducible de `Xₜ = A cos(Φₜ) + Cₜ`, con fase uniforme IID **o** difusión circular, ruido gaussiano clásico blanco **o** AR(1), deriva opcional, comparador y realimentación por ventanas. Todos los parámetros y datos son sintéticos. Ningún resultado representa un producto de Quside ni acredita una fuente física.

La conclusión operativa es concreta: equilibrar ceros y unos puede introducir memoria y ocultar pérdida de predictibilidad. Una ventana más larga reduce ruido de estimación, pero un mayor solapamiento añade retardo y puede desestabilizar un controlador que parecía seguro al usar ventanas independientes.

## Entregables

- [Modelo, demostraciones y supuestos](MODEL_AND_PROOFS.md).
- [Resultados y recomendaciones condicionadas](RESULTS_AND_RECOMMENDATIONS.md).
- [Fuentes primarias y alcance](SOURCES.md).
- [Coexistencia de ciclos no lineales](nonlinear_bifurcation.py), [figura](figures/nonlinear_bifurcation.png).
- [Tasa de entropía en un modelo finito](finite_state_analysis.py), [resumen](results/finite_state_summary.csv).
- [Simulador y CLI](qrng_sim.py), [barrido reproducible](run_experiments.py), [tests](test_qrng_sim.py).
- [Resultados completos CSV](results/experiments.csv), [resumen de cuatro réplicas](results/summary.csv), [contraejemplo exacto](results/exact_feedback.json).
- [Comparación marginal/condicional](figures/marginal_vs_conditional.png), [teoría de feedback](figures/feedback_theory.png), [estabilidad con ventanas solapadas](figures/overlap_stability.png), [seguimiento de deriva](figures/drift_tracking.png). Cada figura también está disponible como SVG.

## Ejecución

```bash
cd /workspace/operation-token-burn/05_qrng_model
python3 -m unittest -v test_qrng_sim.py
python3 run_experiments.py
python3 finite_state_analysis.py
python3 nonlinear_bifurcation.py
python3 numerical_validation.py
python3 qrng_sim.py --out results/single
# Configuración explícita: JSON con campos de Config.
python3 qrng_sim.py --config example_config.json --out results/custom
```

Se requieren Python 3.10+, NumPy, SciPy y Matplotlib. Las dependencias exactas están en [requirements.txt](requirements.txt). Las versiones efectivamente usadas quedan en [run_metadata.json](results/run_metadata.json). No se descarga información ni se conecta a ningún sistema durante las simulaciones. El generador NumPy se usa sólo para simulación, nunca para generar secretos.

El barrido ejecuta 24 escenarios × 4 semillas × 524 288 muestras; descarta 16 384 muestras iniciales para diagnósticos. Este descarte es una elección experimental, no una prueba de mezcla o estacionariedad. Conserva configuraciones, métricas y series de control; las secuencias completas se regeneran con las semillas. La CLI individual conserva una traza NPZ.

## Qué no se ha demostrado

No se ha demostrado entropía cuántica de ningún dispositivo, seguridad frente a memoria cuántica arbitraria, estacionariedad física, independencia de ruido real ni cumplimiento de NIST/BSI. Las métricas de entropía causal de un paso excluyen el transcript futuro y no constituyen una tasa de min-entropía de bloques. Si se divulgan los umbrales posteriores, pueden revelar cuentas de ventanas e incluso todos los bits para W=U=1. Las estimaciones empíricas no llevan intervalos de confianza certificados. Las fórmulas lineales se marcan inaplicables cuando los supuestos del experimento no corresponden.
