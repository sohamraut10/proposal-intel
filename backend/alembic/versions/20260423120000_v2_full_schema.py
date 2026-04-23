"""v2 full schema — align to spec

Revision ID: 20260423120000
Revises: 20260423083909
Create Date: 2026-04-23 12:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision: str = "20260423120000"
down_revision: Union[str, None] = "20260423083909"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users: add missing columns ───────────────────────────────────────────
    op.add_column("users", sa.Column("name", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("portfolio", JSON, nullable=True))
    op.add_column("users", sa.Column("tier", sa.String(50), server_default="free", nullable=False))
    op.add_column("users", sa.Column("subscription_status", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("oauth_provider", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("oauth_id", sa.String(255), nullable=True))

    # rename plan → tier (copy data first via trigger-free approach)
    op.execute("UPDATE users SET tier = plan")
    op.drop_column("users", "plan")

    # hashed_password becomes nullable (OAuth users have none)
    op.alter_column("users", "hashed_password", nullable=True)

    # rename full_name → name
    op.execute("UPDATE users SET name = full_name")
    op.drop_column("users", "full_name")

    # ── freelancer_profiles (new) ────────────────────────────────────────────
    op.create_table(
        "freelancer_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("headline", sa.String(500), nullable=True),
        sa.Column("skills", JSON, nullable=True),
        sa.Column("certifications", JSON, nullable=True),
        sa.Column("past_projects", JSON, nullable=True),
        sa.Column("estimated_hours_per_project", sa.Integer, nullable=True),
        sa.Column("client_rating", sa.Float, nullable=True),
        sa.Column("jobs_completed", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_fp_user"),
    )
    op.create_index("ix_fp_user_id", "freelancer_profiles", ["user_id"])

    # ── jobs: add missing columns ────────────────────────────────────────────
    op.add_column("jobs", sa.Column("client_name", sa.String(255), nullable=True))
    op.add_column("jobs", sa.Column("client_jobs_posted", sa.Integer, nullable=True))
    op.add_column("jobs", sa.Column("currency", sa.String(10), server_default="USD", nullable=False))
    op.add_column("jobs", sa.Column("tags", JSON, nullable=True))
    op.add_column("jobs", sa.Column("level", sa.String(50), nullable=True))
    op.add_column("jobs", sa.Column("raw_data", JSON, nullable=True))
    op.add_column("jobs", sa.Column("aggregation_cycle", sa.Integer, nullable=True))
    op.add_column("jobs", sa.Column("score_reasoning", sa.Text, nullable=True))

    # skills_required: change from Text to JSON (NULL-safe migration)
    op.add_column("jobs", sa.Column("skills_required_json", JSON, nullable=True))
    op.execute(
        "UPDATE jobs SET skills_required_json = to_json(skills_required) "
        "WHERE skills_required IS NOT NULL"
    )
    op.drop_column("jobs", "skills_required")
    op.alter_column("jobs", "skills_required_json", new_column_name="skills_required")

    # add indexes
    op.create_index("ix_jobs_platform", "jobs", ["platform"])
    op.create_index("ix_jobs_category", "jobs", ["category"])
    op.create_index("ix_jobs_is_qualified", "jobs", ["is_qualified"])
    op.create_index("ix_jobs_posted_at", "jobs", ["posted_at"])

    # ── job_qualifications (new) ─────────────────────────────────────────────
    op.create_table(
        "job_qualifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", UUID(as_uuid=True),
                  sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("passed", sa.Boolean, nullable=False),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("details", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("job_id", name="uq_jq_job"),
    )
    op.create_index("ix_jq_job_id", "job_qualifications", ["job_id"])

    # ── proposals: add missing columns ───────────────────────────────────────
    op.add_column("proposals", sa.Column("platform", sa.String(50), nullable=True))
    op.add_column("proposals", sa.Column("approach", sa.Text, nullable=True))
    op.add_column("proposals", sa.Column("highlighted_strengths", JSON, nullable=True))
    op.add_column("proposals", sa.Column("currency", sa.String(10), server_default="USD", nullable=False))
    op.add_column("proposals", sa.Column("strategy", sa.String(50), server_default="standard", nullable=False))
    op.add_column("proposals", sa.Column("quality_score", sa.Integer, nullable=True))
    op.add_column("proposals", sa.Column("win_probability", sa.Float, nullable=True))
    op.add_column("proposals", sa.Column("estimated_response_time", sa.String(50), nullable=True))
    op.add_column("proposals", sa.Column("generated_at", sa.DateTime(timezone=True),
                                          server_default=sa.func.now(), nullable=False))

    # rename content → proposal_text, status default pending
    op.add_column("proposals", sa.Column("proposal_text_new", sa.Text, nullable=True))
    op.execute("UPDATE proposals SET proposal_text_new = content")
    op.drop_column("proposals", "content")
    op.alter_column("proposals", "proposal_text_new", new_column_name="proposal_text", nullable=False)

    op.execute("UPDATE proposals SET status = 'pending' WHERE status = 'draft'")
    op.add_column("proposals", sa.Column("bid_type_drop", sa.String(50), nullable=True))
    op.drop_column("proposals", "outcome_at")

    op.create_index("ix_proposals_status", "proposals", ["status"])

    # ── bid_outcomes (new) ───────────────────────────────────────────────────
    op.create_table(
        "bid_outcomes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("proposal_id", UUID(as_uuid=True),
                  sa.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID(as_uuid=True),
                  sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("feedback", sa.Text, nullable=True),
        sa.Column("actual_amount", sa.Float, nullable=True),
        sa.Column("outcome_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("proposal_id", name="uq_bo_proposal"),
    )
    op.create_index("ix_bo_user_id", "bid_outcomes", ["user_id"])
    op.create_index("ix_bo_proposal_id", "bid_outcomes", ["proposal_id"])

    # ── usage_tracking (new) ─────────────────────────────────────────────────
    op.create_table(
        "usage_tracking",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("proposals_generated", sa.Integer, server_default="0", nullable=False),
        sa.Column("proposals_submitted", sa.Integer, server_default="0", nullable=False),
        sa.Column("proposals_won", sa.Integer, server_default="0", nullable=False),
        sa.Column("revenue_generated", sa.Float, server_default="0", nullable=False),
        sa.Column("api_calls", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "month", name="uq_usage_user_month"),
    )
    op.create_index("ix_usage_user_id", "usage_tracking", ["user_id"])

    # ── events (new) ─────────────────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_data", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_events_user_id", "events", ["user_id"])
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_created_at", "events", ["created_at"])


def downgrade() -> None:
    op.drop_table("events")
    op.drop_table("usage_tracking")
    op.drop_table("bid_outcomes")
    op.drop_table("job_qualifications")
    op.drop_table("freelancer_profiles")
    # NOTE: column renames are not reversible without data loss — downgrade drops added columns only
    for col in ["platform", "approach", "highlighted_strengths", "currency", "strategy",
                "quality_score", "win_probability", "estimated_response_time", "generated_at",
                "bid_type_drop"]:
        op.drop_column("proposals", col)
    for col in ["client_name", "client_jobs_posted", "currency", "tags", "level",
                "raw_data", "aggregation_cycle", "score_reasoning"]:
        op.drop_column("jobs", col)
    for col in ["name", "portfolio", "tier", "subscription_status", "oauth_provider", "oauth_id"]:
        op.drop_column("users", col)
