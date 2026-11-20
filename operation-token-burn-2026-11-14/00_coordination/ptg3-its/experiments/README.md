# Comparación reproducible de los dos núcleos

Pruebas y mediciones sobre vectores públicos y datos sintéticos. El flujo con entrada física obtiene un bloque de salida por llamada. Los estados publicados aquí son de prueba.

## Reproducción

Se requiere Python 3.12 y `cryptography==50.0.0` para reproducir la configuración guardada. Desde este directorio se ejecuta

```sh
python -m unittest -v test_profiles
python benchmark.py > /tmp/ptg3-benchmark-nuevo.json
python make_traces.py > /tmp/ptg3-trazas-nuevas.json
diff profile_traces.json /tmp/ptg3-trazas-nuevas.json
```

`make_traces.py` invoca por separado el ejecutable `openssl` para cada cifrado y transcribe las transiciones paso a paso. Aquí se usó OpenSSL CLI 3.5.7. El script fija un `p` público no nulo, una muestra nula presente, dos transacciones y un contador inicial cercano a la vuelta de 128 bits. La implementación perfilada en `profiles.py` usa el backend OpenSSL del paquete `cryptography`, que puede diferir del ejecutable del sistema. Se conservan entrada y estado posterior de ambas implementaciones. La interfaz experimental admite llamadas ya autorizadas por el controlador de salida. Las rutinas de siembra y las pruebas usan únicamente material sintético.

## Vectores NIST

`nist_vectors.json` conserva cuatro casos `COUNT=0` de `CTR_DRBG.txt`, modo AES-256 no DF, 512 bits devueltos, nonce y personalización vacíos. Los valores oficiales comparados son el resultado de la segunda generación y los estados internos K,V tras la instanciación, la resiembra aplicable y cada generación. Los contadores administrativos se contrastan con la transición de 90A. `AdditionalInputLen` es 0 o 384 en `drbgvectors_no_reseed.zip` y `drbgvectors_pr_false.zip`. El archivo conserva nombre y SHA-256 del miembro fuente. La regeneración a partir del archivo público usa

```sh
python extract_vectors.py /ruta/drbgtestvectors.zip > /tmp/ptg3-cavp.json
diff nist_vectors.json /tmp/ptg3-cavp.json
```

Archivo consultado el 20 de noviembre de 2026, SHA-256 `5f7e5658ebd5b4e6785a7b12fa32333511d2acc2f2d9c5ae1ffa16b699377769`. [NIST CAVP DRBG](https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Algorithm-Validation-Program/documents/drbg/drbgtestvectors.zip) · [SP 800-90A Rev. 1](https://doi.org/10.6028/NIST.SP.800-90Ar1)

## Lectura de resultados

`results.json` contiene siete tasas brutas por núcleo, p50/p99 de tiempo de pared por llamada individual, hashes del código cronometrado y versiones. `benchmark.py` calienta el intérprete, alterna el orden de los núcleos, cronometra tasa y latencia en pases distintos y utiliza SHAKE únicamente para preparar las entradas antes de medir. Ejecutar este microbenchmark en paralelo con otras cargas añade ruido. El backend agrupa las palabras cifradas bajo una misma clave. El coste incluye asignaciones de Python y cambio de clave por llamada según el perfil. La fuente, el acondicionamiento, la siembra y el cómputo de Toeplitz quedan fuera de esta medida. Los tramos cronometrados omiten las pausas del controlador de época de 1024 peticiones. No se usa material de dispositivos reales.

El modelo de coste raw distingue datos, selector, guardas y ensayos descartados. Evalúa lotes de 1, 4 y 16 bloques, con un selector nuevo por lote y una llamada completa por cada bloque de 128 bits entregado. El tamaño de lote 1 es el perfil principal. La columna `source_only_Mbit_s` es una predicción calculada con una frecuencia de adquisición supuesta. Todas las observaciones temporales del experimento proceden del núcleo software. Los supuestos de adquisición y distribución del selector son sintéticos. La entropía asumida para los datos debe acreditarse incluso condicionando a la aceptación, los datos laterales y el historial. La cota LHL del ejemplo gasta el presupuesto indicado bajo selector ideal. Con un selector real se asigna una fracción al error de dependencia conjunta; si se reserva la mitad, el requisito LHL crece en dos bits de minentropía por lote. La calidad física y la admisibilidad AIS de los lotes anchos requieren evidencia propia. [SP 800-90C](https://doi.org/10.6028/NIST.SP.800-90C)

## Observación de salida

`python3 diagnostics.py` reproduce los conteos y los hashes de `diagnostics.json`. Se usan 16 épocas de 1024 peticiones por núcleo y modo. Las 12 comparaciones examinan frecuencia, alternancia intrabloque y relación entre bloques adyacentes en semillas y entradas sintéticas públicas. El umbral bilateral de Hoeffding toma como referencia bits ideales independientes, con presupuesto familiar de 0,01. Este ensayo caracteriza el software medido. La fuente física y la suite de su expediente se evalúan por separado.
