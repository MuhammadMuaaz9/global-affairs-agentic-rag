from fastapi import APIRouter, Depends
from .schemas import SessionRequest, SessionResponse, ErrorResponse
from .dependencies import get_current_user
from .service import verify_id_token, get_user_info_from_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/session", response_model=SessionResponse, responses={401: {"model": ErrorResponse}})
async def create_session(payload: SessionRequest) -> SessionResponse:
    decoded = verify_id_token(payload.id_token)
    info = get_user_info_from_token(decoded)
    return SessionResponse(**info)


@router.get("/me", response_model=SessionResponse, responses={401: {"model": ErrorResponse}})
async def me(user = Depends(get_current_user)) -> SessionResponse:
    return SessionResponse(**user)


