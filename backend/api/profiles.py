import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_db
from models.user import FreelancerProfile, User

router = APIRouter(prefix="/profiles", tags=["profiles"])


class ProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    headline: str | None
    skills: list | None
    certifications: list | None
    past_projects: list | None
    estimated_hours_per_project: int | None
    client_rating: float | None
    jobs_completed: int

    class Config:
        from_attributes = True


class UpsertProfileRequest(BaseModel):
    headline: str | None = None
    skills: list[str] | None = None
    certifications: list[str] | None = None
    past_projects: list[dict] | None = None
    estimated_hours_per_project: int | None = None
    client_rating: float | None = None
    jobs_completed: int | None = None


@router.get("/me", response_model=ProfileOut)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found — create one first")
    return profile


@router.put("/me", response_model=ProfileOut)
async def upsert_my_profile(
    body: UpsertProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = FreelancerProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await db.flush()
    return profile
