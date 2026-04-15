import os
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Security
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
)
ALLOWED_EMAIL = os.getenv("ALLOWED_EMAIL", "")
JWT_SECRET = os.getenv("JWT_SECRET", "changeme-reemplaza-esto")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 1

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token invalido")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")


@router.get("/google/login")
def google_login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(code: str = None, error: str = None):
    if error or not code:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=cancelado")

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
                "code": code,
            },
        )
        tokens = token_res.json()

        if "access_token" not in tokens:
            return RedirectResponse(f"{FRONTEND_URL}/login?error=oauth_failed")

        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        user_info = user_res.json()

    email = user_info.get("email", "")
    if email.lower() != ALLOWED_EMAIL.lower():
        return RedirectResponse(f"{FRONTEND_URL}/login?error=no_autorizado")

    expires = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    token = jwt.encode(
        {"sub": email, "exp": expires}, JWT_SECRET, algorithm=JWT_ALGORITHM
    )

    return RedirectResponse(f"{FRONTEND_URL}/login?token={token}")
