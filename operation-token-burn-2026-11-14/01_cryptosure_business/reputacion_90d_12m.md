# Reputación internacional: tres activos técnicos y un plan verificable

Punto de partida: 14 noviembre 2026. El objetivo es que otros especialistas puedan reutilizar, refutar o ampliar trabajo de Jordi. No medir autoridad por cantidad de publicaciones ni por alcance de marketing. Ninguna publicación, inscripción o comunicación se ha realizado en esta operación.

## Oportunidad próxima que requiere decisión humana

La [convocatoria oficial ICMC 2027](https://icmconference.org/speaking/) anuncia ampliación del plazo de propuestas hasta el **16 de noviembre de 2026**. El evento está previsto para 12–15 abril 2027 en Toronto. La convocatoria pide contenido neutral respecto a proveedores y permite proponer una charla con título y resumen. Se conserva un borrador en [icmc_abstract_draft.md](icmc_abstract_draft.md), sin enviarlo y sin reservar asistencia.

Antes de considerar envío: Jordi debe revisar personalmente las afirmaciones, decidir autoría/afiliación, comprobar el plazo y valorar si puede mantener la promesa técnica. La urgencia de dos días no convierte un borrador producido por agentes en trabajo listo para presentarse.

## Activo A: guía rigurosa sobre feedback e información lateral

Base disponible: [modelo QRNG](../05_qrng_model/README.md) y [demostración de fuga por feedback](../00_coordination/feedback_leakage/README.md). Tema propuesto: cuándo un controlador mejora balance marginal mientras introduce dependencia o revela información sobre bloques anteriores. Separar distribución observable, información del adversario y objetivo de entropía.

Entregable publicable futuro: nota técnica con modelo explícito, resultado analítico, casos exactos pequeños, simulación reproducible y condiciones bajo las que no se aplica. Debe distinguir un sistema sintético de cualquier dispositivo real. No atribuir parámetros, diseños, resultados o prácticas a Quside.

Criterio de revisión: un especialista reproduce las curvas desde un entorno limpio; otro intenta romper los supuestos de información lateral; todas las afirmaciones sobre min-entropía especifican variante y condicionamiento. Si sólo hay simulación, titular como estudio de modelo; si hay teorema, indicar exactamente qué garantiza.

## Activo B: catálogo de afirmaciones correctas e incorrectas sobre extracción

Base disponible: [misión de extractores](../04_extractors_entropy/README.md) y [verificación formal](../03_formal_verification/README.md). Tema: semilla pública reutilizada, independencia, correlación entre bloques, garantías strong y composición. El valor es convertir preguntas recurrentes en teoremas con hipótesis y contraejemplos pequeños.

Entregable futuro: un tutorial técnico con ejemplos ejecutables y una tabla «afirmación → hipótesis necesarias → prueba/contraejemplo → implicación para evaluación». La novedad científica no se presume: algunos resultados son clásicos. Una buena sistematización puede ser valiosa aunque no invente un nuevo extractor.

Criterio de revisión: identificar literatura previa exacta, comprobar notación de min-entropía, revisar side information clásica/cuántica, ejecutar Lean con versión fijada si se afirma verificación mecanizada y mostrar cualquier axioma adicional. No presentar un cálculo exhaustivo de dimensiones pequeñas como prueba general.

## Activo C: formato portable y benchmark de evidencia

Base disponible: [prototipo CryptoSure](../02_cryptosure_prototype/README.md). Tema: cómo separar integridad, reproducción, suficiencia y decisión de certificación, y cómo invalidar apoyo cuando cambian producto o requisitos.

Entregable futuro: especificación mínima de paquete, verificador independiente, corpus sintético de fallos y protocolo de evaluación. Debe incluir casos que el producto no puede resolver, como documento físicamente falso o modelo de fuente no justificado. Un verificador abierto y un export legible crean confianza antes que una demo vistosa.

Criterio de revisión: un equipo ajeno importa el paquete sin instalar una SaaS; detecta modificaciones sembradas; reproduce checks; distingue «integridad verificada» de autenticidad; y comunica las limitaciones sin explicación del autor. Sólo después medir ahorro de tiempo con el protocolo de piloto.

## Plan de 90 días

| Periodo | Resultado controlable | Evidencia de terminado |
|---|---|---|
| Días 1–7 | Elegir un activo principal y revisar el borrador ICMC | Lista de claims, fuentes y objeciones; decisión de enviar o no tomada por Jordi |
| Semanas 2–3 | Congelar v0.1 reproducible del activo A o B | Comando único, entorno fijado, datos sintéticos y checksum |
| Semanas 4–5 | Obtener revisión técnica autorizada y corregir | Matriz de comentarios/resoluciones, sin ocultar resultados negativos |
| Semanas 6–8 | Escribir manuscrito o tutorial completo | Bibliografía primaria, alcance explícito y figuras regeneradas |
| Semanas 9–10 | Reproducción por otra persona | Registro de fallos de instalación, dudas y resultados coincidentes |
| Semanas 11–13 | Decidir destino y preparar versión revisada | Checklist específico del venue y versión que Jordi entiende y puede defender |

El periodo termina aproximadamente el 12 febrero 2027. Propuesta de dedicación: dos bloques de investigación de 90 minutos y un bloque de revisión de 60 minutos por semana, más una sesión mensual de resultados. Si hay disponibilidad mayor, profundizar en pruebas y experimentos antes de multiplicar temas.

## Ventanas y destinos verificados

| Destino | Ajuste temático | Estado consultado | Precaución |
|---|---|---|---|
| [ICMC 2027](https://icmconference.org/speaking/) | Evidencia práctica, módulos y fuentes de entropía | Propuestas hasta 16 noviembre 2026; evento abril 2027 | Charla neutral y revisable; no convertirla en demo de ventas |
| [CHES/TCHES 2027 CFP](https://ches.iacr.org/2027/callforpapers.php) | RNG, métodos formales, ingeniería criptográfica y SoK | El alcance oficial incluye estos temas | Se necesita contribución científica evaluable, no sólo documentación |
| [CHES 2027, instrucciones](https://ches.iacr.org/2027/papersubmission.php) | Manuscrito con artefacto | Fechas tentativas próximas: 15 enero y 15 abril 2027, AoE | Verificar de nuevo; anonimato, políticas y madurez técnica antes de enviar |
| [ICCC 2027](https://iccconference.org/) | Trazabilidad, continuidad y evaluación CC/EUCC | Evento anunciado 13–16 septiembre 2027, Estocolmo | La web mezcla archivos 2026 con información 2027; no asumir CFP abierto |

La [política IA de CHES 2027](https://ches.iacr.org/2027/aipolicy.php) exige responsabilidad de los autores y divulgación apropiada del uso de IA; el texto contiene matices sobre edición que deben revisarse junto a instrucciones de anonimato. Esta operación debe conservarse como material asistido por IA. Reescribir sin entender o borrar procedencia no satisface responsabilidad científica. El sitio principal de TCHES mostró una denegación de acceso; se consultaron páginas oficiales de CHES, sin intentar sortearla.

## Plan hasta doce meses

Meses 4–6: completar un activo con revisión externa real y preparar una charla técnica si fue aceptada. Un segundo activo puede salir como anexo reproducible del primero. Meses 7–9: conectar resultados con un caso genérico de evaluación y recoger objeciones de especialistas, siempre con autorización para contactar. Meses 10–12: consolidar una biblioteca de ejemplos y un manuscrito más fuerte; decidir si la comunidad usa el formato de evidencia o si debe adaptarse a herramientas existentes.

Métricas controlables: dos reproducciones independientes; diez objeciones técnicas resueltas o aceptadas como limitaciones; un artefacto reutilizado fuera del equipo; un documento citado por razones técnicas; y menor tiempo para responder correctamente a una pregunta difícil. Aceptaciones en conferencias, citas y ventas son resultados externos; no se garantizan.

## Separación entre reputación y venta

Un paper/tutorial debe seguir siendo útil para alguien que jamás comprará CryptoSure. Los resultados negativos y contraejemplos aumentan su valor. La empresa puede beneficiarse de experiencia y herramientas, pero el material público no debe implicar endorsement de NIST/BSI/CCN ni de empleadores. Las relaciones comerciales futuras se distinguen del criterio de evaluación.

El activo más estratégico a corto plazo es C para demostrar producto, mientras A o B puede dar mayor profundidad científica. Intentar maximizar simultáneamente startup, investigación y orquestación personal en cada semana probablemente fragmentaría el esfuerzo: elegir un resultado principal trimestral y conservar el resto como backlog.
