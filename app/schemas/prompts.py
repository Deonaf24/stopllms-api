from pydantic import BaseModel


class PromptRequest(BaseModel):
    assignment_id: str
    level: str
    subject: str
    user_message: str
    history: str
