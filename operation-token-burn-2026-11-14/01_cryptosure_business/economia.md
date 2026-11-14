# Economía y escenarios de valoración

Todas las cifras de precios, costes, ventas, retención y múltiplos de este documento son **supuestos sintéticos**. No proceden de entrevistas, presupuestos ni transacciones comparables. Sirven para descubrir condiciones necesarias y contradicciones, no para estimar el valor actual de una empresa inexistente.

## Coste que el cliente podría evitar

Una tarifa regulatoria no es un coste que CryptoSure elimine. NIST publica para 2026 una tasa base de Full Submission FIPS 140-3 nivel 1 de 16.000 USD y de ESV completo de 5.500 USD; existen otros escenarios y posibles tasas adicionales. No incluyen automáticamente honorarios del laboratorio ni ingeniería del fabricante. [S19]

El ahorro defendible se calcula sobre tareas: `horas evitadas × coste cargado por hora`, más retrabajo evitado medido, menos incorporación y mantenimiento. No convertir todo el tiempo de espera de certificación en ingresos recuperados. Para atribuir valor a adelantar una venta se necesita una probabilidad causal, margen de contribución y una relación creíble entre esa demora y la venta.

Ejemplos sintéticos:

| Caso | Horas anuales evitadas | Coste/h | Ahorro directo | Precio máximo con ahorro/precio ≥3 |
|---|---:|---:|---:|---:|
| Fabricante, 4 programas ×100 h | 400 | 100 € | 40.000 € | 13.333 € |
| Laboratorio, 20 proyectos ×40 h | 800 | 110 € | 88.000 € | 29.333 € |
| Fabricante con muchas variantes, 12×120 h | 1.440 | 100 € | 144.000 € | 48.000 € |

Un precio de 30.000 €/año exige al menos 90.000 € de ahorro directo para ese umbral; a 100 €/h son 900 horas. Esta cuenta cuestiona una SaaS cara para un cliente de una sola evaluación. El modelo puede funcionar mejor con múltiples variantes, varias líneas de producto o un laboratorio. Coste de horas liberadas no equivale siempre a ahorro de caja: si no cambian dotación ni producción, puede ser capacidad adicional y hay que demostrar su uso.

## Coste propio inicial

Hipótesis: tres ingenieros a 90.000 €/año de coste total, 60.000 € de dirección/ventas y 30.000 € de estructura, para 360.000 €/año fijos. No es una estimación salarial de mercado. Si Jordi cubre uno de esos roles se asigna su tiempo una sola vez; no se asume trabajo gratuito. Cloud, soporte variable y terceros directos se incluyen en el margen bruto de suscripción y no se vuelven a restar como coste fijo.

Con ACV de 30.000 €, margen bruto del 80% y coste fijo de 360.000 €, se requieren 15 cuentas para cubrir costes fijos antes de reposición de bajas y crecimiento. Con retención anual del 90% y coste incremental de reposición de 6.000 €, la contribución neta es `24.000 − 0,10×6.000 = 23.400 €`, por lo que hacen falta 16 cuentas. Por separado, un CAC completo de 12.000 € produce payback simple de seis meses: `12×12.000/24.000`. El CAC completo incluye costes de venta asignados; no se vuelve a restar de caja además de los costes fijos que ya los contienen.

No confundir margen bruto con beneficio operativo. El coste de incorporación y consultoría puede destruir margen aunque la infraestructura cueste poco. Medir por separado ingresos recurrentes, servicios, coste de soporte por cuenta, desarrollo no reutilizable y tiempo del fundador.

La aproximación `LTV = contribución anual / churn anual` no es una valoración financiera: presupone churn constante, clientes homogéneos, ausencia de descuento, sin expansión y horizonte infinito. Con churn cero el script devuelve ausencia de valor finito en vez de simular certeza infinita. Para decisiones reales se usarán cohortes y flujos descontados con escenarios.

## Qué significan 1 M€, 10 M€ y 100 M€

La fórmula ilustrativa es `valor de empresa (EV) = ARR × múltiplo supuesto`. El valor de las acciones requiere ajustar deuda, caja y otros elementos; una ronda pre-money/post-money tampoco es idéntica a EV. Los múltiplos aquí elegidos no son comparables observados ni una promesa de financiación.

| EV objetivo | Múltiplo supuesto | ARR requerido | ACV supuesto | Cuentas mínimas | Condición empresarial adicional |
|---|---:|---:|---:|---:|---|
| 1 M€ | 4× | 250.000 € | 25.000 € | 10 | Producto repetible y clientes que renuevan; puede seguir perdiendo dinero |
| 10 M€ | 5× | 2.000.000 € | 40.000 € | 50 | Canal de adquisición replicable, bajo servicio singular, menor dependencia del fundador |
| 100 M€ | 8× | 12.500.000 € | 75.000 € | 167 | Expansión internacional y multicomponente, equipo de distribución y mercado suficiente |

Si el mercado sólo valora a 3× ARR, 100 M€ requieren 33,3 M€ de ARR; a ACV de 75.000 €, son 445 cuentas. Si el ACV real es 25.000 € y el múltiplo 5×, hacen falta 800 cuentas. Que una fórmula produzca un número no demuestra que ese número de compradores exista.

La sensibilidad completa en `results/valuation_sensitivity.csv` cruza EV de 1/10/100 M€, múltiplos 3/5/8/12 y ACV 25/50/75 k€. Los extremos altos de múltiplo se incluyen como prueba de sensibilidad, no como hipótesis base.

## Mercado: qué se puede afirmar hoy

