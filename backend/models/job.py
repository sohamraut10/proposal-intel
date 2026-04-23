import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.user import Base


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("platform", "platform_job_id", name="uq_platform_job"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # upwork | freelancer | pph
    platform_job_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skills_required: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array as text
    budget_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # fixed | hourly
    client_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    client_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    client_total_spent: Mapped[float | None] = mapped_column(Float, nullable=True)
    client_hire_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    proposals_count: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # 6D score
    score_budget: Mapped[float] = mapped_column(Float, default=0.0)
    score_client: Mapped[float] = mapped_column(Float, default=0.0)
    score_category: Mapped[float] = mapped_column(Float, default=0.0)
    score_description: Mapped[float] = mapped_column(Float, default=0.0)
    score_scope: Mapped[float] = mapped_column(Float, default=0.0)
    score_timeline: Mapped[float] = mapped_column(Float, default=0.0)
    score_total: Mapped[float] = mapped_column(Float, default=0.0)

    is_qualified: Mapped[bool] = mapped_column(default=False)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    proposals: Mapped[list["Proposal"]] = relationship("Proposal", back_populates="job")
