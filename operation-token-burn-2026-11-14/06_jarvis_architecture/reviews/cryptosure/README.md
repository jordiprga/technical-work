# Revisión independiente de CryptoSure

Revisor: misión JARVIS. Sólo lectura de código de `02_cryptosure_prototype`; pruebas y reportes guardados aquí. Los bundles adversarios fueron temporales y sintéticos. No hubo red, credenciales, Git remoto ni cambios en archivos del propietario revisado.

## Hallazgos y cierre

| ID | Hallazgo inicial | Corrección del propietario | Verificación independiente final |
|---|---|---|---|
| CR-01 | `replay_bundle` cargaba artefactos sin aplicar el límite agregado que sí tenía `run_profile` | Presupuesto total de bundle y de snapshots durante replay | Límite reducido a 1 byte provoca rechazo; sin consumo masivo de memoria |
| CR-02 | Se verificaban hashes y luego se reabrían archivos; sustitución del directorio mezclaba root antiguo y resultados nuevos | `read_verified_bundle` captura bytes verificados una vez; replay/diff usan esos bytes | Sustitución inyectada tras snapshot: disco cambia REVIEW→FAIL; replay conserva REVIEW del snapshot original pinneado |
| OBS-01 | Demo intermedia anterior al renderer actual no reproducía el informe | Regeneración final a cargo del propietario; conservar intermediario marcado | Harness genera fixture fresca propia y confirma baseline reproducible |

CR-02 era una vulnerabilidad de asociación de evidencia bajo modificación concurrente del bundle. El test no necesita ganar una carrera probabilística: intercepta el retorno de la verificación y reemplaza un directorio temporal por otro bundle válido. Antes de la corrección el resultado incluía pin original y resultado del nuevo bundle; después usa el snapshot correcto.

No quedan hallazgos abiertos entre las comprobaciones ejecutadas. Esto no equivale a auditoría exhaustiva ni certificación. No se probó aislamiento del sistema operativo, resistencia ante un administrador hostil ni todas las carreras de filesystem. El root digest necesita un canal confiable externo para atribuir integridad histórica.

## Evidencia

- `report-initial.json`: CR-01 reproducido; controles de pin, rendering y parser comprobados.
- `report-after-budget-fix.json`: CR-01 corregido; CR-02 reproducido con `old_root_returned=true` y resultado FAIL de bundle reemplazado.
- `report-final.json`: ambas correcciones confirmadas, `attack_injected=true` y `safe_snapshot_used=true`.
- Cada reporte incluye SHA-256 de archivos fuente revisados. Si cambian después, es necesario reejecutar el harness para ampliar el alcance de la revisión.

```bash
cd /workspace/operation-token-burn/06_jarvis_architecture
python3 reviews/cryptosure/redteam.py
```

Otros controles que respondieron como esperado: alteración de bytes sin reseal, rehash con pin externo, informe manipulado con reseal, archivo extra sin sellar, symlink, claves JSON duplicadas, números no finitos, Markdown con HTML/enlaces inyectados y prefijos de fórmulas CSV. La aceptación de un bundle rehashed **sin** pin es consistencia interna declarada, no un fallo de autenticidad: la API marca `authenticity_verified=false`.
