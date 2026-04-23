"""Poll all platforms, deduplicate, score, and persist jobs."""
from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any

from sqlalchemy.dialects.postgresql import insert

from db.database import AsyncSessionLocal
from models.job import Job
from services.filter import score_job
from services.platform_clients import FreelancerClient, PeoplePerHourClient, UpworkClient

logger = logging.getLogger(__name__)

_upwork = UpworkClient()
_freelancer = FreelancerClient()
_pph = PeoplePerHourClient()

_cycle_count = 0


async def poll_all_platforms(query: str = "") -> int:
    """Fetch, deduplicate, score, and upsert jobs. Returns number of rows upserted."""
    global _cycle_count
    _cycle_count += 1
    cycle = _cycle_count

    logger.info("Aggregation cycle #%d started", cycle)
    results = await asyncio.gather(
        _upwork.search_jobs(query),
        _freelancer.search_jobs(query),
        _pph.search_jobs(query),
        return_exceptions=True,
    )

    raw_jobs: list[dict[str, Any]] = []
    per_platform: dict[str, int] = {}
    for platform, result in zip(["upwork", "freelancer", "pph"], results):
        if isinstance(result, Exception):
            logger.error("Platform %s error: %s", platform, result)
            per_platform[platform] = 0
        else:
            per_platform[platform] = len(result)
            raw_jobs.extend(result)

    unique = _deduplicate(raw_jobs)
    dedup_rate = 1 - len(unique) / max(len(raw_jobs), 1)

    scored = [_apply_scores(j, cycle) for j in unique]
    stored = await _upsert_jobs(scored)

    logger.info(
        "Cycle #%d complete | fetched=%d unique=%d (dedup=%.0f%%) stored=%d | %s",
        cycle, len(raw_jobs), len(unique), dedup_rate * 100, stored,
        " ".join(f"{p}={n}" for p, n in per_platform.items()),
    )
    return stored


def _deduplicate(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicates using MD5 hash of (platform + title + client + budget_min)."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for job in jobs:
        key = hashlib.md5(
            "|".join([
                str(job.get("platform") or ""),
                str(job.get("title") or "").lower().strip(),
                str(job.get("client_name") or "").lower().strip(),
                str(job.get("budget_min") or ""),
            ]).encode()
        ).hexdigest()
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


def _apply_scores(job: dict[str, Any], cycle: int) -> dict[str, Any]:
    scores = score_job(job)
    return {**job, **scores, "aggregation_cycle": cycle}


async def _upsert_jobs(jobs: list[dict[str, Any]]) -> int:
    if not jobs:
        return 0

    # Keep only columns that exist on the Job model
    job_columns = {c.name for c in Job.__table__.columns}
    rows = []
    for job in jobs:
        row = {k: v for k, v in job.items() if k in job_columns}
        rows.append(row)

    async with AsyncSessionLocal() as session:
        stmt = (
            insert(Job)
            .values(rows)
            .on_conflict_do_update(
                constraint="uq_platform_job",
                set_={
                    "title": insert(Job).excluded.title,
                    "description": insert(Job).excluded.description,
                    "proposals_count": insert(Job).excluded.proposals_count,
                    "tags": insert(Job).excluded.tags,
                    "raw_data": insert(Job).excluded.raw_data,
                    "aggregation_cycle": insert(Job).excluded.aggregation_cycle,
                    "score_budget": insert(Job).excluded.score_budget,
                    "score_client": insert(Job).excluded.score_client,
                    "score_category": insert(Job).excluded.score_category,
                    "score_description": insert(Job).excluded.score_description,
                    "score_scope": insert(Job).excluded.score_scope,
                    "score_timeline": insert(Job).excluded.score_timeline,
                    "score_total": insert(Job).excluded.score_total,
                    "score_reasoning": insert(Job).excluded.score_reasoning,
                    "is_qualified": insert(Job).excluded.is_qualified,
                    "fetched_at": insert(Job).excluded.fetched_at,
                },
            )
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount
