# Artículo y reproducción

El artículo sigue este recorrido: introducción; CTR_DRBG según la90A (parámetros, DF/noDF y procedimientos); clase DRG.3 y sus diez requisitos; análisis de conformidad con9-tupla,4-tuplas y demostración por propiedad; conclusiones y cuestiones abiertas. Se han retirado las comparaciones de productos. El antecedente citado se utiliza para las tuplas y el argumento de plausibilidad; el ejemplo Hash_DRBG del AIS orienta el desarrollo de las pruebas.

La configuración es AES-256 sin DF, incremento completo de128 bits y hasta2^48 solicitudes por intervalo. La prueba presupone entrada fresca condicionalmente uniforme de384 bits. La fuente admisible se asume; se demuestra el procesamiento algorítmico posterior. Los resultados probabilísticos son clásicos en el modelo declarado. La aplicabilidad a AES concreto se discute mediante evidencia criptanalítica, modelos de acceso y una hipótesis explícita sobre claves secretas derivadas; no se afirma una reducción universal ni una cota cuántica inferior.

## Compilar y verificar

```text
python verify.py
python verify_local.py
python build.py
python build.py --review-jordi
```

Para seleccionar el compilador, añadir --compiler /ruta/a/tectonic. Para renderizar e inspeccionar:

```text
python qa_render.py
python qa_render.py --review-jordi
```

Los verificadores usan enteros/fracciones exactos y enumeraciones reducidas; no requieren paquetes externos ni red. El renderizador requiere PyMuPDF y Pillow. Las imágenes y registros de compilación quedan fuera de Git.

## Revisar el argumento

[NOTATION.md](NOTATION.md) fija los símbolos. g(a) es la única notación para la entrada procesada; pad es padding y Pi_i una permutación auxiliar. Requests y grupos tienen índices distintos, relacionados por y(i); no se introduce una segunda entrada procesada.

[RIGOR_REVIEW.md](RIGOR_REVIEW.md) compara las hipótesis, reducciones, conteos y conclusiones con los párrafos1009–1076 del AIS para Hash_DRBG. [requirements.csv](requirements.csv) y [proof-ledger.csv](proof-ledger.csv) enlazan requisitos y derivaciones. [REVIEW.md](REVIEW.md) conserva las objeciones y correcciones. La revisión de agentes no constituye revisión criptográfica externa ni aceptación editorial.

## Edición para Jordi

review-jordi.pdf añade25 recuadros contextuales numerados J1–J25. Las llamadas jordinote de main.tex solo se muestran si review-jordi.tex activa JordiReview. Compilar main.tex las oculta; ambas ediciones conservan la misma numeración de resultados. Para retirarlas definitivamente se eliminan las llamadas y el pequeño bloque de macros.

Los hashes de las fuentes están en sources-manifest.json; los de la entrega en delivery-manifest.json. Los registros pdf-qa documentan la inspección del resultado final.

## Formato y lectura visual

[TEMPLATE.md](TEMPLATE.md) identifica la clase original ToSC, su revisión, licencia y hash. El archivo iacrtrans.cls debe acompañar a main.tex al compilar. La clase establece fuentes, márgenes y títulos; el texto usa ecuaciones alineadas, captions coherentes, tablas flexibles y algoritmos numerados.

[proof-paths.html](proof-paths.html) es un documento independiente en español para comparar las tuplas y las cadenas de razonamiento de Hash_DRBG y CTR_DRBG. Abrirlo en un navegador: el HTML es autosuficiente y contiene sus recursos matemáticos para funcionar sin conexión. proof-assets/ conserva los originales y la procedencia de KaTeX bajo licencia MIT. Los enlaces identifican párrafos del AIS y etiquetas de las demostraciones, y las explicaciones separan premisas, desarrollos y conclusiones.
