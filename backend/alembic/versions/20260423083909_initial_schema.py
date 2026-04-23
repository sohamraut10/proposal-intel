"""initial schema

Revision ID: 20260423083909
Revises:
Create Date: 2026-04-23 08:39:09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260423083909"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("skills", sa.Text, nullable=True),
        sa.Column("hourly_rate", sa.Float, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("is_verified", sa.Boolean, server_default="false", nullable=False),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("plan", sa.String(50), server_default="free", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("platform_job_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("skills_required", sa.Text, nullable=True),
        sa.Column("budget_min", sa.Float, nullable=True),
        sa.Column("budget_max", sa.Float, nullable=True),
        sa.Column("budget_type", sa.String(50), nullable=True),
        sa.Column("client_country", sa.String(100), nullable=True),
        sa.Column("client_rating", sa.Float, nullable=True),
        sa.Column("client_total_spent", sa.Float, nullable=True),
        sa.Column("client_hire_rate", sa.Float, nullable=True),
        sa.Column("proposals_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("duration", sa.String(100), nullable=True),
        sa.Column("experience_level", sa.String(50), nullable=True),
        sa.Column("url", sa.String(1000), nullable=True),
        sa.Column("score_budget", sa.Float, server_default="0", nullable=False),
        sa.Column("score_client", sa.Float, server_default="0", nullable=False),
        sa.Column("score_category", sa.Float, server_default="0", nullable=False),
        sa.Column("score_description", sa.Float, server_default="0", nullable=False),
        sa.Column("score_scope", sa.Float, server_default="0", nullable=False),
        sa.Column("score_timeline", sa.Float, server_default="0", nullable=False),
        sa.Column("score_total", sa.Float, server_default="0", nullable=False),
        sa.Column("is_qualified", sa.Boolean, server_default="false", nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("platform", "platform_job_id", name="uq_platform_job"),
    )

    op.create_table(
        "proposals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("cover_letter", sa.Text, nullable=True),
        sa.Column("bid_amount", sa.Float, nullable=True),
        sa.Column("bid_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), server_default="draft", nullable=False),
        sa.Column("tokens_used", sa.Integer, server_default="0", nullable=False),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_proposals_user_id", "proposals", ["user_id"])
    op.create_index("ix_proposals_job_id", "proposals", ["job_id"])


def downgrade() -> None:
    op.drop_table("proposals")
    op.drop_table("jobs")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
