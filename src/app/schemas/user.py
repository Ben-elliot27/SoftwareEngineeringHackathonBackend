from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.db.models.user import UserRole


class UserBase(BaseModel):
    name: str = Field(..., description="Full name of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    role: UserRole = Field(UserRole.employee, description="Role of the user")
    is_active: bool = Field(True, description="Whether the user account is active")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plain-text password (will be hashed)")


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
