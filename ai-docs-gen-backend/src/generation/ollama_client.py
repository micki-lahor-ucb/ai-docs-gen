"""HTTP client for the local Ollama chat API."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from src.generation.config import (
    MODEL_NAME,
    NUM_CTX,
    OLLAMA_BASE_URL,
    SEED,
    TEMPERATURE,
    TIMEOUT_SECONDS,
)


class OllamaError(Exception):
    """A model failure with a message that can be shown to a person."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)


@dataclass(frozen=True)
class OllamaReply:
    """Text returned by the local model."""

    content: str
    model: str


class OllamaClient:
    """Call the local chat endpoint. The base URL is fixed."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        timeout_seconds: float = TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout_seconds, transport=transport)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def chat(self, messages: list[dict]) -> OllamaReply:
        """Send one non-streaming chat request."""
        payload = {
            "model": MODEL_NAME,
            "think": False,
            "stream": False,
            "messages": messages,
            "options": {
                "temperature": TEMPERATURE,
                "seed": SEED,
                "num_ctx": NUM_CTX,
            },
        }
        try:
            response = self._client.post("/api/chat", json=payload)
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise OllamaError(
                "La generación superó el tiempo de espera de 180 segundos."
            ) from error
        except httpx.ConnectError as error:
            raise OllamaError(
                "El modelo local no está disponible. Compruebe que Ollama esté en ejecución."
            ) from error
        except httpx.HTTPStatusError as error:
            raise OllamaError(
                f"El modelo local respondió con un error HTTP {error.response.status_code}."
            ) from error
        except httpx.HTTPError as error:
            raise OllamaError("No se pudo completar la llamada al modelo local.") from error

        try:
            body = response.json()
            content = body["message"]["content"]
            model = str(body.get("model") or MODEL_NAME)
        except (KeyError, TypeError, ValueError) as error:
            raise OllamaError("La respuesta del modelo local no tiene el formato esperado.") from error
        if not str(content).strip():
            raise OllamaError("El modelo local devolvió una respuesta vacía.")
        return OllamaReply(content=str(content), model=model)
