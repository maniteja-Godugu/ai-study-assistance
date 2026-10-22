
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.database.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.users import User


class StudySession(Base):

    __tablename__ = "study_history"

    # Primary key
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    # Foreign key: connects each study session to its owner
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Study details
    subject: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    topic: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    study_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    # Stores the generated AI response
    generated_content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Creation timestamp in UTC
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ORM relationship with User model
    user: Mapped["User"] = relationship(
        back_populates="study_sessions"
    )