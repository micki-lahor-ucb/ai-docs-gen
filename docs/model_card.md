# Ficha del modelo

**Fecha:** 9 de octubre de 2026  
**Estado:** configuración usada para los borradores de desarrollo. No se ha generado la prueba oficial.

## Origen

El redactor es `qwen3.5:4b`, un modelo preentrenado ejecutado en local con Ollama 0.40.1. No se ajustaron sus pesos y no se entrenó un modelo desde cero.

| Dato | Valor |
|---|---|
| Nombre en Ollama | `qwen3.5:4b` |
| Digest | `d8b0f5e9760c` |
| Familia | qwen35 |
| Parámetros | 4.2B |
| Cuantización | Q4_K_M |
| Sistema | Windows |
| GPU | NVIDIA RTX 2070, 8 GB |
| Contexto máximo del modelo | 262144 tokens |

## Configuración de inferencia

| Parámetro | Valor |
|---|---|
| `think` | false |
| `temperature` | 0 |
| `seed` | 42 |
| `num_ctx` | 4096 |
| `stream` | false |
| Tiempo de espera | 180 segundos |

La temperatura 0 y la semilla reducen la variación entre ejecuciones. No garantizan una repetición idéntica en GPU.

`num_ctx` queda en 4096. Los tres extractos de un caso caben en ese contexto. No se sube a 8192.

## Llamadas realizadas

Una llamada corta del 9 de octubre de 2026, con esta configuración, respondió «listo» y no incluyó una cadena de razonamiento. El reloj marcó 11,2 segundos; la mayor parte fue la carga del modelo.

Después se redactaron los 16 borradores de desarrollo. El modelo informado en cada uno fue `qwen3.5:4b`. La latencia estuvo entre 13 y 24 segundos, con una mediana de unos 18 segundos. No se redactó ningún caso de la prueba.

## Límites

- Un identificador citado solo indica que ese identificador estaba entre las fuentes recuperadas. No demuestra que la fuente respalde la frase.
- Si el borrador cita un identificador que no fue recuperado, la cita se marca como no verificable.
- El modelo puede obedecer una orden escrita dentro de una fuente, aunque la instrucción del sistema pida no hacerlo. En un borrador de desarrollo adoptó el tono que pedía un documento. Eso se evaluará con la rúbrica; no se afirma que el sistema elimine esos errores.
- Si Ollama no responde, se agota el tiempo o la respuesta llega vacía, el resultado es un aviso comprensible y no un volcado de error.
