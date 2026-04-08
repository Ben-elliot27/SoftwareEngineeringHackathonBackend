from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimeCode(Base):
    __tablename__ = "time_codes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    timesheet_entries: Mapped[list["TimesheetEntry"]] = relationship(
        "TimesheetEntry", back_populates="time_code"
    )
    user_access: Mapped[list["UserTimeCodeAccess"]] = relationship(
        "UserTimeCodeAccess",
        back_populates="time_code",
        cascade="all, delete-orphan",
    )
