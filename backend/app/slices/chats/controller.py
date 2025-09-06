from fastapi import APIRouter, Depends, HTTPException, status
from .schemas import ChatsResponse, ChatHistoryResponse, ChatSummary, Message
from .service import list_user_chats, get_thread_history
from ..auth.dependencies import get_current_user


router = APIRouter()


@router.get("/chats/{user_id}", response_model=ChatsResponse)
async def get_all_chats(user_id: str, user = Depends(get_current_user)) -> ChatsResponse:
    if not user_id or not user.get("user_id") or not user_id == user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        chats = await list_user_chats(user_id)
        summaries = [ChatSummary(**c) for c in chats]
        return ChatsResponse(chats=summaries)
    except Exception as exc:
        return ChatsResponse(chats=[], error=str(exc))


@router.get("/chat/{thread_id}", response_model=ChatHistoryResponse)
async def get_chat_history(thread_id: str, user = Depends(get_current_user)) -> ChatHistoryResponse:
    try:
        messages = await get_thread_history(thread_id)
        print(messages)
        return ChatHistoryResponse(messages=[Message(**m) for m in messages])
    except Exception as exc:
        return ChatHistoryResponse(messages=[], error=str(exc))


