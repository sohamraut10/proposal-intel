from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_db
from models.job import Job
from models.proposal import Proposal
from models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_proposals = await db.scalar(
        select(func.count()).where(Proposal.user_id == current_user.id)
    )
    won = await db.scalar(
        select(func.count()).where(Proposal.user_id == current_user.id, Proposal.status == "won")
    )
    submitted = await db.scalar(
        select(func.count()).where(
            Proposal.user_id == current_user.id, Proposal.status == "submitted"
        )
    )
    win_rate = round(won / submitted * 100, 1) if submitted else 0.0

    total_jobs = await db.scalar(select(func.count(Job.id)))
    qualified_jobs = await db.scalar(select(func.count(Job.id)).where(Job.is_qualified.is_(True)))

    return {
        "proposals": {
            "total": total_proposals,
            "submitted": submitted,
            "won": won,
            "win_rate_pct": win_rate,
        },
        "jobs": {
            "total": total_jobs,
            "qualified": qualified_jobs,
        },
    }


@router.get("/win-rates-by-platform")
async def win_rates_by_platform(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        select(Job.platform, Proposal.status, func.count().label("cnt"))
        .join(Proposal, Proposal.job_id == Job.id)
        .where(Proposal.user_id == current_user.id)
        .group_by(Job.platform, Proposal.status)
    )
    data: dict[str, dict] = {}
    for platform, status, cnt in rows:
        if platform not in data:
            data[platform] = {"submitted": 0, "won": 0}
        if status in ("submitted", "won"):
            data[platform][status] += cnt

    return [
        {
            "platform": p,
            "submitted": v["submitted"],
            "won": v["won"],
            "win_rate_pct": round(v["won"] / v["submitted"] * 100, 1) if v["submitted"] else 0.0,
        }
        for p, v in data.items()
    ]


@router.get("/score-distribution")
async def score_distribution(_: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    buckets = [
        ("0-20", 0, 20),
        ("20-40", 20, 40),
        ("40-60", 40, 60),
        ("60-80", 60, 80),
        ("80-100", 80, 100),
    ]
    result = []
    for label, lo, hi in buckets:
        count = await db.scalar(
            select(func.count(Job.id)).where(Job.score_total >= lo, Job.score_total < hi)
        )
        result.append({"range": label, "count": count})
    return result
