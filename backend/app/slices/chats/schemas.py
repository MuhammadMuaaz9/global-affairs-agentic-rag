from pydantic import BaseModel
from typing import List, Optional


class ChatSummary(BaseModel):
    thread_id: str
    title: str


class ChatsResponse(BaseModel):
    chats: List[ChatSummary]
    error: Optional[str] = None


class Message(BaseModel):
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    messages: List[Message]
    error: Optional[str] = None


