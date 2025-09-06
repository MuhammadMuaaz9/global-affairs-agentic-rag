from fastapi import APIRouter, WebSocket
from .service import stream_chat
from ..auth.dependencies import get_current_user
from ..auth.service import verify_id_token


router = APIRouter()


@router.websocket("/ws/{thread_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str, user_id: str):
    await websocket.accept()
    try:
        # Authenticate via query param token or Sec-WebSocket-Protocol/Authorization header
        token = None
        query_params = dict(websocket.query_params)
        if "token" in query_params:
            token = query_params.get("token")
        if not token:
            # Try Authorization header
            auth_header = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
            if auth_header:
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]
        if not token:
            await websocket.close(code=4401)
            return
        try:
            decoded = verify_id_token(token)
            uid = decoded.get("uid") or decoded.get("user_id")
            if not uid or not user_id == uid:
                await websocket.close(code=4403)
                return
        except Exception:
            await websocket.close(code=4401)
            return

        while True:
            data = await websocket.receive_text()
            query = data
            try:
                print("Realtime chat started with thread_id ----> ", thread_id)
                async for event in stream_chat(query, thread_id, 128000):
                    if event["event"] == "on_chat_model_stream":
                        token = event["data"]["chunk"].content
                        if token:
                            await websocket.send_text(token)
            except Exception as exc:
                await websocket.send_text(f"Error: {str(exc)}")
    finally:
        await websocket.close()


