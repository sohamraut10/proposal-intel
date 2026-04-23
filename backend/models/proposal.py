import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.user import Base


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Generated content
    proposal_text: Mapped[str] = mapped_column(Text, nullable=False)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    approach: Mapped[str | None] = mapped_column(Text, nullable=True)
    highlighted_strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Bid
    bid_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    strategy: Mapped[str] = mapped_column(String(50), default="standard")  # standard | aggressive | cautious

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    # pending | submitted | won | lost

    # Quality metrics
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    win_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_response_time: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Generation metadata
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="proposals")
    job: Mapped["Job"] = relationship("Job", back_populates="proposals")
    outcome: Mapped["BidOutcome | None"] = relationship("BidOutcome", back_populates="proposal", uselist=False)


class BidOutcome(Base):
    __tablename__ = "bid_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # won | lost | pending
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    proposal: Mapped["Proposal"] = relationship("Proposal", back_populates="outcome")
    user: Mapped["User"] = relationship("User", back_populates="bid_outcomes")


class UsageTracking(Base):
    __tablename__ = "usage_tracking"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    proposals_generated: Mapped[int] = mapped_column(Integer, default=0)
    proposals_submitted: Mapped[int] = mapped_column(Integer, default=0)
    proposals_won: Mapped[int] = mapped_column(Integer, default=0)
    revenue_generated: Mapped[float] = mapped_column(Float, default=0.0)
    api_calls: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="usage_tracking")

    __table_args__ = (__import__("sqlalchemy").UniqueConstraint("user_id", "month", name="uq_usage_user_month"),)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # proposal_generated | proposal_submitted | proposal_won | job_viewed | filter_used
    event_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
