# Revisión independiente de integración y empaquetado

Revisor: agente CryptoSure prototipo. Ventana: 2026-11-14 11:53–11:57 UTC.
Lectura de `verify_all.py` y `build_release.py` de coordinación; **sin modificar esos archivos**.
Los hashes exactos de la versión inspeccionada y el inventario observado se conservan
en [`../results/packaging-review.json`](../results/packaging-review.json).

## Resultado principal

El diseño conserva bytes y hashes de los archivos copiados y evita mezclar cachés de
investigación, compilación, SQLite o trazas NPZ en la publicación. A las 11:54:59 la
colección incluía 331 archivos, 6.134.822 bytes y excluía 82 archivos. No había entradas
que infringieran la propia política de exclusión.

Es necesario ejecutar la verificación conjunta después de congelar los módulos y
comprobar que sus hashes coincidan con los de la release. El summary conservado durante
esta revisión correspondía a las 11:45:56 y estaba desactualizado: seis misiones habían
añadido o modificado código. Esto es esperable durante el trabajo paralelo, pero ese
summary no debe presentarse como verificación de la baseline final.

## Hallazgos comunicados a coordinación

| Hallazgo | Consecuencia | Acción recomendada |
|---|---|---|
| Resumen anterior al congelado | Por ejemplo, contaba 46 tests CryptoSure cuando la suite final ya ejecuta 49 | Ejecutar `verify_all.py --require-lean --lean ...` al cerrar |
| El empaquetador no liga por sí mismo manifest y hashes del resumen de tests | Una copia íntegra puede incluir fuentes distintas de las ensayadas | Comparar cada `directory/source_sha256` del summary con el manifest final |
| Timestamp actual en `RELEASE_MANIFEST.json` | Dos builds de fuentes iguales producen ZIP diferentes aunque sus entradas tengan fecha fija | Describir «orden y metadatos ZIP estables», o permitir timestamp fijo para reproducibilidad bit a bit |
| `target.with_suffix('.zip')` y ausencia de comprobación de existencia del ZIP | Un target con sufijo puede colisionar con otro archive; un ZIP previo puede sobrescribirse | Usar nombre concatenado `str(target)+'.zip'` y rechazar archivo existente |
| Fingerprint de tests cubre ciertas extensiones y excluye results/figures | `current_source_matches_snapshot` no significa que toda la release sea idéntica | Presentarlo como fingerprint de fuentes seleccionadas; conservar manifest completo de release |

No se detectó un falso PASS actual en los logs revisados. El runner exige exit code
cero y al menos un test o marcador formal; rechaza la ausencia de tests. No se
encontraron suites completamente omitidas mediante skips en los tests inspeccionados.
Como mejora posterior, el conteo debería proceder de un resultado estructurado en
lugar de buscar la primera cadena `Ran N tests` en stdout/stderr. La lógica actual
no es un verificador robusto frente a un test deliberadamente malicioso que imprima
un contador ficticio; ese adversario no forma parte del conjunto de tests generado.

## Consistencia de snapshots y recibos

`verify_all.py` copia cada misión a un directorio temporal, compara su fingerprint con
el original y vuelve a comprobar las fuentes al terminar. Eso evita presentar como
actual un resultado cuya fuente cubierta cambió durante la prueba. La verificación
formal copia sus recibos desde el snapshot ejecutado, lo que es preferible a adjuntar
un recibo de otra ejecución del árbol activo.

`build_release.py` lee cada archivo una vez, escribe esos bytes y calcula su hash sobre
los mismos bytes. El manifest puede comprobar integridad de la copia. No es un snapshot
atómico de todo el árbol: si otros agentes siguen editando, puede mezclar instantes.
La congelación de entregables y el cotejo posterior con los fingerprints de tests
siguen siendo necesarios. El sello no acredita autoría ni certificación, como declara
el propio empaquetador.

Un cotejo suficiente de la parte cubierta por tests es:

```python
# Sobre el summary y RELEASE_MANIFEST.json de la release, ya leídos localmente.
manifest_by_path = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
for result in summary["results"]:
    assert result["status"] == "PASS"
    for relative, digest in result["source_sha256"].items():
        combined = result["directory"] + "/" + relative
        assert manifest_by_path[combined] == digest
```

Debe verificarse además que los archivos de la release tengan los hashes del manifest;
comparar sólo dos documentos de hashes no autentica sus contenidos.

## Cierre de CryptoSure

Se ejecutaron `verify` y `replay` con pins externos sobre `final-demo-v2` y
`formal-bridge-v2` a las 11:54:04. Ambas conservan integridad, resultados reproducidos
y `same_tool_source:true`. El resultado técnico permanece REVIEW. El registro completo
está en [`../results/closure-verification.json`](../results/closure-verification.json).

Los bundles intermedios anteriores se conservan con su fecha e identidad; no se
confunden con la baseline actual. Un recibo formal posterior puede incorporarse como
otra evidencia sin sobrescribir los anteriores. Ninguna importación de un recibo
supone ejecutar Lean ni aprobar la correspondencia entre modelo y producto.

Actualización de cierre a las 11:57: el recibo formal definitivo se incorporó a
`formal-bridge-v3`, conservando las versiones anteriores. `results/closure-final.json`
registra replay coincidente y el mismo código para demo-v2 y bridge-v3. El código
CryptoSure no cambió durante esta actualización de evidencias.

## Alcance de esta revisión

Se revisaron código y archivos locales públicos/sintéticos. No se construyó una release
desde este agente, no se publicó nada, no se accedió a credenciales y no se realizaron
operaciones GitHub. Las decisiones de publicación y el cierre global corresponden a
coordinación. Los hallazgos describen las versiones identificadas por hash; cambios
posteriores del coordinador requieren cotejar su estado final.
