"""
utils/auth.py — JWT Authentication
====================================
Provides:
  • create_access_token()  — sign a JWT for a user
  • verify_token()         — decode and validate a JWT
  • get_current_user()     — FastAPI dependency injected into protected routes

Design decisions (beginner-friendly):
  • Uses python-jose for JWT encoding/decoding
  • Secrets come from settings (environment variables), never hard-coded
  • Returns HTTP 401 with a clear WWW-Authenticate header on failure
  • The dependency is a simple function — inject with Depends(get_current_user)

Usage in a route:
    @router.get("/protected")
    async def protected(user: str = Depends(get_current_user)):
        return {"user": user}
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.config import settings

# ── Security scheme — tells Swagger to show the "Authorize 🔒" button ────────
bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="Paste your JWT access token obtained from POST /auth/token",
)


# ─────────────────────────────────────────────────────────────────────────────
# Token creation
# ─────────────────────────────────────────────────────────────────────────────

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT.

    Args:
        subject: Usually the username — stored in the "sub" claim.
        expires_delta: How long the token is valid.  Defaults to the value
                       set in settings (JWT_ACCESS_TOKEN_EXPIRE_MINUTES).

    Returns:
        Encoded JWT string (str).
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": subject,           # subject — who the token is for
        "exp": expire,            # expiry  — jose checks this automatically
        "iat": datetime.now(timezone.utc),  # issued-at
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Token verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_token(token: str) -> str:
    """
    Decode and validate a JWT.

    Returns:
        The username (subject) from the token on success.

    Raises:
        HTTPException 401 on any failure (expired, tampered, malformed).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Token may be expired or invalid.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username

    except JWTError:
        raise credentials_exception


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI dependency
# ─────────────────────────────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    FastAPI dependency — extracts and validates the Bearer token from the
    Authorization header.

    Inject into any route that needs authentication:
        async def my_route(user: str = Depends(get_current_user)): ...

    Returns the username string on success.
    Raises HTTP 401 automatically on failure.
    """
    return verify_token(credentials.credentials)
