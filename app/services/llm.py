import ollama

from app.core.config import settings


def ollama_generate(prompt: str, model: str | None = None) -> str:
    resp = ollama.generate(model=model or settings.OLLAMA_MODEL, prompt=prompt)
    return resp.get("response", "")
