from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_db
from models.user import User

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    email: str
    name: str | None
    bio: str | None
    hourly_rate: float | None
    tier: str

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    name: str | None = None
    bio: str | None = None
    hourly_rate: float | None = None


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.add(current_user)
    await db.flush()
    return current_user
