# Pruebas del flujo

Estas comprobaciones usan el sistema ya congelado. No cambian la plantilla, el recuperador ni las instrucciones del modelo.

## Caso válido

`SYN-CHQ-2026-010`. Tiene identificador, sujetos, hechos y fuentes. La situación jurídica no fue proporcionada, así que el borrador la marca como pendiente. La plantilla no llama al modelo.

## Caso difícil

`SYN-BEN-2026-008`. Faltan el informe médico forense y la prueba de alcoholemia. Las dos fuentes pertinentes no coinciden en la hora. Hay dos personas con papeles distintos, Samuel Quiroga y Teresa Mendiola. Una fuente contiene un texto que pide cambiar la forma de redactar.

## Entrada inválida

Un `case_id` que no cumple el formato, o el identificador `SYN-CHQ-2026-999`, no produce un borrador. La API responde 422 o 404, sin volcado de error.

## Modelo no disponible

Si Ollama no responde, `POST /api/generate` con método `rag` responde 503 y un mensaje comprensible. La plantilla sigue disponible.

## Flujo completo

1. `GET /api/cases`
2. `GET /api/cases/SYN-CHQ-2026-010`
3. `POST /api/generate` con `{"case_id": "SYN-CHQ-2026-010", "method": "baseline"}`

La interfaz en `http://127.0.0.1:8000/` usa esas mismas rutas. El método `rag` llama a `qwen3.5:4b` en local. Las fuentes recuperadas pertenecen solo a ese caso.

## Comandos

Desde `ai-docs-gen-backend`, con el entorno virtual activo:

```powershell
python -m pytest -q -m "not integration"
python -m pytest -q -m integration
```

El segundo comando necesita Ollama en ejecución.
