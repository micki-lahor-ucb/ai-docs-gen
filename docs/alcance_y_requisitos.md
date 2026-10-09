# Alcance y requisitos

**Proyecto:** asistente de redacción de un informe breve de antecedentes  
**Fecha:** 9 de octubre de 2026  
**Estado:** alcance fijado antes de construir el dataset y antes de evaluar

## Problema

Preparar un informe breve de antecedentes exige ordenar datos de un caso, revisar documentos de respaldo y producir un borrador coherente. El borrador no debe alterar datos, inventar hechos, completar información desconocida ni atribuir a una fuente un contenido que esa fuente no contiene.

El prototipo trabaja solo con casos ficticios. No está conectado a un sistema institucional ni produce un documento oficial.

## Tipo documental

El único tipo de documento que genera el sistema es un **informe breve de antecedentes**.

El borrador organiza identificación del caso, sujetos, hechos conocidos, documentación revisada y datos pendientes. No es una resolución, no concluye culpabilidad y no sustituye la revisión de quien lo usa.

El rol de una persona (denunciante, denunciado, víctima u otro) y su situación jurídica son datos distintos. La situación jurídica solo se reproduce si el caso y una fuente la dicen de forma expresa. No se deduce del rol.

## Qué hace el prototipo

1. Permite elegir un caso sintético y editar sus campos antes de generar.
2. Valida la entrada y rechaza un caso desconocido o un dato mal formado.
3. Recupera como máximo tres documentos de entre las cinco o seis fuentes de ese caso.
4. Produce dos borradores con la misma evidencia:
   - una plantilla determinista, que copia los campos y pega los extractos sin redactarlos;
   - una redacción del modelo local Qwen3.5:4B, a partir de esos mismos campos y extractos.
5. Muestra el borrador, las fuentes usadas, las advertencias, el método y el tiempo de respuesta.
6. Informa si el modelo local no está disponible, si la entrada es inválida o si la generación tarda demasiado.

## Dentro del alcance

- Dataset sintético, elaborado para este prototipo y revisado por el autor.
- Construcción reproducible del dataset de trabajo a partir de los archivos aprobados.
- Plantilla determinista y redacción con el modelo local.
- Recuperación por similitud de texto, limitada al expediente del caso.
- API que ejecuta el método elegido sobre los datos recibidos.
- Interfaz web en español, servida por la misma API.
- Comparación de ambos métodos sobre un conjunto de prueba reservado.
- Pruebas de un caso válido, un caso difícil, una entrada inválida y el flujo completo.

## Fuera del alcance

- Expedientes, nombres o identificadores reales.
- Conexión con sistemas institucionales, autenticación, firma o envío de documentos.
- Entrenamiento o ajuste de pesos del modelo de lenguaje.
- Base de datos transaccional, base vectorial dedicada o despliegue en contenedores.
- Varios tipos de documento.
- Afirmar que el borrador está libre de errores.

## Requisitos de datos

Cada caso incluye un identificador sintético, un código ficticio, departamento, fecha, sujetos con rol, hechos conocidos, objetivo del informe, campos faltantes, contradicciones si las hay y la lista de fuentes de ese caso.

Cada caso tiene cinco o seis fuentes. Unas dos son pertinentes para el informe. Las demás son irrelevantes, tratan otro asunto del mismo expediente ficticio o usan nombres y fechas parecidos.

La clave de evaluación de cada caso incluye al menos dos hechos que están solo en el cuerpo de una fuente pertinente y no en los campos estructurados.

Los textos de las fuentes quedan guardados en el repositorio. La semilla de construcción no los vuelve a redactar.

## Requisitos de la interfaz y de la API

La interfaz muestra de forma permanente que se trata de un prototipo con datos sintéticos y que el resultado es un borrador para revisión humana.

La API valida tipos y tamaño de los campos, no ejecuta texto del usuario como código y no permite elegir una dirección arbitraria del modelo. Si el formulario envía campos editados, la generación usa esos campos y solo carga fuentes del caso indicado. La evaluación oficial usa los casos congelados, sin esas ediciones.

## Criterio de cierre de esta entrega

El prototipo se considera cerrado cuando una persona puede seguir el README, cargar un caso, obtener un borrador real de la plantilla y otro del modelo local, y consultar la comparación hecha sobre el mismo conjunto de prueba. No es necesario que la redacción supere a la plantilla. Sí es necesario informar el resultado observado y sus límites.
