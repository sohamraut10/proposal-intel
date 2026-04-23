import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)  # null for OAuth users
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    hourly_rate: Mapped[float | None] = mapped_column(nullable=True)
    portfolio: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Subscription
    tier: Mapped[str] = mapped_column(String(50), default="free")  # free | pro | agency | enterprise
    subscription_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # active | cancelled | paused
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Auth
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # google | github
    oauth_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    proposals: Mapped[list["Proposal"]] = relationship("Proposal", back_populates="user")
    freelancer_profile: Mapped["FreelancerProfile | None"] = relationship(
        "FreelancerProfile", back_populates="user", uselist=False
    )
    bid_outcomes: Mapped[list["BidOutcome"]] = relationship("BidOutcome", back_populates="user")
    usage_tracking: Mapped[list["UsageTracking"]] = relationship("UsageTracking", back_populates="user")


class FreelancerProfile(Base):
    __tablename__ = "freelancer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), __import__("sqlalchemy").ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    headline: Mapped[str | None] = mapped_column(String(500), nullable=True)
    skills: Mapped[list | None] = mapped_column(JSON, nullable=True)          # ["python", "fastapi", ...]
    certifications: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ["AWS", ...]
    past_projects: Mapped[list | None] = mapped_column(JSON, nullable=True)   # [{title, description}, ...]
    estimated_hours_per_project: Mapped[int | None] = mapped_column(Integer, nullable=True)
    client_rating: Mapped[float | None] = mapped_column(nullable=True)
    jobs_completed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="freelancer_profile")
