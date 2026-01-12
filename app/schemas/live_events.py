from pydantic import BaseModel
from typing import List

class LiveQueryRequest(BaseModel):
    concept_ids: List[int]
    time_limit: int = 15

class LiveQueryResponse(BaseModel):
    generate_prompt: str
    context_summary: str
