"""
routes/auth.py — Authentication Endpoints
==========================================
Provides a simple login endpoint that exchanges credentials for a JWT.

POST /auth/token  →  returns { access_token, token_type, expires_in }

In a real production system you would:
  • Store users in a database (PostgreSQL via SQLAlchemy)
  • Hash passwords with bcrypt (passlib)
  • Support refresh tokens

For an internship portfolio this implementation shows:
  ✓ JWT issuance
  ✓ Environment-variable secrets
  ✓ Clean FastAPI router pattern
  ✓ Swagger-documented auth flow
"""

from datetime import timedelta

from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.models.schemas import LoginRequest, TokenResponse
from app.utils.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login — get a JWT access token",
    responses={
        200: {"description": "Login successful — use the returned token as a Bearer token."},
        401: {"description": "Invalid username or password."},
    },
)
async def login(credentials: LoginRequest) -> TokenResponse:
    """
    Exchange username + password for a JWT Bearer token.

    **How to use in Swagger UI:**
    1. Call this endpoint to get a token.
    2. Click the **Authorize 🔒** button at the top of the page.
    3. Paste the token into the `BearerAuth` field.
    4. All protected endpoints will now work.

    **Demo credentials** (set via environment variables):
    - username: `ariras_user`
    - password: `ariras_pass`
    """
    # ── Credential check ──────────────────────────────────────────────────────
    # Simple single-user check — swap this for a DB lookup in production.
    valid = (
        credentials.username == settings.DEMO_USERNAME
        and credentials.password == settings.DEMO_PASSWORD
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Issue token ───────────────────────────────────────────────────────────
    expires_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    token = create_access_token(
        subject=credentials.username,
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_seconds,
    )
