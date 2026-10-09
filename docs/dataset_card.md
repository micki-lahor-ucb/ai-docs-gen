# Ficha del dataset

**Fecha:** 9 de octubre de 2026  
**Estado:** construido y partido antes de generar borradores de la prueba

## Origen

Los casos y las fuentes son sintéticos. Fueron elaborados para este prototipo y revisados por el autor. No corresponden a expedientes, personas ni identificadores reales.

Cada archivo de fuente lleva la etiqueta «DOCUMENTO SINTÉTICO PARA EVALUACIÓN ACADÉMICA — NO CORRESPONDE A UN CASO REAL».

## Tamaño y campos

| Elemento | Cantidad |
|---|---:|
| Casos | 24 |
| Fuentes | 121 |
| Palabras aproximadas en las fuentes | 14191 |
| Desarrollo | 16 |
| Prueba | 8 |

Cada caso tiene de 5 a 6 fuentes. Unas 2 son pertinentes para el informe. El resto son distractores del mismo expediente: repiten palabras del asunto, pero corresponden a otra persona, otra fecha u otro lugar.

Campos del caso: `case_id`, `cud`, `department`, `report_date`, `subjects` (nombre, tipo y número de documento, rol), `legal_status`, `objective`, `facts`, `missing_fields`, `contradictions` y `source_ids`.

La clave de evaluación, guardada aparte, indica las fuentes pertinentes, los hechos exigidos y los hechos que solo aparecen en el cuerpo de una fuente.

## Construcción y semilla

`scripts/build_dataset.py` lee los lotes revisados y los Markdown de `data/synthetic/`. Valida identificadores, el número de fuentes, la etiqueta de sintético y que un hecho exclusivo no esté copiado en los campos estructurados. Escribe `cases.jsonl`, `gold_labels.jsonl`, `splits.json` y `manifest.json`.

`SEED=42` fija esa construcción y la partición por caso completo. No regenera los textos fuente, porque esos archivos ya están versionados. Volver a ejecutar el script con los mismos archivos produce la misma partición.

La prueba quedó identificada en `splits.json` y no se usa para ajustar la plantilla ni la recuperación.

## Dificultad

Un caso puede tener más de una etiqueta.

| Etiqueta | Desarrollo | Prueba |
|---|---:|---:|
| Contradicción entre fuentes pertinentes | 6 | 2 |
| Campos faltantes | 6 | 4 |
| Texto dentro de una fuente que intenta cambiar la redacción | 4 | 4 |

La prueba no está formada solo por casos simples. El detalle por caso está en `reports/data_diagnostics.md`.

## Criterios de exclusión

No entran expedientes reales, nombres presentados como reales, ni identificadores institucionales auténticos. Tampoco entran normas inventadas y presentadas como legislación vigente. Se rechaza un caso con menos de 5 o más de 6 fuentes, un identificador repetido, una fuente sin etiqueta de sintético o un hecho exclusivo que ya esté escrito en los campos estructurados.

## Limitaciones

- No representan expedientes reales y pueden diferir de documentos institucionales.
- El volumen es reducido. Con 8 casos de prueba el resultado es exploratorio.
- Una sola persona revisó los textos.
- La semilla no vuelve a redactar las fuentes.
- El rol de una persona y su situación jurídica son datos distintos. La situación jurídica solo se conserva cuando una fuente la dice de forma expresa.
