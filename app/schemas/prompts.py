from pydantic import BaseModel

class PromptRequest(BaseModel):
    level: str
    subject: str
    q_number: str
    user_message: str
    history: str