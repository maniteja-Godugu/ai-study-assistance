from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.studysession import StudySession

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    study_sessions: Mapped[list["StudySession"]] = relationship(
        back_populates="user"
    )
