# Dos expedientes PTG.3 con conservación ITS

La nota analiza dos puertos independientes de 128 bits. Comparten un modelo de PTG.2 con Toeplitz de selector renovado. Uno usa el DRNG AES/SHA de los §§996–998 de AIS 20/31 v3. El otro usa CTR_DRBG AES-256 sin DF con una entrada presente de 384 bits cuyo campo inferior contiene el bloque físico. Los dos reciben una derivación de las tuplas, las propiedades ITS, los requisitos DRG.3 y los límites de evaluación.

[Abrir la nota técnica con diagramas y enlaces a teoremas](technical-note.pdf) · [Fuente LaTeX](technical-note.tex) · [Resultados de pruebas del kernel](formal/verification.json) · [Pruebas de ejecución y tasas](experiments/README.md)

## Resultados por puerto

| | AES/SHA de AIS | CTR_DRBG sin DF |
|---|---|---|
| Siembra y resiembra | Dos bloques dedicados de 128 bits. Asignación al arrancar y XOR con el estado vigente al resembrar. | 384 bits de material con la calidad exigida por 90A, con actualización de clave y contador y reinicio del contador administrativo. |
| Puerto ITS | Cada bloque fresco de 128 bits, incluido su efecto en el siguiente estado, da 128 bits. | Cada bloque físico ocupa los 128 bits inferiores de la entrada adicional; se actualiza el estado antes y después de cifrar el bloque de salida. |
| Resultado común | La secuencia entre resiembras conserva exactamente la distancia a uniforme y la probabilidad de adivinación condicionadas a la misma vista y al estado inicial. | Se demuestra la misma igualdad para las llamadas de 90A con este perfil exacto. |
| Compromiso | Con dos capturas y entrada uniforme, la fuga se calcula mediante las fibras de la transición SHA restringida. | El estado posterior excluye dos posibles valores de la última salida. El anterior y una palabra del posterior la determinan por completo. |
| DRG.3 | El §998 reconoce el ejemplo. El expediente verifica su especialización y desarrolla el argumento computacional bajo hipótesis declaradas sobre AES/SHA. | §1007 encarga la prueba al solicitante. El modelo de cifrado ideal permite exhibir al menos 2²⁴⁶ clases de respuesta. La reducción computacional precisa los supuestos necesarios para la predicción e inversión. La cota genérica por tramos es insuficiente para acreditar por sí sola 246 bits en una época de 1.024 peticiones. |
| NIST | Para atribuir RBG3 a un puerto se debe especificar una construcción admitida. | La generación directa, RBG3(XOR) y RBG3(RS) tienen conexiones y consumos diferentes. El expediente incluye el acondicionador CMAC y la prueba específica del primer bloque de RS. |

La salida del PTG.2 requiere un modelo físico que justifique su entropía frente al historial y al selector. El análisis utiliza datos públicos y sintéticos. Lean comprueba las igualdades de leyes clásicas finitas y la reindexación de bloques y medidas en el modelo clásico-cuántico bajo las leyes de operadores declaradas. La fuente y el lema de extracción cuántica se justifican por separado. El benchmark mide los núcleos software y especifica por separado un modelo de captación. La aceptación de las hipótesis y la evidencia del dispositivo pertenecen al expediente real.

## Reproducir

Se usan Lean **4.19.0**, sin paquetes Lean externos, Python 3.12, pdfLaTeX con TikZ, y las versiones de OpenSSL y `cryptography` indicadas en el expediente experimental. Ejecutar desde este directorio.

```bash
python3 verify.py --lean /ruta/a/lean-4.19.0/bin/lean
python3 index_proofs.py --check
(cd experiments && python3 -m unittest -v test_profiles)
mkdir -p /tmp/ptg3-pdf
for pass in 1 2 3; do
  pdflatex -halt-on-error -interaction=nonstopmode -output-directory=/tmp/ptg3-pdf technical-note.tex || exit 1
done
```

`verify.py --report /tmp/ptg3-verificacion.json` guarda los hashes SHA-256 de los fuentes compilados y los axiomas transitivos de cada teorema público. Se rechazan huecos de demostración y dependencias distintas de los principios lógicos estándar admitidos. Las hipótesis criptográficas son argumentos visibles de los teoremas. Al actualizar los archivos Lean, ejecutar `python3 index_proofs.py` para regenerar las líneas de los enlaces del PDF y volver a compilar.

El archivo histórico `drg3-ctr-addendum.pdf` corresponde a una revisión anterior. El artículo integrado y sus fuentes en esta carpeta contienen los resultados vigentes.
