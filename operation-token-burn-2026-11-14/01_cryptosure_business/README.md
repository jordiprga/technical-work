# CryptoSure: una empresa de infraestructura de evidencia criptográfica

Fecha de corte: 14 de noviembre de 2026. Investigación pública; ningún cliente entrevistado, precio validado o relación comercial asumida.

**Recomendación:** probar un producto que convierta cambios de ingeniería en paquetes de evidencia reproducibles, revisables y portables para fabricantes y laboratorios. La primera oferta debe cubrir preparación y mantenimiento de evidencia de fuentes de entropía y su integración en módulos. No vender «certificación automática».

La automatización básica ya existe: NIST está modernizando CMVP y Lightship comercializa Greenlight para pruebas Common Criteria. El espacio defendible, todavía una hipótesis comercial, es gestionar la procedencia, vigencia y reutilización controlada de evidencias entre versiones, equipos y esquemas. Las necesidades del laboratorio deben definir qué exportaciones tienen valor real.

## Entregables

| Archivo | Uso |
|---|---|
| [propuesta.md](propuesta.md) | Mercado, posicionamiento, clientes, distribución, precios, riesgos y experimentos |
| [arquitectura.md](arquitectura.md) | Modelo de confianza, datos, ejecución, cambios, estándares y CI/CD |
| [backlog.md](backlog.md) | MVP de tres ingenieros con dependencias y criterios de aceptación |
| [economia.md](economia.md) | Supuestos, unit economics y escenarios de 1/10/100 M€ |
| [sources.md](sources.md) | Fuentes primarias y límites de lo que acreditan |
| [mercado_bottom_up.md](mercado_bottom_up.md) | Muestra pública de 62 registros ESV, deduplicación y límites comerciales |
| [piloto_y_discovery.md](piloto_y_discovery.md) | Oferta de piloto, experimento de eficacia y preguntas de validación |
| [reputacion_90d_12m.md](reputacion_90d_12m.md) | Tres activos técnicos, plan de reputación y venues verificados |
| [icmc_abstract_draft.md](icmc_abstract_draft.md) | Propuesta neutral para revisión; ICMC anuncia plazo 16 noviembre 2026 |
| [model.py](model.py) | Modelo económico reproducible sin dependencias externas |
| [stress.py](stress.py) | Sensibilidad de caja a retrasos, precio, margen y costes |
| [tests/test_model.py](tests/test_model.py) | Comprobaciones de fórmulas y límites del modelo |
| [results/](results/) | Tablas generadas y registro de ejecución |

## Decisiones que cambiarían la tesis

1. Si los laboratorios no aceptan una exportación neutral o exigen volver a producir toda evidencia, el producto se limita a preparación interna y su disposición a pagar puede ser menor.
2. Si los fabricantes hacen una certificación aislada y no reutilizan evidencia, la recurrencia SaaS será débil; vender una licencia anual por programa activo, no inventar uso recurrente.
3. Si el ahorro de ingeniería y revisión no supera tres veces el precio, no escalar ventas.
4. Si cada cliente necesita adaptadores totalmente distintos, mantener un negocio de servicios o reducir el segmento antes de financiar una plataforma general.

## Reproducción

Desde este directorio:

```bash
python3 model.py --out results
python3 market_sample.py
python3 stress.py
python3 -m unittest discover -s tests -v
```

El modelo usa escenarios sintéticos explícitos. No realiza operaciones financieras, solicitudes de red ni decisiones de inversión. El prototipo de software de la misión 2 vive en [../02_cryptosure_prototype](../02_cryptosure_prototype/README.md); esta misión define producto y arquitectura objetivo, no afirma que todo esté implementado.
