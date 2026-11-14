# MVP realizable por tres ingenieros

Plan orientativo de doce semanas; no es estimación contractual. Supone experiencia suficiente en Python, seguridad y certificación, acceso autorizado a ejemplos públicos/sintéticos y un evaluador dispuesto a revisar entregables. Si no se consigue esa revisión, no seguir ampliando cobertura nominal.

Roles: A, modelo de evidencia y backend; B, runners y reproducibilidad; C, interfaz de revisión, perfiles y documentación. Jordi aporta criterio de dominio y decisiones de producto; si además ocupa uno de los tres puestos, reducir alcance o reservar explícitamente 30% de su capacidad para investigación/ventas. Los tiempos no presuponen cuatro personas gratis.

## Alcance cerrado

Una línea vertical: fuente de entropía sintética → metadatos de adquisición → ejecución de checks → referencias a resultados → revisión de supuestos → exportación reproducible → cambio de un parámetro → identificación de evidencia afectada. La versión inicial no emite certificados, no se conecta a producción de NIST, no automatiza instrumentos externos y no cubre todos los esquemas con profundidad.

## Backlog con aceptación

| ID | Prioridad | Trabajo | Responsable | Dependencias | Criterio observable de terminado |
|---|---|---|---|---|---|
| P01 | P0 | Modelo de datos y vocabulario | A+C | — | Cinco casos ambiguos representados sin un booleano de compliance |
| P02 | P0 | Perfil versionado y localizadores | C | P01 | Cada requisito apunta a edición/ID y define aplicabilidad; error si falta versión |
| P03 | P0 | Ingesta de archivos y límites | A | P01 | Rechaza traversal, duplicados ambiguos y tamaños no admitidos; digest reproducible |
| P04 | P0 | Almacén por contenido | A | P03 | Modificar un byte invalida verificación; colisión de ID lógico no sobrescribe objeto |
| P05 | P0 | Snapshot de producto/Git | B | P01 | Captura commit y árbol sucio; diferencia code revision de build digest |
| P06 | P0 | Runner de checks permitidos | B | P02,P03 | Perfil no ejecuta shell; timeout/error queda como estado propio |
| P07 | P0 | Procedencia y parámetros | B | P06 | Reejecución local con inputs fijados reproduce un check determinista |
| P08 | P0 | Matriz de trazabilidad | C | P02,P04,P07 | Muestra faltantes y referencias rotas; ninguna ausencia cuenta como PASS |
| P09 | P0 | Hallazgos y revisión | A+C | P08 | Una decisión tiene autor, rationale y snapshot; histórico preservado |
| P10 | P0 | Export HTML/JSON y verificador | C | P04,P08 | Máquina limpia verifica paquete sin contactar CryptoSure |
| P11 | P0 | Detección de cambios | A | P01,P09 | Cambio deliberado marca exactamente la clausura declarada; pruebas de dependencias omitidas documentadas |
| P12 | P0 | Adaptador resultado 90B | B | P07 | Importa versión/log/resultado original de herramienta fijada; no infiere validez del modelo |
| P13 | P0 | Dataset sintético y benchmark | B+C | P12 | Tres fallos sembrados detectados y reproducibles; supuestos separados |
| P14 | P0 | Ensayo con evaluador | Equipo | P10,P11,P13 | Revisor encuentra evidencia, reproduce y detecta cambio sin explicación oral del desarrollador |
| P15 | P1 | Plantilla CI genérica | B | P10 | Genera artefacto local en ejemplo; no requiere permisos a producción |
| P16 | P1 | Roles en instalación privada | A | P09 | Autor no puede autoaprobar cuando política lo prohíbe |
| P17 | P1 | Importación segundo esquema | C | P14 | Reutiliza artefacto con evaluación separada, sin equivalencia automática |
| P18 | P1 | Migración de perfiles | A+C | P11,P17 | Cambio de baseline produce delta revisable y preserva evaluaciones previas |
| P19 | P2 | Firma y verificación de productor | A+B | P10, modelo de identidad | Raíz de confianza explícita; prueba de revocación/clave equivocada |
| P20 | P2 | LLM asistente de enlaces | C | benchmark adversario | Toda sugerencia tiene fuentes y revisión; ningún acceso extra por documento |

## Secuencia

Semanas 1–2: P01–P05 y contrato de export; comprobar que el modelo sirve al evaluador antes de diseñar dashboards. Semanas 3–4: P06–P08 y un ejemplo vertical. Semanas 5–6: P09–P12, historial y cambio. Semanas 7–8: P13–P14, errores adversarios y revisión externa autorizada en el futuro. Semanas 9–10: corregir hallazgos y empaquetar instalación. Semanas 11–12: incorporación de segundo piloto y, sólo si el núcleo funciona, P15/P17.

Reservar al menos un tercio de capacidad de cada bloque para correcciones, documentación y casos de borde. No llenar doce semanas con estimaciones que suman exactamente doce semanas: eso es una agenda sin margen, no un plan realizable.

## Definition of done de la primera versión pagable

El cliente puede importar un proyecto, distinguir datos originales de transformaciones, repetir un check y exportar un paquete. Un revisor descubre evidencia ausente y sabe qué no está demostrado. Cambiar un archivo crítico invalida su apoyo previo. La instalación tiene copia/restauración documentada. Ninguna conexión saliente es necesaria para verificar un paquete.

Un ensayo adversario debe cubrir al menos: mismo nombre/distinto contenido; requisito renombrado conservando semántica; versión cambiada conservando nombre; fallo del runner; resultado truncado; perfil malicioso; ruta externa; referencia inexistente; documento contradictorio; artefacto antiguo reutilizado; duplicación de evidencia que aparenta aumentar cobertura; y ausencia de hipótesis fundamental. Las pruebas deben proteger invariantes reales y no simplemente repetir la implementación.

## Trabajos excluidos del MVP

Marketplace, app móvil, entrenamiento de modelos, implementación propia de ACVP, inferencia automática de entropía certificable, análisis de canales laterales genérico, gestor de hardware de laboratorio, soporte completo para todos los PP, facturación multinacional y promesa de certificación continua. La continuidad requiere procesos y decisiones del esquema aplicable, no sólo un dashboard verde.

## Hitos de inversión de esfuerzo

**G0, semana 2:** modelo entendido por un revisor y tres casos reales de cambio descritos sin material privado. **G1, semana 4:** flujo vertical reproducible. **G2, semana 8:** benchmark de ahorro y detección de errores. **G3, semana 12:** piloto pagado o evidencia convincente de voluntad de pagar. Si G3 falla, no duplicar equipo para añadir esquemas; estudiar segmento, canal o modelo de servicios.

## Backlog comercial paralelo

Preparar guion de entrevistas, demo sintética de diez minutos, tabla de coste evitado y condiciones de piloto. Toda comunicación futura requiere autorización del usuario; esta misión no la realiza. Los pilotos no necesitan cifras generales de TAM para empezar: necesitan un comprador que acepte un resultado concreto, un precio y una evaluación de éxito.