No se ha medido TAM, SAM ni SOM. El número de certificados no es el número de clientes: un fabricante puede tener muchos certificados, un grupo varios laboratorios, un certificado abarcar varias versiones y una compra requerir otro centro presupuestario. Tampoco los productos históricos implican presupuesto actual.

Construir mercado de abajo arriba: partir de listas oficiales, normalizar entidades/grupos, clasificar actividad reciente, identificar equipos y contar programas repetidos. Después medir frecuencia de compra, ACV y probabilidad de adopción en entrevistas. Hacer dos universos separados —fabricantes y laboratorios— y deduplicar el gasto que uno trasladaría al otro. No sumar todo el gasto de certificación como mercado de software.

Como comprobación aritmética, un segmento de 100 compradores a 25.000 €/año sólo ofrece 2,5 M€ de ingreso anual al 100% de penetración. Para una empresa que aspire a 12,5 M€ ARR hace falta un universo más amplio, mayor ACV o producto adyacente validado. Este ejemplo no afirma que existan exactamente 100 compradores.

## Simulación de caja a 36 meses

`model.py` modela cuentas nuevas por mes, bajas esperadas, facturación recurrente mensual, incorporación y costes. Arranca con 500.000 € de caja hipotética; no ejecuta una financiación. La retención mensual es `retención_anual^(1/12)`. Las cuentas fraccionarias son una expectativa de cohorte, no contratos parciales reales.

| Parámetro | Conservador | Base | Expansión |
|---|---:|---:|---:|
| ACV | 24.000 € | 30.000 € | 42.000 € |
| Margen bruto suscripción | 70% | 80% | 85% |
| Retención anual de cuentas | 85% | 90% | 95% |
| Ventas mensuales al final | 2 | 3 | 6 |
| Coste fijo mensual inicial | 30.000 € | 30.000 € | 30.000 € |
| Coste fijo mensual final | 30.000 € | 60.000 € | 80.000 € |

Cada alta tiene 6.000 € de coste incremental de adquisición y 5.000 € de ingreso de incorporación con 4.000 € de coste directo. Ese CAC incremental excluye dirección/ventas fija ya incluida en costes fijos; no es comparable directamente con el CAC completo de la tabla de unit economics. El script no duplica ambos.

Resultados redondeados de la ejecución conservada:

| Escenario | ARR mes 12 | ARR mes 24 | ARR mes 36 | Caja mínima | Caja negativa por primera vez |
|---|---:|---:|---:|---:|---|
| Conservador | 139 k€ | 386 k€ | 863 k€ | −142 k€ | Mes 19 |
| Base | 350 k€ | 1.177 k€ | 2.089 k€ | 146 k€ | No en el horizonte |
| Expansión | 621 k€ | 2.559 k€ | 5.385 k€ | 242 k€ | No en el horizonte |

El escenario conservador necesitaría al menos 142 k€ adicionales para evitar saldo negativo dentro de esta simulación, sin colchón de seguridad. Base y expansión dependen de ritmos comerciales no validados. La expansión no es «lo esperable»: exige cerrar 6 cuentas nuevas al mes, retener el 95% anual y mantener margen alto. Es una condición exigente que debe contrastarse con capacidad comercial y de soporte.

Los saltos de coste fijo son niveles, no incrementos: base pasa a 45 k€/mes en mes 19 y 60 k€ en mes 31; expansión a 50 k€ en mes 13 y 80 k€ en mes 25. El primer mes con flujo positivo puede ir seguido de otro negativo al contratar: `summary.json` registra también desde qué mes todos los restantes del horizonte son no negativos.

## Stress del calendario y los costes

`python3 stress.py` conserva ocho sensibilidades deterministas en `results/stress.csv`. No asigna probabilidades a los escenarios. Cuando se retrasan ventas, la agenda de contratación permanece en fechas de calendario originales para hacer visible la tensión entre gasto comprometido y cobro.

| Cambio sobre escenario base | Caja inicial mínima dentro de 36 meses, sin colchón |
|---|---:|
| Sin cambio | 354 k€ |
| Ventas retrasadas 3 meses | 489 k€ |
| Ventas retrasadas 6 meses | 624 k€ |
| ACV 30% menor | 526 k€ |
| Margen bruto 60% | 489 k€ |
| Adquisición incremental al doble | 564 k€ |
| Costes fijos 25% mayores | 524 k€ |
| Retraso 6 meses + ACV −20% + margen 70% + adquisición 9 k€ + fijo +25% | 1.378 k€ |

Un trimestre de retraso reduce la holgura base casi por completo: con 500 k€ iniciales queda un mínimo aproximado de 11 k€. En el combinado adverso el flujo del mes 36 todavía es negativo; 1,378 M€ sólo cubre el horizonte, no garantiza supervivencia posterior. La respuesta gerencial a explorar sería condicionar contrataciones a hitos de ventas y reutilización, no suponer capital ilimitado.

## Límites y uso correcto

No se modelan IVA, impuesto de sociedades, cobros demorados, impagos, financiación, dilución, descuento, variaciones de precio, concentración de clientes, pipeline probabilístico, capacidad máxima del equipo ni pérdida correlacionada por cambio regulatorio. Las ventas se fijan exógenamente: la simulación muestra consecuencias, no explica cómo conseguirlas. No añadir decimales al discurso comercial por el hecho de que Python calcule muchos.

La siguiente iteración debería sustituir supuestos por observaciones de pilotos y usar un modelo de capacidad: horas de incorporación, tickets de soporte, horas de contenido normativo y ventas por persona. Hasta entonces, la decisión defendible es financiar una prueba acotada de disposición a pagar, no optimizar una valoración de 100 M€.

[S19]: https://csrc.nist.gov/projects/cryptographic-module-validation-program/nist-cost-recovery-fees
