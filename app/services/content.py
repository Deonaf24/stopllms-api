from typing import List, Dict, Any, Tuple, Optional
from app.models.school import File
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def extract_content_from_files(files: List[File]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extracts text and prepares LLM payloads from a list of File objects.
    Returns:
        combined_text: String containing text extracted from all files.
        file_payloads: List of dictionaries suitable for Gemini/LLM input (binary data).
    """
    from app.services.storage import get_storage_service
    from app.services.analysis import _extract_text_from_bytes

    storage = get_storage_service()
    
    combined_text = ""
    file_payloads = []
    
    for file in files:
        try:
            # We assume file.path is the storage path key
            data = await storage.open_file(file.path)
            
            # Extract text (best effort)
            text = _extract_text_from_bytes(data, file.filename, file.mime_type)
            if text:
                combined_text += f"\n--- File: {file.filename} ---\n{text}\n"
            
            # For Gemini, we can send the raw blob if supported
            if settings.LLM_PROVIDER == "gemini":
                file_payloads.append({"data": data, "mime_type": file.mime_type})
                
        except Exception as e:
            logger.warning(f"Failed to read file {file.id} ({file.filename}): {e}")
            
    return combined_text, file_payloads
