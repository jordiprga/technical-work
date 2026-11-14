# Fuentes primarias y alcance

Consultadas el **2026-11-14 UTC**. Las recomendaciones de arquitectura son inferencias/propuestas propias; los siguientes hechos de producto proceden de documentación primaria. No se utilizaron páginas de terceros como autoridad técnica.

| Fuente | Qué se comprobó | Qué no demuestra |
|---|---|---|
| [OpenAI — App Server](https://learn.chatgpt.com/docs/app-server) | Protocolo JSON-RPC, stdio, esquemas por versión y solicitudes de aprobación; WebSocket marcado experimental | Estabilidad de cualquier versión futura; seguridad de exponer un listener sin configuración |
| [OpenAI — Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security) | Sandbox y controles de red; superficies de apps/MCP/búsqueda separadas del proxy de comandos | Que una opción de shell bloquee toda salida del producto |
| [OpenAI — Running Codex safely](https://openai.com/index/running-codex-safely/) | Enfoque de fronteras técnicas, aprobación y observabilidad | Certificación de la arquitectura JARVIS |
| [Temporal — Workflow Execution](https://docs.temporal.io/workflow-execution) | Recuperación por historial y replay, restricciones de determinismo | Exactly-once universal para efectos externos |
| [LangGraph — Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | Diferencia entre checkpoints de hilo y stores persistentes | Portabilidad automática de conocimiento entre frameworks |
| [LangGraph — Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) | Pausa/reanudación; el nodo puede reejecutarse y repetir efectos | Que colocar un efecto tras una aprobación elimine duplicaciones tras crash |
| [SQLite — WAL](https://www.sqlite.org/wal.html) | Concurrencia y requisito de mismo host para WAL | Seguridad de DB sobre cualquier NAS o método de backup |
| [Telegram — Bot API](https://core.telegram.org/bots/api#setwebhook) | Reintentos webhook, secret_token y deduplicación vía updates | Autenticidad de intención humana o confidencialidad de contenidos enviados al bot |

Evidencia local: `codex --version` devolvió `codex-cli 0.167.0-alpha.4`; `codex exec --help` y `codex app-server --help` están conservados en `results/`. Se ejecutó sólo ayuda: no se leyeron archivos de configuración, autenticación ni perfiles personales.

Los enlaces antiguos `developers.openai.com/codex/app-server/` y `developers.openai.com/codex/security/` redirigieron a la documentación actual; el segundo conduce al producto Codex Security, no al documento de sandbox. Se usa el documento específico de approvals/security para evitar mezclar productos.

No se han verificado mediante despliegue las integraciones Codex, Telegram, Temporal, LangGraph, autenticación o backup del diseño. El código probado es el kernel offline de este directorio.
