from pydantic import BaseModel

class PromptRequest(BaseModel):
    level: int
    subject: str
    q_number: str
    user_message: str