from pydantic import BaseModel
from typing import Optional


class SessionRequest(BaseModel):
    id_token: str


class SessionResponse(BaseModel):
    user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str


