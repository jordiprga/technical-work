# CryptoSure — prototipo funcional offline

Motor de requisitos versionados, evidencias por contenido, comprobaciones automáticas,
trazabilidad e informes. Implementado con Python estándar, sin servicios externos.
**No decide conformidad ni concede certificaciones.** Los perfiles incluidos son sintéticos.

## Ejecutar en menos de un minuto

Desde este directorio, con Python 3.11 o superior:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 examples/demo.py --out /tmp/cryptosure-demo-nuevo
PYTHONPATH=src python3 -m cryptosure verify /tmp/cryptosure-demo-nuevo/bundle
PYTHONPATH=src python3 -m cryptosure replay /tmp/cryptosure-demo-nuevo/bundle
```

Usar una ruta de salida nueva: las ejecuciones no sobrescriben bundles existentes.
No se necesita instalación ni descarga de dependencias. `pyproject.toml` permite
empaquetado convencional, pero no es necesario para la demostración.

La demo produce un requisito PASS técnico y tres REVIEW. Un flujo **determinista
alternante**, de entropía cero cuando es conocido, aprueba los RCT/APT configurados.
Es un contraejemplo ejecutable a la afirmación «pasa health tests, luego tiene entropía».

## Qué está implementado

| Capacidad | Implementación y límite |
|---|---|
| Ingesta de requisitos | JSON estricto, identificadores únicos, versión de perfil y metadatos de estándar; no extracción automática de texto normativo |
| Evidencias verificables | Snapshot de archivos, SHA-256, tipo MIME, tamaño, nombre de origen y fecha; integridad no equivale a autoría |
| Ejecución | Cuatro plugins puros permitidos: vectores SHA-256, RCT binario, APT binario y comparación de campo JSON |
| Trazabilidad | Relaciones requisito → check → artefacto → digest; CSV e informe Markdown |
| Reproducibilidad | Bundle portable con entradas exactas, resultados, código identificado por digest y reejecución local |
| Cambio de baseline | `diff` identifica cambios de requisito, evidencias, perfil, herramienta y metadatos Git |
| Git | HEAD, árbol e índice por hash; no commit/push ni `status`/`diff`, y working tree expresamente no evaluado |
| Extensión | Registro de plugins en código confiable; perfiles no pueden importar módulos ni ejecutar shell |

No existe un estimador 90B completo, cliente ACVP/ESV, conector de laboratorio,
motor de firma, gestión de revisores ni interpretación normativa de CC/EUCC/MEGA.

## Flujo CLI

```bash
PYTHONPATH=src python3 -m cryptosure validate examples/profile.json
PYTHONPATH=src python3 -m cryptosure plugins

PYTHONPATH=src python3 -m cryptosure import \
  --store /tmp/cryptosure-store \
  --id sha256-vectors \
  --source-root examples/data \
  --path sha256-vectors.json \
  --media-type application/json

PYTHONPATH=src python3 -m cryptosure run \
  --profile examples/profile.json \
  --store /tmp/cryptosure-store \
  --out /tmp/cryptosure-bundle-incompleto
```

El último comando queda BLOCKED porque sólo se importó una evidencia: la ausencia
de entradas nunca se transforma en PASS. Para un flujo completo, usar `examples/demo.py`.

`--repo /ruta/a/repo-publico` es opcional y sólo acepta la raíz de un repositorio
normal con `.git` interno. No examina el PC local. Los worktrees con gitdir externo
se rechazan en esta versión. `dirty:null` significa **desconocido**, no limpio.
Los artefactos ejecutados se vinculan por sus hashes; un commit no reemplaza ese vínculo.

## Interpretación de estados y salida para CI

| Estado | Significado | Exit code de `run` |
|---|---|---:|
| PASS | Todos los checks técnicos declarados aprueban y no se exige revisión | 0 |
| REVIEW | Falta juicio humano; no hay aprobación automática | 3 |
| FAIL | Existe al menos una comprobación técnica fallida | 4 |
| BLOCKED | Evidencia ausente/corrupta, entrada inválida, plugin desconocido o límite excedido | 5 |
| Error de ejecución/esquema | No se pudo completar la operación | 2 |

FAIL prevalece sobre BLOCKED para no ocultar fallos ya observados. Un estado desconocido
se trata como BLOCKED. No existe NOT_APPLICABLE automático: su justificación requiere
un modelo de alcance y aprobación humana que aún no se implementa.

Una integración CI debe conservar todos los códigos distintos de cero como resultado
no aprobado y adjuntar el bundle local como artefacto. No debe transformar REVIEW en
PASS para obtener una pipeline verde. No hay workflows desplegados ni llamadas a GitHub.

## Integridad y reejecución

El comando `run` devuelve `root_sha256`, el hash de `seal.json`. El sello enumera los
hashes y tamaños de perfil, entradas, resultados e informes. Para comprobar un digest
conservado por un canal de confianza:

```bash
PYTHONPATH=src python3 -m cryptosure verify /ruta/bundle \
  --expected-root DIGEST_SHA256_DE_64_HEXADECIMALES
PYTHONPATH=src python3 -m cryptosure replay /ruta/bundle \
  --expected-root DIGEST_SHA256_DE_64_HEXADECIMALES
```

`verify` comprueba bytes, estructura y ausencia de archivos sin sellar. Sin pin externo,
un atacante capaz de modificar el bundle puede recalcular todos sus hashes; el test
`test_recomputed_seal_needs_external_pin_to_detect_attacker` lo demuestra.

`replay` además repite los checks sobre los bytes incluidos, compara resultados,
agregación y metadatos, y vuelve a generar informe y CSV. No demuestra que los datos
provengan del dispositivo declarado ni que el perfil represente todos los requisitos.
Informa si el digest del código actual coincide con el registrado. Reproducir bundles
históricos puede fallar tras una modificación del motor o del formato de informe.

## Control de cambios

```bash
PYTHONPATH=src python3 -m cryptosure diff /ruta/baseline-anterior /ruta/baseline-nuevo \
  --old-root DIGEST_ANTERIOR --new-root DIGEST_NUEVO
```

El análisis verifica sellos y los vínculos perfil/ejecución y artefactos/ejecución, y marca requisitos a revisar
cuando cambian sus entradas. No reejecuta los checks: `semantic_replay_verified:false`
es explícito. Un timestamp de ejecución distinto no invalida por sí solo entradas
idénticas. Cambios de metadatos del perfil, herramienta o Git afectan conservadoramente
a todos los requisitos. No se heredan aprobaciones humanas.

## Archivos de entrega

- [Arquitectura y contratos](docs/architecture.md).
- [Modelo de amenazas y límites](docs/security.md).
- [Extensión por estándares y backlog](docs/extension-plan.md).
- [Fuentes primarias consultadas](docs/sources.md).
- [Suite ejecutable](tests/test_cryptosure.py) y [registro de tests](results/test-log.txt).
- [Informe final de demostración](results/final-demo-v2/bundle/report.md) y
  [puente de evidencia formal](results/formal-bridge-v3/bundle/report.md).
- `results/demo/` conserva la primera ejecución intermedia; no se presenta como baseline
  del código final. La baseline consolidada y sus digests figuran en `STATUS.md`.

Los datos, títulos y modelos son públicos o inventados. No se han consultado sistemas,
documentos, credenciales ni parámetros privados de Quside.
