import logging
from typing import Any
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)

def parse_llm_json(raw: str) -> dict[str, Any]:
    """
    Parses JSON from an LLM response using LangChain's robust parser.
    """
    try:
        parser = JsonOutputParser()
        # JsonOutputParser handles markdown blocks and common issues automatically
        return parser.parse(raw)
    except Exception as e:
        logger.warning("LangChain parser failed: %s. Raw input sample: %s", e, raw[:100])
        # Fallback: simpler aggressive check or return empty
        return {}
