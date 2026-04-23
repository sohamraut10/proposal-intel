"""Polls all platforms, deduplicates, scores, and persists jobs."""
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from db.database import AsyncSessionLocal
from models.job import Job
from services.filter import score_job
from services.platform_clients import FreelancerClient, PeoplePerHourClient, UpworkClient

logger = logging.getLogger(__name__)

_upwork = UpworkClient()
_freelancer = FreelancerClient()
_pph = PeoplePerHourClient()


async def poll_all_platforms(query: str = "") -> int:
    """Fetch jobs from all platforms, deduplicate, score, and upsert. Returns count stored."""
    import asyncio

    results = await asyncio.gather(
        _upwork.search_jobs(query),
        _freelancer.search_jobs(query),
        _pph.search_jobs(query),
        return_exceptions=True,
    )

    jobs: list[dict[str, Any]] = []
    for r in results:
        if isinstance(r, Exception):
            logger.error("Platform fetch error: %s", r)
        else:
            jobs.extend(r)

    if not jobs:
        logger.info("No jobs fetched from any platform")
        return 0

    scored = [_apply_scores(j) for j in jobs]
    stored = await _upsert_jobs(scored)
    logger.info("Upserted %d jobs from %d fetched", stored, len(jobs))
    return stored


def _apply_scores(job: dict[str, Any]) -> dict[str, Any]:
    scores = score_job(job)
    return {**job, **scores}


async def _upsert_jobs(jobs: list[dict[str, Any]]) -> int:
    if not jobs:
        return 0

    async with AsyncSessionLocal() as session:
        stmt = (
            insert(Job)
            .values(jobs)
            .on_conflict_do_update(
                constraint="uq_platform_job",
                set_={
                    "title": insert(Job).excluded.title,
                    "description": insert(Job).excluded.description,
                    "proposals_count": insert(Job).excluded.proposals_count,
                    "score_budget": insert(Job).excluded.score_budget,
                    "score_client": insert(Job).excluded.score_client,
                    "score_category": insert(Job).excluded.score_category,
                    "score_description": insert(Job).excluded.score_description,
                    "score_scope": insert(Job).excluded.score_scope,
                    "score_timeline": insert(Job).excluded.score_timeline,
                    "score_total": insert(Job).excluded.score_total,
                    "is_qualified": insert(Job).excluded.is_qualified,
                },
            )
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount
