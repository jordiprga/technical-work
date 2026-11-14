# Entorno y límites observados

Inspección inicial: 2026-11-14, 11:29–11:33 UTC.

- `/workspace` no contenía repositorio de trabajo, README ni AGENTS.md accesibles del proyecto. Se ha creado un árbol nuevo y aislado en `/workspace/operation-token-burn`.
- Concurrencia disponible: siete agentes, incluidos el coordinador y seis especialistas. No se ha supuesto paralelismo ilimitado.
- Python 3.12.14; disponibles NumPy, SciPy, Matplotlib, pandas y SymPy. `pytest` no estaba instalado: los proyectos pueden usar `unittest`.
- Git, curl, Node, npm y pdftotext disponibles. Lean y Lake no estaban en PATH inicial; la misión formal prepara su toolchain aislada.
- Búsqueda web y lectura de fuentes públicas disponibles. Las aplicaciones conectadas no se han usado para buscar datos personales o empresariales.
- No se dispone de telemetría fiable del saldo semanal de tokens ni de su reinicio. No puede verificarse un consumo del 80 %. La restricción operativa es una ventana aproximada de 37 minutos desde 11:29 UTC.
- Los seis directorios de misión tienen propietario separado; el coordinador escribe en la raíz y `00_coordination`.
- No acceso al PC local, sistemas o documentación privada de Quside, credenciales, operaciones financieras, compras, comunicaciones, despliegues o publicaciones.

Las lecturas web de normas no sustituyen la revisión de su versión aplicable con el laboratorio y organismo correspondientes. Los prototipos se ejecutan sobre fixtures y datos sintéticos.

Actualización de alcance, aproximadamente 11:46 UTC: Jordi autorizó expresamente subir el trabajo a su GitHub. El coordinador prepara una publicación separada y excluye cachés de documentos externos, toolchains y ficheros regenerables. La cuenta conectada comprobada es `jordiprga`. La prohibición de acceso al PC local y a información privada de Quside sigue vigente.
