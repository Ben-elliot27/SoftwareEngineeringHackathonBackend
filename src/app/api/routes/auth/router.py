import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.security import create_access_token
from app.db.repository.users import authenticate_user
from app.schemas.auth import Token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=Token, summary="Obtain a JWT access token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Authenticate with **email** (in the *username* field) and **password**.

    Returns a JWT Bearer token that must be included in the
    ``Authorization: Bearer <token>`` header for all protected endpoints.
    """
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id, role=user.role.value)
    logger.info("User %s (%s) logged in", user.email, user.role)
    return Token(access_token=access_token)
