import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.user import Base


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("platform", "platform_job_id", name="uq_platform_job"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform_job_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Core fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)        # ["python", "api", ...]
    skills_required: Mapped[list | None] = mapped_column(JSON, nullable=True)
    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)  # entry | intermediate | expert
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Budget
    budget_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # fixed | hourly
    currency: Mapped[str] = mapped_column(String(10), default="USD")

    # Client
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    client_jobs_posted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    client_total_spent: Mapped[float | None] = mapped_column(Float, nullable=True)
    client_hire_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    client_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proposals_count: Mapped[int] = mapped_column(Integer, default=0)

    # Raw platform data
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    aggregation_cycle: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 6D scores (0.0–1.0 each, total 0–100)
    score_budget: Mapped[float] = mapped_column(Float, default=0.0)
    score_client: Mapped[float] = mapped_column(Float, default=0.0)
    score_category: Mapped[float] = mapped_column(Float, default=0.0)
    score_description: Mapped[float] = mapped_column(Float, default=0.0)
    score_scope: Mapped[float] = mapped_column(Float, default=0.0)
    score_timeline: Mapped[float] = mapped_column(Float, default=0.0)
    score_total: Mapped[float] = mapped_column(Float, default=0.0)
    score_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_qualified: Mapped[bool] = mapped_column(default=False, index=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    proposals: Mapped[list["Proposal"]] = relationship("Proposal", back_populates="job")
    qualification: Mapped["JobQualification | None"] = relationship(
        "JobQualification", back_populates="job", uselist=False
    )


class JobQualification(Base):
    """Cached qualification result for a job — avoids re-scoring on every request."""
    __tablename__ = "job_qualifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), __import__("sqlalchemy").ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["Job"] = relationship("Job", back_populates="qualification")
