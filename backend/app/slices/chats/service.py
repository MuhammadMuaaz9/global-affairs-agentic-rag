from typing import List, Dict, Any
from backend.graph import get_all_thread_ids, get_full_conversation


async def list_user_chats(user_id: str) -> List[Dict[str, Any]]:
    chats = await get_all_thread_ids(user_id)
    return chats[::-1]


async def get_thread_history(thread_id: str) -> List[Dict[str, Any]]:
    messages = await get_full_conversation(thread_id)
    # print(messages)
    
    # Ensure dict structure for schema compatibility
    print("Current thread_id: ---->", thread_id)
    normalized: List[Dict[str, Any]] = []
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role") or msg.get("type") or "user"
            content = msg.get("content", "")
        else:
            role = getattr(msg, "type", "user")
            content = getattr(msg, "content", "")
        normalized.append({"role": role, "content": content})
    return normalized


