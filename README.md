# Informe breve de antecedentes

Prototipo local para redactar un borrador de informe breve de antecedentes a partir de un caso sintético y de sus documentos de respaldo. El resultado no es un documento oficial y requiere revisión humana.

Los datos son ficticios. No hay expedientes reales ni conexión con un sistema institucional.

## Qué hace

La misma aplicación ofrece dos métodos sobre las mismas fuentes recuperadas:

- una plantilla que copia los campos y pega los extractos;
- una redacción del modelo local `qwen3.5:4b`.

El recuperador elige como máximo tres documentos del caso. No mezcla expedientes.

## Requisitos

- Windows
- Python 3.12
- Git
- Ollama
- el modelo `qwen3.5:4b`

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

Los textos fuente ya están en `ai-docs-gen-backend/data/synthetic/`. La semilla 42 arma la partición y no vuelve a redactar esos textos.

```powershell
python scripts/build_dataset.py
```

## Plantilla y pruebas

```powershell
python scripts/evaluate_baseline.py
python -m pytest -q -m "not integration"
python -m pytest -q -m integration
```

`pytest -m integration` llama al modelo local. Los demás tests no lo hacen.

Los casos usados para demostrar el flujo están descritos en `reports/pruebas_flujo.md`. Los resultados de la prueba reservada están en `reports/results.md`.

## Ejecutar el sistema

Desde `ai-docs-gen-backend`:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Abrir `http://127.0.0.1:8000/`. La documentación de la API queda en `http://127.0.0.1:8000/docs`.

## Límites

`qwen3.5:4b` es un modelo preentrenado. Este prototipo no ajusta sus pesos. Puede omitir un hecho, citar mal o seguir una orden escrita dentro de un documento. Una cita con identificador no demuestra, por sí sola, que la fuente respalde la frase. La comparación con la plantilla usa ocho casos y es exploratoria.
