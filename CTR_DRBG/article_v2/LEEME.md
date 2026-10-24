# CTR_DRBG: artículo vigente

Esta carpeta contiene el artículo en inglés main.tex y su PDF, la bibliografía, la matriz DRG.3, el registro de lemas y la revisión crítica. La conclusión es condicional al modelo de cifrador ideal y al perfil P64, con fuente suficiente asumida. No se afirma una prueba para todo el rango NIST.

Desde esta carpeta, con Python3.12:

```text
python -m pip install -r requirements-dev.txt
python verify_chain.py
python verify.py
python build.py
```

build.py requiere Tectonic en PATH. Para otro ejecutable: `python build.py --compiler RUTA_AL_EJECUTABLE`. Tectonic descarga los paquetes tipográficos en su primera ejecución. Los ficheros auxiliares y logs están ignorados por Git; el PDF se conserva como entregable.

verification_chain.json registra comprobaciones racionales y modelos reducidos; verification_smt.json registra cuatro identidades SMT y comprobaciones anteriores. La prueba general de probabilidad y los argumentos cuánticos son escritos y revisados, no una formalización completa en un asistente de pruebas.

sources-manifest.json contiene URLs, versiones y SHA256 sin rutas personales. Los originales se conservan en la biblioteca local y no están incluidos en este repositorio. REVIEW.md y proof-ledger.csv explican la cobertura y las objeciones resueltas.
