# Piloto y discovery: comprobar valor antes de ampliar producto

Documento de trabajo; no se ha enviado a clientes ni usado para captar datos. Los importes son propuestas. Cualquier comunicación futura sigue requiriendo autorización de Jordi.

## Pregunta que el piloto debe resolver

¿Puede un equipo preparar, revisar y mantener evidencia con menos esfuerzo y sin perder capacidad para detectar errores? Un resultado rápido que oculta supuestos es peor que un flujo más lento que los hace visibles. La decisión de compra debe apoyarse en ambas dimensiones.

## Oferta de piloto concreta

Duración: cuatro semanas después de disponer del núcleo funcional. Alcance: una familia de producto, dos snapshots y un perfil acotado; hasta tres clases de artefactos y dos herramientas ya soportadas. Precio a contrastar: 10.000 € con exportación completa al cierre. Si el cliente necesita nuevos adaptadores, se cotizan de forma separada y se declaran fuera de la medida de ahorro inicial.

Entregables: inventario inicial, matriz de evidencia, primer paquete reproducible, informe de diferencias entre snapshots, hallazgos pendientes y medición de tareas acordadas. No incluye certificado, submission oficial, dictamen de conformidad ni promesa sobre tiempos de terceros.

El piloto empieza con datos sintéticos o públicos. Si posteriormente se requiere material del cliente, se decide expresamente alcance, custodia, ubicación, acceso y retención antes de recibirlo. El diseño admite ejecución en entorno del cliente sin que la startup copie sus muestras o documentos.

## Diseño de evaluación

Construir 12 casos sintéticos en cuatro familias: ausencia de evidencia, inconsistencia de versión, fallo de integridad y supuesto no justificado. Cada familia tiene caso válido, error visible y error sutil. Este corpus no mide cumplimiento normativo; mide comportamiento del flujo ante anomalías conocidas.

Dos revisores evalúan casos equivalentes con su flujo habitual y con la herramienta. Alternar orden y variantes para reducir aprendizaje. El revisor no conoce de antemano dónde está el fallo, pero sí el alcance y la definición de éxito. Mantener constante el acceso a información y registrar ayuda del fundador: una explicación oral es coste, no magia del producto.

La unidad de análisis es el caso/revisor, no cada click o requisito. Doce casos son evidencia exploratoria, no un ensayo que justifique generalizar un porcentaje a toda certificación. Informar pares, dispersión y diferencias por familia; si se calcula un intervalo por bootstrap, agrupar por caso para no simular independencia inexistente.

| Métrica | Definición | Error que evita |
|---|---|---|
| Tiempo de localización | Inicio de tarea hasta identificar evidencia correcta y snapshot | Confundir abrir un archivo con encontrar el correcto |
| Tiempo de reproducción | Entorno preparado hasta obtener resultado explicable | Ocultar instalación o intervención del autor |
| Detección de anomalías | Fallos sembrados detectados / fallos presentados | Celebrar velocidad con falsos negativos |
| Falsos apoyos | Claims declarados respaldados cuando el caso es insuficiente | Convertir cobertura aparente en seguridad |
| Incorporación | Horas de configuración, perfilado y correcciones | Ignorar el coste inicial |
| Reutilización | Horas que usan adaptadores comunes / horas totales | Confundir consultoría con producto |
| Exportabilidad | Verificación y lectura fuera de la instalación original | Dependencia permanente del proveedor |

Umbrales propuestos: no perder anomalías críticas detectadas por el flujo habitual; ningún falso apoyo crítico; mediana de tiempo reducido ≥30% en tareas definidas; ≥70% de incorporación reutiliza componentes; y ahorro anual conservador ≥3 veces licencia. Si la muestra no permite concluir, registrar incertidumbre y ampliar antes de vender el porcentaje.

## Preguntas de discovery que discriminan hipótesis

1. Describir el último cambio que obligó a revisar evidencia: qué cambió, quién detectó impacto y qué trabajo se repitió.
2. Mostrar un ejemplo anonimizado o sintético de una solicitud adicional del laboratorio. ¿Faltaba contenido, contexto, formato o confianza?
3. ¿Qué parte del flujo actual funciona suficientemente bien como para no sustituirla?
4. ¿Cuántas versiones, entornos y esquemas se mantienen simultáneamente? Separar actividad prevista de realizada.
5. ¿Quién puede autorizar presupuesto y qué partida paga hoy este trabajo?
6. ¿Qué condiciones impedirían usar SaaS? ¿Basta una instalación privada o se exige aislamiento mayor?
7. ¿El laboratorio aceptaría revisar una exportación de terceros? ¿Qué tendría que contener?
8. Si el producto desapareciera mañana, ¿qué querrían poder seguir verificando?
9. ¿Cuánto trabajo singular de integración sería tolerable y quién lo paga?
10. Ante una demo exacta y un precio, ¿comprarían un piloto ahora, con qué condición observable?

No empezar con «¿te gustaría una IA que automatice la certificación?»: invita a una respuesta aspiracional y no descubre coste, frecuencia ni decisión de compra. No ofrecer descuentos antes de entender el desacuerdo sobre valor.

## Ficha por cuenta, sin datos personales

Guardar entidad/grupo, segmento, número de programas confirmado, rol del comprador, alternativa actual, horas medidas, restricciones de despliegue, precio propuesto, respuesta y siguiente decisión. Hasta entrevistar, estos campos quedan como `desconocido`; no inferirlos de un certificado. Separar interés verbal, permiso para piloto, contrato y renovación.

## Criterios de servicio o producto

Si la mayor parte del valor proviene de que Jordi explica el modelo de entropía, vender ese análisis como servicio y usar software para aumentar calidad. Si una persona ajena ejecuta el mismo flujo en otro proyecto con poco soporte, hay evidencia inicial de producto. Registrar horas por tipo de trabajo durante tres pilotos consecutivos evita elegir el modelo por aspiración.

## Preguntas difíciles de comité de inversión

**¿Por qué no lo hace NIST?** Parte ya la hace. La hipótesis es que preparación, cambios y reutilización entre equipos/esquemas siguen requiriendo producto; demostrarlo con flujos reales.

**¿Por qué no lo hace el laboratorio?** Algunos ya lo hacen. La propuesta debe ofrecer interoperabilidad o coste menor a un subconjunto concreto, no afirmar incompetencia de incumbentes.

**¿Qué evita que otro copie el producto?** Poco al principio. La ventaja necesita adopción, confianza, adaptadores y corpus de regresión. El conocimiento del fundador acelera aprendizaje pero no constituye una barrera infinita.

**¿Cuántos clientes hay?** La muestra pública demuestra actividad y repetición, no un TAM. Antes de una ronda orientada a 100 M€, identificar suficientes centros de compra y ACV respaldados.

**¿Y si cada norma cambia?** Mantener perfiles es parte del coste. La separación baseline–reglas–artefactos limita el daño, pero necesita presupuesto y revisión experta.

**¿Puede funcionar sin IA?** El núcleo debería hacerlo. Usar IA sólo donde mejore una tarea medida y sus errores puedan revisarse. Esto reduce dependencia y hace más creíble la evidencia.
