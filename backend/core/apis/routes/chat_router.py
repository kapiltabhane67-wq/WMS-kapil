from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.apis.dependencies import current_user
from core.controllers import chat_controller
from core.database.connection import db_connection
from core.schemas import UserContext


router = APIRouter()


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)


@router.post("/v1/chat")
def chat(payload: ChatRequest, user: UserContext = Depends(current_user)):
    """
    AI chatbot endpoint — Admin and Manager only.
    Answers questions about live WMS data (inventory, orders, staff, etc.).
    Never reveals passwords or sensitive credentials.
    """
    with db_connection() as conn:
        return chat_controller.chat(
            conn,
            user,
            payload.message,
            [h.model_dump() for h in payload.history],
        )
