import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_db
from models.job import Job
from models.proposal import BidOutcome, Proposal, UsageTracking, Event
from models.user import User
from services.proposal_gen import generate_proposal

router = APIRouter(prefix="/proposals", tags=["proposals"])


class ProposalOut(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    platform: str | None
    proposal_text: str
    cover_letter: str | None
    approach: str | None
    highlighted_strengths: list | None
    bid_amount: float | None
    currency: str
    strategy: str
    status: str
    quality_score: int | None
    win_probability: float | None
    estimated_response_time: str | None
    tokens_used: int
    model_used: str | None
    generated_at: datetime
    submitted_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    job_id: uuid.UUID
    strategy: str = "standard"   # standard | aggressive | cautious


class UpdateProposalRequest(BaseModel):
    proposal_text: str | None = None
    cover_letter: str | None = None
    bid_amount: float | None = None
    status: str | None = None


class OutcomeRequest(BaseModel):
    status: str          # won | lost
    actual_amount: float | None = None
    feedback: str | None = None


@router.post("/generate", response_model=ProposalOut, status_code=201)
async def generate(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_result = await db.execute(select(Job).where(Job.id == body.job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Build freelancer profile from user + freelancer_profile relation
    profile = _build_profile(current_user)

    job_dict = {c.name: getattr(job, c.name) for c in job.__table__.columns}
    result = await generate_proposal(job_dict, profile, strategy=body.strategy)

    proposal = Proposal(
        user_id=current_user.id,
        job_id=job.id,
        platform=job.platform,
        proposal_text=result["proposal_text"],
        cover_letter=result.get("cover_letter"),
        approach=result.get("approach"),
        highlighted_strengths=result.get("highlighted_strengths"),
        bid_amount=result.get("bid_amount"),
        currency=result.get("currency", "USD"),
        strategy=body.strategy,
        quality_score=result.get("quality_score"),
        win_probability=result.get("win_probability"),
        estimated_response_time=result.get("estimated_response_time"),
        model_used=result.get("model_used"),
        tokens_used=result.get("tokens_used", 0),
    )
    db.add(proposal)
    await db.flush()

    # Track usage
    await _increment_usage(db, current_user.id, "proposals_generated")
    await _log_event(db, current_user.id, "proposal_generated",
                     {"job_id": str(job.id), "strategy": body.strategy})

    return proposal


@router.get("/", response_model=list[ProposalOut])
async def list_proposals(
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Proposal)
        .where(Proposal.user_id == current_user.id)
        .order_by(Proposal.created_at.desc())
    )
    if status:
        q = q.where(Proposal.status == status)
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{proposal_id}", response_model=ProposalOut)
async def get_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Proposal).where(
            Proposal.id == proposal_id, Proposal.user_id == current_user.id
        )
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.patch("/{proposal_id}", response_model=ProposalOut)
async def update_proposal(
    proposal_id: uuid.UUID,
    body: UpdateProposalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Proposal).where(
            Proposal.id == proposal_id, Proposal.user_id == current_user.id
        )
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(proposal, field, value)

    if body.status == "submitted" and not proposal.submitted_at:
        proposal.submitted_at = datetime.now(timezone.utc)
        await _increment_usage(db, current_user.id, "proposals_submitted")
        await _log_event(db, current_user.id, "proposal_submitted",
                         {"proposal_id": str(proposal_id)})

    db.add(proposal)
    return proposal


@router.post("/{proposal_id}/outcome", response_model=ProposalOut)
async def record_outcome(
    proposal_id: uuid.UUID,
    body: OutcomeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Proposal).where(
            Proposal.id == proposal_id, Proposal.user_id == current_user.id
        )
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Upsert outcome
    existing = await db.execute(
        select(BidOutcome).where(BidOutcome.proposal_id == proposal_id)
    )
    outcome = existing.scalar_one_or_none()
    if outcome:
        outcome.status = body.status
        outcome.actual_amount = body.actual_amount
        outcome.feedback = body.feedback
        outcome.outcome_date = datetime.now(timezone.utc)
    else:
        outcome = BidOutcome(
            proposal_id=proposal_id,
            user_id=current_user.id,
            job_id=proposal.job_id,
            status=body.status,
            actual_amount=body.actual_amount,
            feedback=body.feedback,
            outcome_date=datetime.now(timezone.utc),
        )
        db.add(outcome)

    proposal.status = body.status
    db.add(proposal)

    if body.status == "won":
        await _increment_usage(db, current_user.id, "proposals_won")
        if body.actual_amount:
            await _add_revenue(db, current_user.id, body.actual_amount)
        await _log_event(db, current_user.id, "proposal_won",
                         {"proposal_id": str(proposal_id), "amount": body.actual_amount})

    return proposal


# ── Helpers ─────────────────────────────────────────────────────────────────

def _build_profile(user: User) -> dict:
    profile = {
        "name": user.name,
        "bio": user.bio,
        "hourly_rate": user.hourly_rate,
        "portfolio": user.portfolio,
    }
    fp = getattr(user, "freelancer_profile", None)
    if fp:
        profile.update({
            "headline": fp.headline,
            "skills": fp.skills,
            "certifications": fp.certifications,
            "past_projects": fp.past_projects,
            "estimated_hours_per_project": fp.estimated_hours_per_project,
        })
    return profile


async def _increment_usage(db, user_id: uuid.UUID, field: str) -> None:
    from datetime import date
    month = date.today().strftime("%Y-%m")
    existing = await db.execute(
        select(UsageTracking).where(
            UsageTracking.user_id == user_id,
            UsageTracking.month == month,
        )
    )
    usage = existing.scalar_one_or_none()
    if not usage:
        usage = UsageTracking(user_id=user_id, month=month)
        db.add(usage)
        await db.flush()
    setattr(usage, field, getattr(usage, field) + 1)
    db.add(usage)


async def _add_revenue(db, user_id: uuid.UUID, amount: float) -> None:
    from datetime import date
    month = date.today().strftime("%Y-%m")
    existing = await db.execute(
        select(UsageTracking).where(
            UsageTracking.user_id == user_id,
            UsageTracking.month == month,
        )
    )
    usage = existing.scalar_one_or_none()
    if usage:
        usage.revenue_generated += amount
        db.add(usage)


async def _log_event(db, user_id: uuid.UUID, event_type: str, data: dict) -> None:
    db.add(Event(user_id=user_id, event_type=event_type, event_data=data))
