import logging
from io import BytesIO
from pypdf import PdfReader

logger = logging.getLogger(__name__)

def extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_bytes(data: bytes, filename: str | None, mime_type: str | None) -> str:
    lowered_name = (filename or "").lower()
    if (mime_type and "pdf" in mime_type) or lowered_name.endswith(".pdf"):
        return extract_text_from_pdf(data)
    
    # We cannot extract text from images without OCR dependencies
    if (mime_type and "image" in mime_type) or lowered_name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        logger.warning("Skipping image file %s as OCR is not available", filename)
        return ""

    return data.decode("utf-8", errors="ignore")
