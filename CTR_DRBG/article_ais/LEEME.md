# Artículo y reproducción

El manuscrito ofrece una exposición autosuficiente: contexto AIS y SP 800-90A, exclusión de AES-128/AES-192, antecedentes, definición de las propiedades, tuplas, hipótesis sobre AES y demostraciones de predicción e inversión. El cuerpo desarrolla las leyes de bloques, la marginal de la clave enmascarada, las intersecciones bajo claves repetidas y los casos de sucesor/predecesor. Los apéndices conservan el acoplamiento completo y la corrección por parada adaptativa. Cada demostración concluye con el requisito correspondiente y los resultados que lo justifican. Una tabla final registra esa trazabilidad y la diferencia frente al argumento del BSI. El puente con la 90A identifica cada procedimiento y las tuplas; la comparación con browsers distingue los cambios de representación de los parámetros reales. No se formula un teorema de conformidad general.

El perfil es AES-256 sin DF, con contador de 128 bits, semilla fresca uniforme de 384 bits y hasta 2^48 solicitudes por intervalo. Se incluye entrada adicional pública y adaptativa. La salida se hace utilizable tras la actualización final y se borran los temporales. Las cotas son clásicas en el modelo declarado de permutaciones ideales; se conservan los límites de alcance de AIS214 y de la variante con DF.

## Reproducir

Con Python 3.12 y Tectonic, desde esta carpeta:

```text
python verify.py
python verify_local.py
python build.py
```

Para indicar el compilador:

```text
python build.py --compiler /ruta/a/tectonic
```

`verify.py` y `verify_local.py` no requieren dependencias externas ni red. El segundo verifica por enumeración las identidades locales y la equivalencia de representación de las tuplas con parámetros comunes; escribe `verification-local.json`. Las comparaciones numéricas usan enteros y fracciones exactas; las enumeraciones pequeñas son comprobaciones de coherencia, no una formalización completa de las pruebas.

`proof-ledger.csv` y `requirements.csv` registran derivaciones y requisitos. `REVIEW.md` conserva las objeciones y correcciones. `sources-manifest.json` identifica las cinco fuentes técnicas citadas con sus ediciones, URLs y hashes. `delivery-manifest.json` identifica los bytes entregados.

La inspección opcional con `qa_render.py` requiere PyMuPDF y Pillow. Sus imágenes se guardan en `qa/`, excluido de Git. La entrega fue compilada e inspeccionada; `pdf-qa.json` registra la revisión visual, las referencias y los márgenes. La revisión de agentes y estas comprobaciones no sustituyen una revisión criptográfica externa.
