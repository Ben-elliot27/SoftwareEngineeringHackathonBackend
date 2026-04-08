from pydantic import BaseModel

from app.db.models.user import UserRole


class Token(BaseModel):
    """OAuth2-compatible token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded JWT claims used internally by dependency functions."""

    user_id: int
    role: UserRole
