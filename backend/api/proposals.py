import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_db
from models.job import Job
from models.proposal import Proposal
from models.user import User
from services.proposal_gen import generate_proposal

router = APIRouter(prefix="/proposals", tags=["proposals"])


class ProposalOut(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    content: str
    cover_letter: str | None
    bid_amount: float | None
    bid_type: str | None
    status: str
    tokens_used: int
    model_used: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    job_id: uuid.UUID
    bid_amount: float | None = None
    bid_type: str | None = None


class UpdateProposalRequest(BaseModel):
    content: str | None = None
    cover_letter: str | None = None
    bid_amount: float | None = None
    status: str | None = None


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

    profile = {
        "full_name": current_user.full_name,
        "skills": current_user.skills,
        "hourly_rate": current_user.hourly_rate,
        "bio": current_user.bio,
    }
    job_dict = {c.name: getattr(job, c.name) for c in job.__table__.columns}

    result = await generate_proposal(job_dict, profile)

    proposal = Proposal(
        user_id=current_user.id,
        job_id=job.id,
        content=result["content"],
        cover_letter=result["cover_letter"],
        bid_amount=body.bid_amount,
        bid_type=body.bid_type,
        model_used=result["model_used"],
        tokens_used=result["tokens_used"],
    )
    db.add(proposal)
    await db.flush()
    return proposal


@router.get("/", response_model=list[ProposalOut])
async def list_proposals(
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Proposal).where(Proposal.user_id == current_user.id).order_by(Proposal.created_at.desc())
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
        select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == current_user.id)
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
        select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == current_user.id)
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(proposal, field, value)

    if body.status == "submitted" and not proposal.submitted_at:
        proposal.submitted_at = datetime.now(timezone.utc)

    db.add(proposal)
    return proposal
