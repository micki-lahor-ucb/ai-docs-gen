# Registro de decisiones

**Fecha de cierre de estas decisiones:** 9 de octubre de 2026  
**Regla:** las decisiones de método que afectan la medición no se cambian después de ver los borradores del conjunto de prueba. Un cambio posterior es otro experimento.

## Aplicación

| Decisión | Motivo |
|---|---|
| Python 3.12 para API, recuperación, plantilla y evaluación | Un solo lenguaje alcanza para el prototipo y ya está disponible en el equipo de desarrollo. |
| FastAPI | Validación de entradas, códigos de error claros y una API pequeña. |
| Interfaz en HTML, CSS y JavaScript, servida por la misma API | Evita un segundo servidor. La interfaz y los mensajes visibles van en español. El código y sus comentarios van en inglés. |
| Archivos JSON, JSONL y Markdown en disco | El prototipo no necesita una base de datos. |
| El formulario puede editar campos, pero la evaluación oficial usa los casos congelados | La demostración permite ingresar datos. La medición no usa ediciones hechas a mano sobre el conjunto de prueba. |

## Modelo

| Decisión | Motivo |
|---|---|
| Reutilizar `qwen3.5:4b` mediante Ollama en la máquina local | El modelo ya está descargado. La demostración no depende de un servicio externo. |
| Tratarlo como modelo preentrenado, sin ajuste de pesos | No se entrenan sus parámetros. Se documentan origen, digest, hardware y configuración de inferencia. |
| `think: false`, temperatura 0, semilla 42 y `num_ctx` 4096 | El modelo puede emitir una cadena de razonamiento. Se desactiva para que el borrador sea solo el informe. La temperatura 0 y la semilla reducen la variación entre ejecuciones; no la eliminan por completo en GPU. El contexto por defecto del modelo es muy amplio; 4096 cabe en la memoria de la GPU de 8 GB y alcanza para tres extractos. |
| Tiempo de espera de 180 segundos | Si la generación no termina, la API devuelve un error comprensible y no un volcado de pila. |
| Digest observado al fijar esta decisión: `d8b0f5e9760c`. Ollama 0.40.1. Cuantización Q4_K_M. Familia qwen35, 4.2B parámetros | Queda constancia de la versión usada. Si `ollama list` muestra otro digest al congelar la prueba, se anota el valor real y no se cambia en silencio. |

Una llamada corta del 9 de octubre de 2026, con esa configuración, respondió sin cadena de razonamiento. Casi todo el tiempo se fue en cargar el modelo. Esa llamada no es un resultado del experimento.

## Recuperación y plantilla

| Decisión | Motivo |
|---|---|
| TF-IDF y similitud de coseno, con scikit-learn, ajustado solo con las fuentes del caso consultado | Separa expedientes. Con cinco o seis documentos no hace falta un índice global. |
| Devolver como máximo tres fuentes | Dentro del caso hay documentos irrelevantes. El recorte obliga a elegir. |
| Indexar las fuentes autorizadas del caso no se considera fuga | Esas fuentes son el material que el sistema puede consultar. La fuga sería usar las etiquetas de relevancia, o los resultados de la prueba, para cambiar el recuperador y luego presentar esa misma prueba como independiente. |
| La plantilla y el modelo reciben los mismos tres extractos | La comparación no castiga a la plantilla por no ver documentos que el modelo sí ve. |
| La plantilla copia los campos y pega los extractos sin resumirlos | Es un método simple, determinista y sin modelo de lenguaje. Mide si redactar aporta algo frente a pegar la misma evidencia. |
| No se usa una base vectorial ni un marco de orquestación adicional | Añadirían servicios sin cambiar la pregunta del experimento. |

## Datos y medición

| Decisión | Motivo |
|---|---|
| Solo casos sintéticos, revisados por el autor | El repositorio se puede compartir sin expedientes reales. |
| `SEED=42` para identificadores estables y para la partición | La misma entrada aprobada y la misma semilla producen el mismo dataset de trabajo. La semilla no regenera la prosa de las fuentes, porque esa prosa ya está en los archivos. |
| Partir por caso completo | Fuentes y borradores de un caso quedan en la misma partición. |
| Meta de 24 casos: 16 de desarrollo y 8 de prueba | Alcanza para depurar y para una prueba reservada. Con 8 casos el resultado es exploratorio. |
| Tasa de aceptación como métrica principal | Un borrador útil para este prototipo es fiel y completo. La elegancia no compensa un dato inventado ni un hecho exigido que falta. |
| Un solo evaluador, con método, modelo y latencia ocultos al puntuar | No hay un segundo revisor. Ocultar los metadatos reduce el sesgo. El estilo de la plantilla puede delatarla igual, y eso se declara. |
| ROUGE-L solo como medida exploratoria | La semejanza de texto no demuestra que el borrador sea verdadero. |

## Lo que no se hará en esta entrega

No se ajustan los pesos del modelo, no se cambia a un modelo más grande a mitad del experimento, no se integra un sistema institucional y no se procesan documentos reales.
