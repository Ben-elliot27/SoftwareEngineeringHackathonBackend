from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.db.models.timesheet_entry import EntryStatus
from app.schemas.time_code import TimeCodeResponse
from app.schemas.user import UserResponse


class TimesheetEntryBase(BaseModel):
    user_id: int = Field(..., description="ID of the user submitting the entry")
    time_code_id: int = Field(..., description="ID of the time code to use")
    entry_date: date = Field(..., description="Date the work was performed")
    hours: float = Field(..., gt=0, le=24, description="Hours worked (0 < hours <= 24)")
    description: Optional[str] = Field(None, description="Optional notes about the work")


class TimesheetEntryCreate(TimesheetEntryBase):
    pass


class TimesheetEntryUpdate(BaseModel):
    time_code_id: Optional[int] = None
    entry_date: Optional[date] = None
    hours: Optional[float] = Field(None, gt=0, le=24)
    description: Optional[str] = None


class RejectionRequest(BaseModel):
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")


class TimesheetEntryResponse(TimesheetEntryBase):
    id: int
    status: EntryStatus
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Nested objects for convenience
    user: Optional[UserResponse] = None
    time_code: Optional[TimeCodeResponse] = None
    approver: Optional[UserResponse] = None

    model_config = {"from_attributes": True}
