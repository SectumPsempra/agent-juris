import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class User(Base):
    """Populated by John when Clerk JWT auth is wired up."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    clerk_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[str] = mapped_column(String(16), nullable=False, default="FREE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )

    # cases relationship wired by John when FK is enforced after auth is live


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # user_id stored as plain string until John wires Clerk auth and populates the users table
    user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled Case")
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PROCESSING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )

    steps: Mapped[list["AgentStep"]] = relationship(
        "AgentStep", back_populates="case", order_by="AgentStep.step_index"
    )


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True, nullable=False)
    step_name: Mapped[str] = mapped_column(String(64), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PROCESSING")
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="steps")
