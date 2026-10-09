# Protocolo experimental

**Fecha de fijación:** 9 de octubre de 2026  
**Estado:** reglas fijadas el 9 de octubre de 2026, antes de ver los borradores de la prueba.  
**Generación oficial:** 9 de octubre de 2026, con el commit `f4ca646`. No se modificó la plantilla, el recuperador ni las instrucciones después de producir esas salidas.

Las salidas de la prueba se generaron una sola vez. Las reglas de esta página no se reescriben para mejorarlas.

## Pregunta

Para un caso sintético, ¿un borrador redactado por Qwen3.5:4B a partir de los datos estructurados y de tres extractos recuperados resulta aceptable con más, igual o menos frecuencia que una plantilla que pega esos mismos extractos sin redactarlos?

El resultado puede favorecer a la plantilla. Ese desenlace se informa igual.

## Unidad de observación

Una unidad es un borrador de informe breve de antecedentes producido para un `case_id`.

Cada caso del conjunto de prueba aporta dos unidades: el borrador de la plantilla y el borrador de Qwen. Las dos reciben el mismo registro estructurado y los mismos tres extractos.

## Material

Los casos y las fuentes son sintéticos, elaborados para este prototipo y revisados por el autor. No corresponden a expedientes reales.

Cada caso tiene:

- identificador, código ficticio, departamento y fecha;
- sujetos, con nombre ficticio, documento ficticio y rol;
- situación jurídica solo si una fuente la expresa;
- hechos que sí están en los campos estructurados;
- objetivo del informe, campos faltantes y contradicciones;
- cinco o seis fuentes, de las cuales unas dos son pertinentes;
- una clave con los hechos que el informe debe conservar, entre ellos al menos dos que aparecen solo en una fuente pertinente y no en el JSON;
- la lista `relevant_source_ids`.

Al menos un caso de desarrollo y uno de prueba incluyen, dentro de una fuente, un párrafo que pide cambiar las reglas de redacción. Ese párrafo es contenido del documento. No es una instrucción del sistema.

El script de construcción comprueba que cada hecho exclusivo no está en los campos estructurados y sí está en la fuente indicada. Parte los casos completos con `SEED=42`. La semilla no regenera el texto de las fuentes.

### Tamaño y partición previstos

| Conjunto | Casos | Uso |
|---|---:|---|
| Desarrollo | 16, si se llega a 24 | Depurar plantilla, recuperador y redacción |
| Prueba | 8, si se llega a 24 | Medición oficial, una sola vez |

Si solo se revisan 20 casos, la prueba conserva al menos 8 y el resto queda en desarrollo. Si se revisan 30, el reparto pasa a 20 y 10. Esas cifras se anotan cuando el dataset exista. No se mueven casos de una partición a otra después de ver borradores de prueba.

## Sistemas comparados

Los dos usan el mismo recuperador.

1. Se cargan solo las fuentes de ese `case_id`.
2. Se ajusta TF-IDF con esas fuentes y se toman como máximo las tres de mayor similitud de coseno con la consulta formada por el objetivo y los hechos estructurados.
3. No se consultan `relevant_source_ids` para elegir.

**Plantilla.** Copia identificadores, nombres, fechas y hechos del JSON. Pega el texto de los tres extractos, cada uno con su `source_id`, sin resumir. Marca `[PENDIENTE: información no proporcionada]` si falta un campo obligatorio. No llama al modelo.

**Qwen3.5:4B.** Recibe las mismas piezas y redacta el informe en español. La llamada local usa `think: false`, temperatura 0, semilla 42, `num_ctx` 4096 y un tiempo de espera de 180 segundos. El modelo es preentrenado. No se ajustan sus pesos.

## Métrica principal

Tasa de aceptación = borradores aceptables / borradores evaluados.

Un borrador es aceptable solo si aprueba los cuatro criterios críticos y la completitud. Pertinencia y formato no compensan un fallo crítico ni un hecho exigido que no aparece.

Se publican `k/n`, el porcentaje y un intervalo de Wilson del 95 %. Con `k` aceptados en `n` borradores y `z = 1,96`:

- centro = `(k + z²/2) / (n + z²)`
- margen = `z * sqrt( k(n-k)/n + z²/4 ) / (n + z²)`
- intervalo = centro ± margen, recortado al rango de 0 a 1

