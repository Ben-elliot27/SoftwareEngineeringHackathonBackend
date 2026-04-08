from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TimeCodeBase(BaseModel):
    code: str = Field(..., description="Short identifier for the time code (e.g. DEV, ADMIN)")
    description: Optional[str] = Field(None, description="Human-readable description")
    is_active: bool = Field(True, description="Whether this time code is available for use")


class TimeCodeCreate(TimeCodeBase):
    pass


class TimeCodeUpdate(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TimeCodeResponse(TimeCodeBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
