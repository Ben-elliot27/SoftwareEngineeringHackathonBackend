"""
Association table that records which time codes a user is allowed to use.

An admin can grant or revoke access per user/time-code pair.
If a user has *no* rows in this table, they have access to *no* time codes
(unless they are an admin, who always sees every code).
"""
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserTimeCodeAccess(Base):
    __tablename__ = "user_time_code_access"
    __table_args__ = (
        UniqueConstraint("user_id", "time_code_id", name="uq_user_time_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    time_code_id: Mapped[int] = mapped_column(
        ForeignKey("time_codes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="time_code_access")  # type: ignore[name-defined]
    time_code: Mapped["TimeCode"] = relationship("TimeCode", back_populates="user_access")  # type: ignore[name-defined]
