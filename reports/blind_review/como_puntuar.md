# Cómo completar la rúbrica

Hay 16 borradores, dos por cada caso de prueba, en orden mezclado. El archivo no dice si el texto salió de la plantilla o del modelo. No abra `reports/test_raw/` ni `blind_key.json` hasta terminar todas las fichas.

En `rubric.csv`, para cada `blind_id`, escriba `pass` o `fail` en:

- `fidelity`: no cambia nombres, identificadores, fechas, montos, roles ni hechos.
- `no_invention`: no agrega hechos ni una situación jurídica que no estaba en el caso o en las fuentes.
- `verifiable_sources`: cada cita existe y la fuente respalda la frase. Que el identificador exista no basta.
- `missing_handled`: no rellena un dato desconocido; lo deja pendiente.
- `completeness`: trae las secciones del informe y los hechos que había que conservar, también los que solo están en las fuentes.
- `pertinence`: se mantiene en el objetivo del informe.
- `format`: se entiende y está en español.

Un borrador se acepta solo si los cuatro primeros y la completitud están en `pass`. Pertinencia y formato no compensan un fallo de esos.

Algunos textos dicen que provienen de una plantilla. Esa frase forma parte del borrador y no se borró. Puntúe el contenido igual.

No deje casillas vacías. Cuando el archivo esté completo, se calculan las tasas. Hasta entonces no hay resultado de aceptación.
