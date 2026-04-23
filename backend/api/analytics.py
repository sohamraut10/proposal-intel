from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_db
from models.job import Job
from models.proposal import BidOutcome, Proposal, UsageTracking
from models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def summary(
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=period_days)

    total = await db.scalar(
        select(func.count(Proposal.id)).where(Proposal.user_id == current_user.id)
    )
    submitted = await db.scalar(
        select(func.count(Proposal.id)).where(
            Proposal.user_id == current_user.id,
            Proposal.status.in_(["submitted", "won", "lost"]),
        )
    )
    won = await db.scalar(
        select(func.count(Proposal.id)).where(
            Proposal.user_id == current_user.id, Proposal.status == "won"
        )
    )
    win_rate = round(won / submitted * 100, 1) if submitted else 0.0

    # Revenue from outcomes in period
    revenue = await db.scalar(
        select(func.coalesce(func.sum(BidOutcome.actual_amount), 0)).where(
            BidOutcome.user_id == current_user.id,
            BidOutcome.status == "won",
            BidOutcome.outcome_date >= since,
        )
    ) or 0.0

    # Average bid
    avg_bid = await db.scalar(
        select(func.avg(Proposal.bid_amount)).where(
            Proposal.user_id == current_user.id,
            Proposal.bid_amount.isnot(None),
            Proposal.created_at >= since,
        )
    ) or 0.0

    # Response time (minutes from generated to submitted)
    avg_response = await db.scalar(
        select(
            func.avg(
                func.extract("epoch", Proposal.submitted_at - Proposal.generated_at) / 60
            )
        ).where(
            Proposal.user_id == current_user.id,
            Proposal.submitted_at.isnot(None),
        )
    )

    total_jobs = await db.scalar(select(func.count(Job.id)))
    qualified_jobs = await db.scalar(
        select(func.count(Job.id)).where(Job.is_qualified.is_(True))
    )

    return {
        "period_days": period_days,
        "proposals": {
            "total": total,
            "submitted": submitted,
            "won": won,
            "win_rate_pct": win_rate,
            "avg_bid_usd": round(float(avg_bid), 2),
            "avg_response_minutes": round(float(avg_response or 0), 1),
        },
        "revenue": {
            "total_usd": round(float(revenue), 2),
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
        if status in ("submitted", "won", "lost"):
            if status == "won":
                data[platform]["won"] += cnt
            data[platform]["submitted"] += cnt

    return [
        {
            "platform": p,
            "submitted": v["submitted"],
            "won": v["won"],
            "win_rate_pct": round(v["won"] / v["submitted"] * 100, 1) if v["submitted"] else 0.0,
        }
        for p, v in data.items()
    ]


@router.get("/win-rates-by-category")
async def win_rates_by_category(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        select(Job.category, Proposal.status, func.count().label("cnt"))
        .join(Proposal, Proposal.job_id == Job.id)
        .where(Proposal.user_id == current_user.id, Job.category.isnot(None))
        .group_by(Job.category, Proposal.status)
    )
    data: dict[str, dict] = {}
    for category, status, cnt in rows:
        if category not in data:
            data[category] = {"submitted": 0, "won": 0}
        if status == "won":
            data[category]["won"] += cnt
        if status in ("submitted", "won", "lost"):
            data[category]["submitted"] += cnt

    return sorted(
        [
            {
                "category": c,
                "submitted": v["submitted"],
                "won": v["won"],
                "win_rate_pct": round(v["won"] / v["submitted"] * 100, 1) if v["submitted"] else 0.0,
            }
            for c, v in data.items()
        ],
        key=lambda x: x["win_rate_pct"],
        reverse=True,
    )


@router.get("/bid-distribution")
async def bid_distribution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    buckets = [
        ("$100-250",  100,  250),
        ("$250-400",  250,  400),
        ("$400-750",  400,  750),
        ("$750+",     750, 999999),
    ]
    result = []
    for label, lo, hi in buckets:
        count = await db.scalar(
            select(func.count(Proposal.id)).where(
                Proposal.user_id == current_user.id,
                Proposal.bid_amount >= lo,
                Proposal.bid_amount < hi,
            )
        )
        result.append({"range": label, "count": count or 0})
    return result


@router.get("/score-distribution")
async def score_distribution(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    buckets = [("0-20", 0, 20), ("20-40", 20, 40), ("40-60", 40, 60),
               ("60-80", 60, 80), ("80-100", 80, 101)]
    result = []
    for label, lo, hi in buckets:
        count = await db.scalar(
            select(func.count(Job.id)).where(
                Job.score_total >= lo, Job.score_total < hi
            )
        )
        result.append({"range": label, "count": count or 0})
    return result


@router.get("/usage")
async def usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        select(UsageTracking)
        .where(UsageTracking.user_id == current_user.id)
        .order_by(UsageTracking.month.desc())
        .limit(12)
    )
    return [
        {
            "month": u.month,
            "proposals_generated": u.proposals_generated,
            "proposals_submitted": u.proposals_submitted,
            "proposals_won": u.proposals_won,
            "revenue_generated": u.revenue_generated,
        }
        for u in rows.scalars()
    ]
