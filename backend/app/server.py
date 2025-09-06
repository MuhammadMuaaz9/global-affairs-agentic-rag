from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Routers will be imported from slices
from .slices.chats.controller import router as chats_router
from .slices.realtime.controller import router as realtime_router
from .slices.auth.controller import router as auth_router
from .slices.auth.service import ensure_firebase
from ..graph import setup_checkpointer, shutdown_checkpointer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ensure_firebase()
    
    try:
        await setup_checkpointer()
    except Exception:
        # If DB not available, continue; routes may handle errors gracefully
        pass
    yield
    
    # Shutdown
    try:
        await shutdown_checkpointer()
    except Exception:
        pass


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    # Static and root endpoints remain for frontend
    app.mount("/static", StaticFiles(directory="./frontend"), name="static")

    @app.get("/")
    async def get_root():
        return FileResponse('./frontend/index.html')

    @app.get("/favicon.ico")
    async def get_favicon():
        return FileResponse('./frontend/favicon.png')

    # Include vertical slice routers
    app.include_router(auth_router, prefix="")
    app.include_router(chats_router, prefix="")
    app.include_router(realtime_router, prefix="")

    return app


