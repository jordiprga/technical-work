# Dimensionamiento desde registros públicos: muestra, no TAM

Consulta: 14 noviembre 2026. Se ha construido una muestra manual auditable para comprobar cómo se relacionan certificados, fabricantes y posibles cuentas. El propósito es corregir errores de dimensionamiento, no estimar ingresos a partir de un directorio.

## ESV: resultados observados

La [búsqueda oficial NIST, página 1](https://csrc.nist.gov/projects/cryptographic-module-validation-program/entropy-validations/search?ipp=250&page=1) mostraba 363 registros coincidentes. Se transcribieron IDs E1–E31 y, de la [página 2](https://csrc.nist.gov/projects/cryptographic-module-validation-program/entropy-validations/search?ipp=250&page=2), E338–E368. Son dos ventanas elegidas, no una muestra aleatoria; la primera cubre agosto 2022–marzo 2023 y la segunda julio–octubre 2026.

| Ventana | Registros | Etiquetas de fabricante normalizadas | Etiquetas con varios registros |
|---|---:|---:|---:|
| E1–E31 | 31 | 21 | 4 |
| E338–E368 | 31 | 23 | 7 |
| Unión | 62 | 41 | 12 |

En la primera ventana SUSE aparece siete veces; en la reciente Samsung tres. Esto basta para refutar el supuesto «un certificado = un comprador». No permite estimar el número total de fabricantes mediante una proporción, porque selección temporal, tamaños de empresa y recurrencia no son aleatorios.

Los datos están en [esv_manual_sample.csv](results/esv_manual_sample.csv), el recuento en [market_sample_summary.json](results/market_sample_summary.json) y el procedimiento en [market_sample.py](market_sample.py). Ejecutar `python3 market_sample.py` regenera ambos. No se descargaron PUDs ni se recopilaron contactos personales.

## Normalización y límites

La normalización abrevia razones sociales y unifica puntuación de la misma marca observada. No consolida grupos corporativos ni unidades de producto. Por ejemplo, `HPE` y `HPE Juniper` se conservan separados; `IBM` y `Red Hat` también. La lista necesita un campo independiente para entidad legal, grupo, centro de compra y equipo técnico, con fuente y fecha para cada relación.

Las fechas son las de validación mostradas, no fechas de compra, de inicio del proyecto o de renovación de licencia. Los IDs presentan huecos fuera de la muestra; no se interpreta el ID máximo como número de certificados activos. El total mostrado tampoco es una lista de leads disponibles ni certificaciones nuevas en un año.

## Laboratorios: una muestra útil de concentración

En el [directorio CC oficial](https://www.commoncriteriaportal.org/labs/index.cfm), las secciones Canadá y España muestran nueve entradas: EWA–Canada, Lightship, Applus Laboratories, INTA, Clover, DEKRA, jtsec, Layakk y SGS Brightsight Barcelona. No son nueve acreditaciones NVLAP: pertenecen a este directorio CC y cada alcance debe verificarse por separado.

Las fuentes corporativas de [Lightship](https://www.appluslaboratories.com/global/en/about-us/inbrief/applus-lightship-security) y [jtsec](https://www.applus.com/global/en/about-us/our-brands/jtsec) permiten agruparlas con Applus. Así, sólo con esa consolidación, nueve entradas pasan a siete grupos/etiquetas restantes, sin concluir que tengan siete presupuestos independientes. Un mismo grupo puede comprar por filial o centralizar. A la inversa, un laboratorio puede estar listado bajo más de un esquema sin ser otra instalación.

El [sitio NIST de laboratorios](https://csrc.nist.gov/projects/testing-laboratories) remite al buscador NVLAP y al filtro de programa de ensayos criptográficos. La herramienta web disponible mostró el formulario, no una lista filtrada completa; no se afirma haber censado laboratorios CST. Una descarga directa por Python encontró restricción de red del sandbox; la investigación continuó por búsqueda pública, sin eludir la restricción.

## Cómo convertir esto en un mercado comercial

Crear cuatro niveles separados:

1. **Registro de actividad:** certificado o acreditación pública, fecha, alcance y fuente.
2. **Entidad:** fabricante/laboratorio, filial y grupo, sin suponer independencia de compra.
3. **Programa repetido:** versiones/configuraciones/estándares que requieren trabajo recurrente.
4. **Oportunidad cualificada:** comprador, presupuesto, problema, alternativa y plazo confirmados en una futura conversación autorizada.

Hoy sólo hay evidencia de los dos primeros niveles de forma parcial. Multiplicar 363 registros por 30 k€ produciría 10,89 M€, pero sería una cifra sin interpretación comercial válida. Se conserva aquí como ejemplo de cálculo que **no debe usarse** como TAM.

Para una estimación defendible: completar universo, deduplicar, segmentar frecuencia y seleccionar entrevistas por contraste. Incluir un fabricante grande con herramientas propias, uno pequeño con evaluación ocasional, uno con muchas variantes, un laboratorio con plataforma propia y otro que externalice desarrollo. No entrevistar únicamente amigos entusiastas ni fabricantes de QRNG que comparten la misma situación.

## Servicio frente a producto

El directorio sugiere un ecosistema especializado donde unas pocas relaciones pueden importar, pero no demuestra el mejor modelo comercial. Hay tres pruebas prácticas:

| Observación futura | Interpretación | Decisión |
|---|---|---|
| Cada proyecto paga por análisis experto singular | Mercado de servicios especializado | Cobrar consultoría y usar software interno; no afirmar ARR por repetir facturas |
| El mismo cliente reutiliza conectores y revisa cambios cada trimestre | Posible producto recurrente | Licencia por programa y coste marginal medido |
| Muchos clientes compran sólo a través de pocos labs | Canal concentrado | Edición de revisión y acuerdos futuros, con riesgo de dependencia explícito |

Un negocio de servicios rentable puede financiar investigación sin llegar a una valoración de 100 M€. Una plataforma escalable necesita evidencia de repetición y distribución, no sólo una lista extensa de logotipos.
