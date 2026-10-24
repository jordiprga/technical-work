# Artículo en la estructura del ejemplo AIS Hash_DRBG

`main.tex` comienza por la 9-tupla y las dos 4-tuplas; después presenta las hipótesis y la justificación de cada propiedad. XDRBG se usa sólo como referencia de presentación. No se traslada ninguna propiedad suya a CTR_DRBG.

El perfil principal usa AES-256, contador de 128 bits y no DF. La fuente fresca uniforme de 384 bits es una hipótesis explícita; no se intenta sustituir su evaluación. El argumento de composición incluye el intervalo NIST completo de 2^48 solicitudes y entrada adicional pública/adaptativa, conservando su preactualización y actualización final. El PDF exige salida utilizable tras la actualización final y borrado de temporales.

Las cotas numéricas son resultados en el modelo de permutaciones ideales; aplicar ese modelo al AES concreto requiere la hipótesis criptanalítica declarada. Consulte las condiciones y límites exactos en el artículo y en REVIEW.md. El mapa de siembra con DF se distingue expresamente del principal: citar un componente de acondicionamiento aprobado no prueba automáticamente su concreta entropía efectiva.

## Reproducir

Desde esta carpeta, con Python 3.12 y Tectonic:

```text
python verify.py
python build.py
```

Para usar otro ejecutable de Tectonic:

```text
python build.py --compiler /ruta/a/tectonic
```

`verify.py` no requiere paquetes externos ni red. Escribe `verification.json`; las comparaciones que deciden éxito usan enteros y fracciones exactas. Las enumeraciones de modelos pequeños sólo comprueban coherencia: no sustituyen la demostración escrita para128 bits.

`proof-ledger.csv` registra las derivaciones y limitaciones; `requirements.csv` enlaza los requisitos AIS; `sources-manifest.json` identifica las ediciones y hashes sin publicar la biblioteca local de documentos ajenos. El PDF se compila y se inspecciona visualmente antes de entregarlo. `delivery-manifest.json` permite verificar los archivos finales.

El cierre adaptativo completo de la condición adicional de AIS214 sigue abierto: las cotas escritas son de cómputo ordinario. No se presenta el resultado como conformidad DRG.3 irrestricta ni como contraejemplo al algoritmo. Esta limitación se mantiene breve y separada de la demostración principal por tuplas.

Inspección visual opcional: `qa_render.py` requiere PyMuPDF y Pillow; sus imágenes quedan en `qa/`, excluido de Git. El PDF entregado tiene11 páginas y ha pasado inspección visual y comprobaciones de referencias y márgenes.
