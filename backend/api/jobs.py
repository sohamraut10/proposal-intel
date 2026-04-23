import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_db
from models.job import Job
from models.user import User
from services.aggregator import poll_all_platforms

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobOut(BaseModel):
    id: uuid.UUID
    platform: str
    title: str
    description: str | None
    category: str | None
    budget_min: float | None
    budget_max: float | None
    budget_type: str | None
    client_country: str | None
    client_rating: float | None
    proposals_count: int
    score_total: float
    is_qualified: bool
    url: str | None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[JobOut])
async def list_jobs(
    qualified_only: bool = Query(False),
    platform: str | None = Query(None),
    min_score: float = Query(0.0),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Job).order_by(Job.score_total.desc())
    if qualified_only:
        q = q.where(Job.is_qualified.is_(True))
    if platform:
        q = q.where(Job.platform == platform)
    if min_score:
        q = q.where(Job.score_total >= min_score)
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/refresh")
async def refresh_jobs(
    query: str = Query(""),
    _: User = Depends(get_current_user),
):
    count = await poll_all_platforms(query=query)
    return {"message": f"Fetched and stored {count} jobs"}
