from typing import Optional, Dict, Any
import os

from firebase_admin import auth as fb_auth, credentials, initialize_app, get_app


_firebase_initialized = False


def ensure_firebase() -> None:
    global _firebase_initialized
    if _firebase_initialized:
        return

    # Use env var for firebase service account JSON path
    sa_path = os.getenv("FIREBASE_CREDENTIALS_FILE")
    if not sa_path:
        raise RuntimeError("FIREBASE_CREDENTIALS_FILE environment variable is not set")

    try:
        # Check if Firebase is already initialized
        try:
            get_app()
        except ValueError:
            cred = credentials.Certificate(sa_path)
            initialize_app(cred)

        _firebase_initialized = True
    except Exception as exc:
        raise RuntimeError(f"Failed to initialize Firebase Admin: {exc}")


def verify_id_token(id_token: str) -> Dict[str, Any]:
    ensure_firebase()
    decoded = fb_auth.verify_id_token(id_token)
    return decoded


def get_user_info_from_token(decoded_token: Dict[str, Any]) -> Dict[str, Optional[str]]:
    user_id = decoded_token.get("uid") or decoded_token.get("user_id")
    email = decoded_token.get("email")
    name = decoded_token.get("name") or decoded_token.get("display_name")
    return {"user_id": user_id, "email": email, "display_name": name}


