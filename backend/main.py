from fastapi import FastAPI,WebSocket
from graph import get_all_thread_ids, get_full_conversation, run_workflow
from pydantic import BaseModel
import traceback
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

class ChatInput(BaseModel):
    messages: list[str]
    thread_id: str


# serve static files
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# serve home page
@app.get("/")
async def get():
    return FileResponse('../frontend/index.html')


@app.get("/favicon.ico")
async def get_favicon():
    return FileResponse('../frontend/favicon.png')


# get all thread_ids of all chats for sidebar
@app.get("/chats/{user_id}")
async def get_all_chats(user_id: str):
    try:
        
        chats = await get_all_thread_ids(user_id)
        reversed_chats = chats[::-1]
        
        # print("Fetched chats:", chats)
        return {"chats": reversed_chats}
    
    except Exception as e:
        return {"error": str(e), "chats": []}
    

# get full chat history for a specific thread_id or chat    
@app.get("/chat/{thread_id}")
async def get_chat_history(thread_id: str):
    try:
        messages = await get_full_conversation(thread_id)
        # print("Fetched messages:", messages)
        return {"messages": messages}
    
    except Exception as e:
        return {"error": str(e), "messages": []}



# WebSocket endpoint for real-time chat
@app.websocket("/ws/{thread_id}/{user_id}")     
async def websocket_endpoint(websocket: WebSocket, thread_id: str, user_id: str):
    print(f"thread_id = {thread_id}, user_id = {user_id}")
    await websocket.accept()
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            query = data
            
            try:
                stream = await run_workflow(query, thread_id, 128000)
                print(stream)
                    
                if stream is None:
                    await websocket.send_text("Error: No stream returned")
                    continue
                    
                async for event in stream:
                    if event["event"] == "on_chat_model_stream":
                        token = event["data"]["chunk"].content
                        print(token)
                        if token:
                            await websocket.send_text(token)        
            
            except Exception as e:
                    
                print(f"Stream error: {e}")
                traceback.print_exc()       # This will show the full error
                await websocket.send_text(f"Error: {str(e)}")
                
    except Exception as e:
         print(f"WebSocket error: {e}")
    finally:
        await websocket.close()    