El intervalo describe la incertidumbre de una proporción pequeña. No se presenta como prueba de una diferencia concluyente entre sistemas.

Junto a la tasa de aceptación se publica la tasa de criterios críticos: borradores con los cuatro críticos aprobados, aunque falle la completitud.

## Rúbrica

Cada criterio se anota como aprobado o reprobado.

| # | Criterio | Papel |
|---|---|---|
| 1 | Fidelidad factual: no cambia nombres, identificadores, fechas, montos, roles ni hechos | Crítico |
| 2 | No invención: no agrega hechos ni una situación jurídica que no fue suministrada | Crítico |
| 3 | Fuentes verificables: cada cita existe en el paquete del caso y respalda la afirmación | Crítico |
| 4 | Faltantes: no rellena un dato desconocido; lo marca como pendiente | Crítico |
| 5 | Completitud: incluye las secciones obligatorias y todos los hechos de la clave, también los que solo están en las fuentes | Exigida para aceptar |
| 6 | Pertinencia: se mantiene en el objetivo del informe | Complementaria |
| 7 | Formato y claridad: estructura legible y español comprensible | Complementaria |

Secciones obligatorias: título, identificación del caso, sujetos procesales, antecedentes conocidos, documentación revisada y observaciones o faltantes.

La existencia de un `source_id` no basta para dar por buena la cita. Quien evalúa comprueba que la fuente respalde la frase.

Si un hecho exclusivo no quedó entre los tres extractos, los dos borradores pueden fallar la completitud por la misma causa. `Recall@3` muestra ese fallo de recuperación aparte.

## Métricas complementarias

- Número de errores críticos por sistema.
- Proporción de citas cuyo `source_id` existe y es pertinente.
- Proporción de hechos exigidos presentes, separados en hechos del JSON y hechos exclusivos de las fuentes.
- Tasas de pertinencia y de formato.
- Latencia en segundos, con la mediana por sistema.
- `Recall@3`: proporción de `relevant_source_ids` que aparecen entre las tres fuentes recuperadas. Se calcula una vez, sobre la prueba, y es el mismo valor para los dos sistemas porque comparten el recuperador.
- Corte por tipo de caso: directo, con distractores y con texto que intenta cambiar las reglas de redacción.
- ROUGE-L entre el borrador y un texto de referencia armado con los hechos de la clave. Es exploratorio. No mide veracidad ni calidad jurídica.

## Quién evalúa

Evalúa una sola persona, la misma que construye el prototipo. No hay acuerdo entre evaluadores y no se informará como si lo hubiera.

Antes de puntuar:

1. Se exportan los borradores de la prueba con un identificador opaco.
2. Se quitan método, nombre del modelo y latencia.
3. El texto del borrador no se modifica.
4. El orden se baraja con `SEED=42`.
5. Se completa la rúbrica.
6. Solo después se une cada ficha con su método.

Ocultar los metadatos no garantiza que el estilo de la plantilla pase desapercibido. El informe lo dirá.

## Congelamiento

Quedan congelados, con fecha y commit, antes de generar los borradores de prueba:

- este protocolo;
- el texto de instrucciones que recibe el modelo;
- la plantilla;
- la configuración del modelo (`think`, temperatura, semilla, `num_ctx`);
- el corpus aprobado;
- `splits.json`.

Reglas:

- Plantilla, recuperador e instrucciones del modelo se ajustan solo con desarrollo.
- Los borradores oficiales de la prueba se generan una sola vez, los dos métodos, el mismo día de congelamiento.
- No se reescribe una instrucción, una plantilla ni el recuperador para mejorar un caso de prueba ya visto.
- Si algo de eso cambia, la corrida anterior deja de ser la evaluación final. La nueva corrida se informa como otra versión.
- No se agregan casos al conjunto de prueba después de ver sus borradores.

## Qué no afirman los números

Ocho casos de prueba, o diez si se llega a treinta, no sostienen una generalización. Un borrador fluido puede ser falso. Un identificador de fuente citado no demuestra, por sí solo, que la fuente diga lo que el borrador afirma. El intervalo de Wilson no declara un ganador.
