import logging
import ollama
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Gemini Client
gemini_client = None
if settings.GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini client: {e}")

from google.genai import types

# ... (existing code)

def _generate_gemini(prompt: str, model: str | None = None, files: list[dict] | None = None) -> str:
    if not gemini_client:
        logger.error("Gemini client not initialized. Check GEMINI_API_KEY.")
        return ""
    
    try:
        model_name = model or settings.GEMINI_MODEL
        
        contents = [types.Part.from_text(text=prompt)]
        
        if files:
            for f in files:
                contents.append(
                    types.Part.from_bytes(data=f["data"], mime_type=f["mime_type"])
                )

        response = gemini_client.models.generate_content(
            model=model_name,
            contents=types.Content(parts=contents)
        )
        return response.text
    except Exception as e:
        logger.error(f"Error generating text with Gemini: {e}")
        return ""

def _generate_ollama(prompt: str, model: str | None = None, format: str | None = None, files: list[dict] | None = None) -> str:
    if files:
        logger.warning("Ollama provider does not currently support file attachments. Files ignored.")
    try:
        model_name = model or settings.OLLAMA_MODEL
        # Ensure format is passed only if needed, though updated logic mainly used text
        resp = ollama.generate(model=model_name, prompt=prompt, format=format)
        return resp.get("response", "")
    except Exception as e:
        logger.error(f"Error generating text with Ollama: {e}")
        return ""

def generate_text(prompt: str, model: str | None = None, files: list[dict] | None = None) -> str:
    """
    Generates text using the configured LLM provider (Gemini or Ollama).
    Args:
        prompt: The text prompt.
        model: Optional model override.
        files: Optional list of dicts with 'data' (bytes) and 'mime_type' (str).
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "gemini":
        return _generate_gemini(prompt, model, files)
    elif provider == "ollama":
        return _generate_ollama(prompt, model, files=files)
    else:
        logger.warning(f"Unknown LLM_PROVIDER '{provider}'. Falling back to Gemini.")
        return _generate_gemini(prompt, model, files)
