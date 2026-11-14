# JARVIS: arquitectura personal y kernel de control

JARVIS debe separar **agentes que proponen** de **servicios que autorizan y ejecutan**. La primera versión recomendada vive íntegramente en un VPS: navegador móvil/web, conocimiento portable, SQLite/PostgreSQL, Git y workers aislados. No necesita ni puede acceder al PC local de Jordi.

Este directorio contiene diseño y un prototipo offline ejecutado. No es un sistema desplegado ni tiene conectores activos.

## Entregables

| Archivo | Utilidad |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Componentes, flujos, memoria, Git/Codex, interfaces y decisiones |
| [SECURITY.md](SECURITY.md) | Modelo de amenazas, aprobación exacta, invariantes y límites |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Backlog 30/90 días, criterios de aceptación y experimentos |
| [SOURCES.md](SOURCES.md) | Fuentes primarias, fecha y alcance comprobado |
| [RESTORE.md](RESTORE.md) | Protocolo de recuperación y verificación de proyecciones |
| [src/jarvis_kernel.py](src/jarvis_kernel.py) | Inbox, permisos, aprobación HMAC, presupuesto, auditoría y estados |
| [src/verify_snapshot.py](src/verify_snapshot.py) | Verificador independiente de export, cadena y ledger |
| [tests/test_kernel.py](tests/test_kernel.py) | Pruebas positivas, negativas, concurrentes y de recuperación |
| [schemas/](schemas/) | Contratos portables de propuesta y evidencia |
| [results/](results/) | Evidencia de ejecución, demo y ayuda local de Codex |
| [Revisión independiente de CryptoSure](reviews/cryptosure/README.md) | Dos hallazgos reproducidos, corregidos y revalidados |
| [Revisión del bridge formal](reviews/formal_bridge.md) | Procedencia Lean→recibo→CryptoSure y dos mejoras del runner verificadas |

## Ejecutar

Python 3.12, sin dependencias externas:

```bash
cd /workspace/operation-token-burn/06_jarvis_architecture
python3 -m unittest discover -s tests -v
python3 src/jarvis_kernel.py --demo /tmp/jarvis-demo-nueva
```

La demo exige un directorio sin base de datos anterior. Guarda SQLite, `export.json` y `demo-report.json`; genera la clave HMAC sólo en memoria. No solicita claves, no llama a modelos, no ejecuta comandos de agentes ni contacta sistemas externos. `simulated-human` representa una aprobación sintética de prueba, no una aprobación real de Jordi. Los 125 tokens contabilizados son datos sintéticos.

La suite comprueba: cambios de plan/política, caducidad antes de admisión y despacho, identidad declarada frente al caller del broker, denegación de efectos externos, colisiones de idempotencia, replay, doce admisiones concurrentes sin exceder cupo, crash con reserva retenida, manipulación de eventos, reconstrucción del ledger y necesidad de checkpoint externo para detectar truncación. La demo vigente está en `results/demo-final`; las anteriores son intermediarios conservados.

## Resultado y límites

- Existe código funcional y una demo verificable de control de admisión; no un orquestador distribuido completo.
- Un permiso autoriza un recurso virtual `artifact:project/path`; no hay executor de filesystem. Por ello no se atribuye al prototipo resistencia a symlinks ni un sandbox del sistema operativo.
- HMAC prueba integridad ante quien no posee la clave. No prueba que un humano haya revisado la propuesta y no aporta no repudio.
- La cadena de hashes detecta cambios respecto a un checkpoint confiable. El administrador que controla toda la base puede reescribir cadena y tablas; hace falta anclaje fuera de ese dominio.
- Se confían `caller`, reloj, autoridad, política y llamadas internas `start`/`finish`; en producción estarán en un broker inaccesible al worker.
- El contador limita reservas internas. El gateway del proveedor debe imponer límites reales por petición y cerrar al alcanzar el techo; el prototipo no puede imponer gasto a una API que no invoca.
- Ningún resultado equivale a certificación de seguridad.

El diseño y las decisiones propias están etiquetados como **propuesta**; capacidades de productos se apoyan en documentación primaria consultada el 14-11-2026. La versión local observada fue `codex-cli 0.167.0-alpha.4`; las interfaces experimentales deben fijarse por versión.
