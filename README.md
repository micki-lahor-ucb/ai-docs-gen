# Informe breve de antecedentes

Prototipo local para redactar un borrador de informe breve de antecedentes a partir de un caso sintético y de sus documentos de respaldo. El resultado no es un documento oficial y requiere revisión humana.

Los datos son ficticios. No hay expedientes reales ni conexión con un sistema institucional.

## Alcance

El sistema permite elegir un caso, revisar sus campos y generar un borrador por uno de dos métodos:

- una plantilla que copia los campos y pega los extractos;
- una redacción del modelo local `qwen3.5:4b`.

No incluye acceso institucional, firma, envío de documentos ni ajuste de los pesos del modelo.

## Arquitectura

```text
Navegador (ai-docs-gen-frontend)
        |
        v
FastAPI (ai-docs-gen-backend)
        |
        +-- plantilla determinista
        |
        +-- TF-IDF, solo con las fuentes de ese caso
                    |
                    +-- como máximo 3 extractos
                                |
                                +-- Ollama, qwen3.5:4b
```

La interfaz y la API comparten el mismo servidor. Los documentos de otro caso no entran en la recuperación.

## Requisitos

- Windows
- Python 3.12
- Git
- Ollama
- el modelo `qwen3.5:4b`

Las versiones de Python usadas por este prototipo están fijadas en `ai-docs-gen-backend/requirements.txt`.

## Instalación

Desde `ai-docs-gen-backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull qwen3.5:4b
```

Si la activación del entorno está bloqueada en esa ventana:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Dataset

Los textos fuente ya están en `ai-docs-gen-backend/data/synthetic/`. El script valida esos archivos y escribe los casos, las claves y la partición. La semilla 42 fija esa partición. No vuelve a redactar los textos, porque ya están guardados.

```powershell
python scripts/build_dataset.py
```

La descripción del corpus está en `docs/dataset_card.md`.

## Reproducir la comparación

La plantilla de desarrollo se vuelve a generar con:

```powershell
python scripts/evaluate_baseline.py
```

La prueba oficial ya está generada. No hace falta volver a llamarla. Las tasas se recalculan desde las etiquetas guardadas:

```powershell
python scripts/evaluate_system.py
```

## Ejecutar el sistema

Desde `ai-docs-gen-backend`:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Abrir `http://127.0.0.1:8000/`. La documentación de la API queda en `http://127.0.0.1:8000/docs`.

## Pruebas

```powershell
python -m pytest -q -m "not integration"
python -m pytest -q -m integration
```

El segundo comando llama al modelo local. Los demás tests no lo hacen. El caso válido, el caso difícil y la entrada inválida están descritos en `reports/pruebas_flujo.md`.

## Artefactos

| Ruta | Contenido |
|---|---|
| `docs/protocolo_experimental.md` | Qué se mide y cómo se acepta un borrador |
| `docs/model_card.md` | Modelo, configuración y límites |
| `docs/dataset_card.md` | Origen, tamaño y semilla del corpus |
| `reports/results.md` | Tabla de la prueba: 5/8 la plantilla y 3/8 la redacción |
| `reports/evaluation.csv` | Etiquetas unidas al método, después de puntuar |
| `reports/data_diagnostics.md` | Conteos y partición |
| `reports/pruebas_flujo.md` | Caso válido, caso difícil y entrada inválida |
| `reports/baseline_dev/` | Borradores de la plantilla en desarrollo |
| `reports/rag_dev/` | Borradores del modelo en desarrollo |
| `reports/test_raw/` | Borradores oficiales de la prueba, con el método visible |
| `reports/blind_review/` | Los mismos borradores en orden mezclado y la rúbrica |

`reports/test_raw/blind_key.json` indica qué método produjo cada borrador. No hace falta abrirlo para ejecutar el sistema.

## Requisitos cubiertos

| Requisito | Evidencia |
|---|---|
| Dataset sintético, con origen, tamaño y limitaciones | `docs/dataset_card.md`, `data/synthetic/` |
| Código que construye la partición y semilla | `scripts/build_dataset.py`, semilla 42 |
| Modelo preentrenado, con versión y configuración | `docs/model_card.md` |
| Línea base en los mismos casos | `src/baseline/template_generator.py`, `reports/results.md` |
| Métrica, validación y análisis de errores | `docs/protocolo_experimental.md`, `reports/results.md` |
| API que ejecuta el modelo real | `backend/main.py` |
| Interfaz para cargar datos y ver el resultado | `ai-docs-gen-frontend/` |
| Caso válido, difícil, inválido y flujo completo | `reports/pruebas_flujo.md`, `tests/` |

## Límites

`qwen3.5:4b` es un modelo preentrenado. Este prototipo no ajusta sus pesos. Puede omitir un hecho, citar mal o seguir una orden escrita dentro de un documento. Una cita con identificador no demuestra, por sí sola, que la fuente respalde la frase.

La comparación usa ocho casos y una sola persona evaluadora. Los intervalos de la tabla se solapan: no declaran un ganador. ROUGE-L no mide veracidad.

El informe en PDF y la presentación todavía no están en este repositorio.
