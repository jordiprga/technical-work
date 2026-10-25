# Revisión de rigor: Hash_DRBG del AIS y el argumento CTR_DRBG

Esta revisión compara el contenido de la argumentación, no el número de ecuaciones ni el uso de entornos de teorema. El patrón es *A Proposal for Functionality Classes for Random Number Generators*, versión3.0,10 de septiembre de2024, §5.3.1, párrafos1009–1076. La edición y el hash del original consultado están en [sources-manifest.json](sources-manifest.json); la [referencia oficial AIS](https://www.bsi.bund.de/dok/ais-20-31-appx-2024) identifica el documento. El objeto revisado es [main.tex](main.tex), con su [matriz de requisitos](requirements.csv) y [registro de derivaciones](proof-ledger.csv).

## Cobertura de toda la sección5.3.1

El patrón es la sección completa, titulada *Security Evaluation of the Hash−DRBG [SP800-90A]*, desde¶1009 hasta¶1076, páginas impresas205–218 (PDF213–226).¶1007 aporta además el contexto específico de CTR_DRBG. La comparación de¶1040–1046 se refiere únicamente a las hipótesis criptográficas, no sustituye la comparación del conjunto.

| Párrafos AIS | Función dentro de su demostración | Correspondencia y decisión en CTR_DRBG |
|---|---|---|
|1009–1012|Objetivo, referencia90A, lista de primitivas y parámetros permitidos.|§1 delimita AES-256, noDF, incremento128, tamaños y referencia exacta90A; no se pretende cubrir variantes cambiando solo el nombre de la primitiva.|
|1013–1021|9-tupla, estado persistente/temporal, f/g, transición y salida.|§3 conserva la formulación CTR del antecedente BSI. Tipos y dominios se comprueban contra los procedimientos NIST.|
|1022–1033|4-tuplas, preparación de seed material, función derivada, seeding y reseeding.|§3 define las dos4-tuplas noDF y el tratamiento de personalización/auxiliares; no importa la construcción Hash_df.|
|1034–1039|Paso a la prueba; longitud/truncamiento; secuencia observada y objetivos temporales; identidad de transición; anuncia hipótesis.|§2 define cada propiedad y la información;§3 eq:output da truncamiento;§4.1 eq:request-sequence/eq:revealed-triple da la identidad que relaciona salida y estado.|
|1040–1046|Hipótesis sobre primitiva y funciones relacionadas, con justificaciones.|Asunción AES y sec:primitive-assessment; conteos derivados, dependencia retenida y evidencia/hipótesis criptográficas explícitas. Es una parte del patrón completo.|
|1047|Fija longitudes de las funciones derivadas.|§1 y§3 fijan bloque128, clave256, estado secreto384, g de384 bits y Update de tres bloques. f aquí devuelve un par; no se importan los tipos de las funciones Hash.|
|1048–1052|Problema más favorable al adversario y justificación de la reducción.|Se conceden bloques completos salvo bits objetivo y estado terminal; el controlador no recibe los bits ocultos. No se amplían peticiones artificialmente, porque a diferencia de Hash la transición CTR sí depende de su longitud.|
|1053–1063|Forward secrecy: casos de objetivo y coincidencias; presupuesto de vida; estimación.|§4.1 compone grupos y consultas durante todo el intervalo;§4.2 identifica sucesor dentro/entre peticiones y aplica la cota global de predicción.|
|1064|Backward secrecy.|§4.3 identifica predecesor dentro/entre peticiones; no reutiliza la clave de la petición siguiente para un bloque anterior.|
|1065–1067|Enhanced backward secrecy, preimagen y protección de salida; referencia214.|§4.4 protege directamente salida anterior con estado terminal conocido; inversión se estudia además. Frontera de compromiso y erasure expresas. Valoración no clásica separada de desigualdades clásicas.|
|1068–1069|Estado efectivo y límite de petición.|§4.5: clave candidata determina contador candidato; AES128/192 no alcanzan246; AES256 tiene256 bits efectivos; p≤2^19.|
|1070–1072|Entrada adicional, funciones criptográficas y tests estadísticos.|§§4.6–4.8: controles públicos adaptativos, inversión de cualquier preimagen, y distancia estadística con presupuesto Qc del controlador.|
|1073|Resumen de los ocho requisitos algorítmicos.|Tabla final enlaza cada requisito con resultados y premisas; no se emite un teorema de conformidad incondicional.|
|1074–1075|Fuente y entropía caso por caso; componentes deterministas no añaden entropía.|§4.9 separa fuente admitida asumida y efecto del seeding demostrado; uniforme384 es más restrictivo que el abanico de ejemplos AIS. Se explicitan proyección efectiva y límites de extensión.|
|1076|Entropía introducida por additional input cuando Hash_DRBG se usa como postprocesado PTG.3; contrasta reseeding.|No se afirma postprocesado PTG.3 ni refresh mediante Generate; a se trata como dato público sin crédito de entropía. Esta diferencia de alcance se declara en la definición DRG.3.8. No es una propiedad requerida para cerrar el perfil DRG.3 seleccionado.|

La diferencia de¶1048–1052 es sustantiva para la estrategia: en Hash extender las peticiones no cambia estados futuros; en CTR modifica el contador del Update final. Nuestra reducción concede más información sobre las peticiones reales, conserva sus longitudes y usa un máximo uniforme4096 solo en las desigualdades. El argumento no depende de ejecutar peticiones ficticias más largas.

## Qué nivel de prueba proporciona realmente el ejemplo AIS

Los autores no deducen seguridad incondicional de una primitiva concreta. Separan la descripción del algoritmo, las hipótesis criptográficas justificadas, los argumentos probabilísticos y la conclusión de cada propiedad. Su razonamiento admite modelos ideales y algunas hipótesis adicionales sobre funciones derivadas. Por tanto, el criterio comparable para CTR_DRBG es justificar explícitamente cada paso dentro de sus premisas y separar la valoración criptográfica de la deducción matemática. No basta invocar que AES es una primitiva reconocida. Tampoco procede exigir una formalización adicional que el ejemplo no aplica.

| Punto revisado | Hash_DRBG en AIS | CTR_DRBG en este manuscrito | Resultado de la comparación |
|---|---|---|---|
| Algoritmo y tuplas |¶1013–1033 especifican9-tupla y4-tuplas. |§3 mantiene f,g,Sreq=S y phiA/phiB del antecedente BSI, con dominios y guardas explícitos. | Mismo tipo de descripción formal; su ejecución se contrasta con Generate. |
| Hipótesis de primitiva |¶1040 asume resistencia a preimagen y modelización de Hash como aplicación aleatoria. | Asunción de familia AES de permutaciones independientes por clave; una clave repetida reutiliza su tabla. | Ambas son hipótesis ideales declaradas. No son hechos demostrados sobre las primitivas concretas ni hipótesis lógicamente idénticas. |
| Funciones derivadas |¶1041–1044 justifican hipótesis para prefijos, restricciones, f y Hash_df. | Las leyes de ternas, XOR y marginales se derivan por conteo; Update no se sustituye por una función aleatoria independiente. | La dependencia entre salidas y claves siguientes se conserva. No se asume directamente la propiedad DRG.3 que se quiere concluir. |
| Entradas relacionadas |¶1045,ecuación5.65, introduce una hipótesis expresamente no estándar sobre hasta2^60 valores de Hash en entradas con diferencias conocidas; la justifica mediante el modelo aleatorio. | La composición se analiza mediante tablas parciales compartidas, intersecciones y un acoplamiento secuencial. | Se hace explícito el mecanismo que conecta evaluaciones relacionadas con los resultados de predicción. |
| Simplificación del adversario |¶1048–1052 proporciona bloques completos y diferencias de preimágenes para fortalecer el problema. | Se revelan los bits no objetivo, los controles y el estado terminal, respetando que el controlador no observe los bits ocultos. | Hay que justificar que la información aumenta y que no se introduce una filtración del objetivo por la aplicación. El texto lo especifica. |
| Forward secrecy |¶1053–1063 separa preimágenes nuevas de coincidencias y calcula la probabilidad de estas últimas bajo sus hipótesis. | Se identifica el sucesor dentro o entre peticiones y se aplica la proposición de predicción con la pérdida de composición. | Se conserva la separación entre identidad del objetivo, hipótesis y estimación de probabilidad. |
| Backward secrecy |¶1064 usa el razonamiento análogo para el predecesor. | Se identifica expresamente la clave y posición del predecesor y se aplica la misma proposición. | No se confunde el predecesor con una inversión bajo la clave de la petición siguiente. |
| Compromiso del estado |¶1065–1067 reduce el estado conocido a invertir una función derivada; aplica la hipótesis5.66 y argumenta protección de las salidas. | La proposición incluye el estado final como información del observador y protege directamente salida anterior; la inversión se analiza aparte. | La protección de salida no se sustituye por recuperar o no recuperar una clave. Se fija la frontera de compromiso. |
| Entrada adicional |¶1070 argumenta desde el estado desconocido y las funciones derivadas de Hash. | Se prueban leyes uniformes sobre g(a), se incluyen ambos Update con el mismo input y se permite control público adaptativo. | El alcance adaptativo utilizado está escrito y conectado al acoplamiento; el XOR aislado no se toma como prueba de toda la composición. |
| Unidireccionalidad |¶1046 y1066 justifican/aplican una hipótesis sobre v+b+g(v+b);¶1071 remite al carácter criptográfico de las funciones. | La alineación inversa cuenta cualquier estado de trabajo compatible; se verifica el candidato anterior completo antes de transferir el evento mediante el acoplamiento. | La tarea de inversión tiene entrada y longitud reales fijadas y admite cualquier preimagen; no se restringe artificialmente a la original. |
| Estadística |¶1072 relaciona fallos de tests adecuados con debilidades de Hash; no da una distancia estadística explícita. | Se deriva una distancia finita incluyendo las computaciones del controlador Qc. | La cota adicional es un resultado del modelo, no una nueva obligación que se impone al ejemplo AIS. No se convierte en fuerza de predicción. |
| Fuente e inicialización |¶1074–1075 separa la fuente y usa hipótesis/estimaciones de entropía caso por caso. | Fuente admisible y uniforme384 condicionada son premisas; el efecto del seeding sin DF se obtiene por traducción y proyección. | La uniformidad es una restricción explícita. No se afirma cubrir toda distribución que solo satisfaga un mínimo de entropía. |

## Diferencias que deben declararse, no ocultarse

AIS usa en¶1060 y¶1063 hipótesis de uniformidad aproximada, independencia aproximada y una aproximación continua para su estimación de coincidencias. El manuscrito CTR_DRBG usa conteos finitos y desigualdades exactas en el modelo declarado; los números se verifican con enteros y fracciones. Eso no hace que el AES concreto se convierta en una permutación aleatoria, ni demuestra por enumeración el acoplamiento general. El argumento escrito y sus condicionamientos siguen siendo necesarios.

El ejemplo Hash usa una aplicación aleatoria para Hash; CTR usa una familia de permutaciones. No podemos importar literalmente sus hipótesis ni llamar indistintamente aleatoria a la función Update: las ternas en contadores vecinos comparten evaluaciones. Se requiere el argumento propio sobre claves derivadas y tablas compartidas.

Las condiciones de entropía inicial tampoco se trasladan entre construcciones. La traducción sin DF preserva la distribución conjunta, pero la clave es una proyección. Las cotas368/378 son suficientes para ciertos objetivos de entropía inicial y no extienden el resultado de composición demostrado para uniforme384. La extensión DF es una cuestión adicional, no una condición necesaria para analizar el perfil sin DF seleccionado.

## AIS214: corrección del baremo de comparación

En¶1009–1076 no aparece un teorema separado de consultas cuánticas, una reducción QROM ni una prueba adaptativa cuántica completa.¶1067 concluye enhanced backward secrecy a partir de hipótesis criptográficas y remite a¶214. Por tanto, exigir un teorema cuántico completo como condición indispensable para que CTR_DRBG alcance el nivel expositivo y de justificación del ejemplo AIS impondría un baremo adicional. Esa exigencia no se mantiene en esta revisión.

Esto tampoco transforma una cota clásica en una prueba contra cálculos cuánticos. En CTR_DRBG sigue siendo necesario justificar la valoración criptográfica adicional requerida por¶214, del mismo modo que el ejemplo AIS utiliza hipótesis justificadas de resistencia criptográfica. El manuscrito identifica esa obligación sin convertirla ni en un contraejemplo al algoritmo ni en un corolario automático del conteo clásico.

## Procedencia de las tuplas y modificaciones examinadas

El antecedente es Müller, *Analysis of Random Number Generation in Browsers*, versión2.0, secciones3.2.4 y4.2.4. Su utilidad aquí es la formulación y el argumento de plausibilidad de CTR_DRBG; las comparativas de productos no forman parte del artículo.

- Se conserva la estructura9-tupla, Sreq=S, f,g,phiA,phiB,phi_req,phi0 ypsi. El procesamiento sin DF utiliza la variante con padding que ya aparece en el antecedente.
- El perfil NIST analizado fija el incremento completo de128 bits. Esta decisión aparece antes de las pruebas; la aritmética modular de los intervalos depende de ella. No se generaliza por conservar los mismos símbolos.
- El estado agotadoR+1 y la saturación dan una extensión total sobre el estado finito; la guarda prohíbe generar cuando se ha agotado el intervalo. Esta precisión no altera una petición admitida.
- La proyección al par secreto se usa únicamente en los cálculos probabilísticos. El contador público continúa en la tupla y no recibe crédito de entropía.
- g(a) es la única notación para la entrada procesada. La antigua igualdad d(a)=g(a) se ha eliminado; pad yPi_i distinguen padding y permutaciones auxiliares.

## Criterio de cierre de esta revisión

Se pide que cada propiedad tenga objetivo, información disponible, hipótesis, resultado y conclusión. Se comprueban por separado fidelidad a la90A, dominios, índices, condicionamientos, composición y alcance de las afirmaciones. La revisión no se da por cerrada solo por adoptar el estilo tipográfico del AIS ni por pasar los verificadores.

El resultado pretendido es un argumento condicional con un nivel de explicitud comparable al ejemplo Hash_DRBG y mayor detalle cuantitativo en algunos pasos. La conclusión de conformidad integral sigue dependiendo de las premisas y valoraciones identificadas; no se declara probada por analogía. Los dictámenes independientes y las comprobaciones de la iteración final se incorporan a REVIEW.md. Una revisión de agentes no equivale a aceptación editorial ni a aprobación del AIS.

## Ciclo de revisión contra objeciones concretas, 25 de octubre de 2026

El ciclo usa criterios verificables: fidelidad del algoritmo, hipótesis de primitiva no circulares, condicionamientos, composición con claves compartidas, protección de salida tras compromiso, inversión de cualquier preimagen, trazabilidad normativa y conclusión dentro del alcance demostrado. Tras corregir una objeción se vuelve a revisar el argumento afectado. La ausencia de objeciones de estos revisores no se identifica con la aprobación futura de los autores del AIS.

| Ronda | Objeto y objeción | Cambio o comprobación | Segunda revisión |
|---|---|---|---|
| 1 | Reorganización expositiva y nomenclatura: había comparación de productos y aliases redundantes. | Cinco secciones; formulación f/g como tupla principal; g(a) única entrada procesada; pad/Pi distintos; fuente y perfil antes del conteo. | Revisión normativa y crítica de las correspondencias; la ejecución f/g se contrasta con Generate en133120 casos reducidos. |
| 2 | Un reemplazo de índices había convertido siete sigma_i en sigma_y(i). | Restaurado sigma_i para estados de grupo; y(i) solo enlaza la entrada de la petición. | Comprobación explícita de índices y relectura independiente del argumento. |
| 3 | Una cota de entropía de clave DF no basta para aplicar una prueba que usa la distribución conjunta inicial. | El apartado DF exige también justificar la ley conjunta de clave/contador. | La limitación queda expresada sin afirmar fallo de DF. |
| 4 | Auditoría nueva, sin contexto previo, de factorización, máscaras adaptativas, colisiones, acoplamiento y objetivo terminal. | Se revisaron los condicionamientos y la ley marginal secuencial; no apareció un contraejemplo ni un paso sin justificar bajo las premisas escritas. | El revisor probabilístico no identificó una objeción bloqueante. La enumeración reducida apoya pasos locales y no sustituye la demostración. |
| 5 | Auditoría nueva de alineación inversa, parada adaptativa y transferencia del evento de inversión. | Se comprobaron cualquier preimagen, factor Gamma multiplicativo, tablas completas solo en el experimento privado y tres/seis evaluaciones de verificación. | El revisor de inversión no identificó una objeción bloqueante bajo las hipótesis declaradas. |
| 6 | Comparación nueva con AIS1040–1046: declarar el modelo AES y posponer toda su valoración era menos que la justificación del ejemplo Hash. | Añadido sec:primitive-assessment: evidencia biclique; modelo de acceso related-key y su diferencia con la interfaz; hipótesis explícita sobre uso de claves derivadas; referencia genérica Grover con límites. Tres originales conservados con hashes. | El revisor de calibración consideró corregida la mera remisión y comparable el tipo de justificación, sin circularidad ni necesidad de imponer un teorema cuántico ajeno al baremo AIS. |
| 7 | Dos precisiones: ausencia de todo atajo sería demasiado fuerte; evidencia selectiva no equivale a valoración criptográfica exhaustiva. | Se habla de evidencia y acceso como fundamento de la idealización, y de ataques que hacen viable la recuperación, no de prohibir todo atajo. | El revisor probabilístico no encontró extrapolación clásica/cuántica ni transferencia concreta presentada como teorema. |

### Resultado y límites de la comparación

No queda una objeción matemática bloqueante identificada por las revisiones independientes para el perfil escrito: AES-256 sin DF, incremento completo, fuente fresca uniforme384 condicionada y modelo de permutaciones compartidas por clave. Cada propiedad tiene definición, mapas, resultados y conclusión. La justificación criptográfica tiene ahora el mismo carácter condicional que las hipótesis justificadas del ejemplo Hash; no se ha elevado una valoración a teorema ni se ha supuesto directamente la seguridad del DRBG.

Sigue siendo una hipótesis la adecuación de AES concreto en este uso con claves secretas derivadas. La referencia Grover no demuestra una cota inferior universal; el manuscrito no ofrece una reducción de todo ataque contra el generador a recuperación de una clave AES ni un teorema de composición cuántica. Esas afirmaciones más fuertes no se atribuyen tampoco al ejemplo AIS. La extensión DF y fuentes menos restrictivas que uniforme384 requieren trabajo adicional. No se ha encontrado un contraejemplo al perfil probado; los ejemplos negativos del artículo refutan inferencias de entropía insuficientes o fronteras de compromiso distintas.

Este cierre describe el estado del argumento y de la revisión, no asegura que los autores del AIS no formulen nuevas objeciones. La revisión humana criptográfica y normativa sigue siendo el siguiente contraste externo.

### Corrección del alcance del baremo por indicación del autor

La calibración previa se describía como1013–1075 y la última discusión se concentró en1040–1046. El autor precisó que el patrón es toda§5.3.1. Se corrigieron los límites a1009–1076 y se añadió el inventario exhaustivo anterior; se revisaron expresamente1034–1039,1047,1073 y1076. Esta comprobación no se reduce a comparar modelos de primitiva. La diferencia de longitud de transición y la no pretensión de refresh/PTG.3 quedan expresas.

La auditoría normativa independiente y la revisión de calibración volvieron a comprobar toda la cobertura1009–1076 tras la corrección. No identificaron una nueva objeción sustantiva para el perfil declarado. El contenido de1047 se comprobó visualmente en el original; no se confunden sus funciones Hash con las funciones f/g de la tupla CTR. Esta ampliación exige correspondencias y delimitación de alcance, no modifica por sí misma las desigualdades.
