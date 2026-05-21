from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    request_id: str | None = None


class ChatResponse(BaseModel):
    agent: str
    response: str
