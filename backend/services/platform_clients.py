"""Platform API clients — Upwork, Freelancer, PeoplePerHour.

Each client exposes search_jobs() → list[dict] using the unified Job schema.
Credentials are read from settings; missing keys → skip with warning.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(30.0)


# ── Upwork ─────────────────────────────────────────────────────────────────
class UpworkClient:
    """
    Upwork Talent API v4.
    Docs: https://developers.upwork.com/
    Auth: OAuth 2.0 — use UPWORK_API_KEY as Bearer token after your OAuth flow.
    """
    SEARCH_URL = "https://api.upwork.com/api/profiles/v4/search/jobs"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def search_jobs(self, query: str = "", limit: int = 50) -> list[dict[str, Any]]:
        if not settings.UPWORK_API_KEY:
            logger.warning("UPWORK_API_KEY not set — skipping Upwork")
            return []

        async with httpx.AsyncClient(timeout=TIMEOUT) as http:
            resp = await http.get(
                self.SEARCH_URL,
                headers={
                    "Authorization": f"Bearer {settings.UPWORK_API_KEY}",
                    "Accept": "application/json",
                },
                params={
                    "limit": limit,
                    "sort": "recency",
                    "category2": ",".join([
                        "Writing", "Translation", "Data Entry",
                        "Web Development", "Software Development",
                    ]),
                    "duration": "week,less-than-1-month",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        jobs = data.get("jobs", {})
        if isinstance(jobs, dict):
            jobs = jobs.get("job", [])
        return [self._normalize(j) for j in (jobs or [])]

    @staticmethod
    def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
        buyer = raw.get("buyer") or raw.get("client") or {}
        budget = raw.get("budget") or {}
        return {
            "platform": "upwork",
            "platform_job_id": str(raw.get("id") or raw.get("uid") or ""),
            "title": raw.get("title", ""),
            "description": raw.get("snippet") or raw.get("description") or "",
            "category": (raw.get("category2") or {}).get("name") if isinstance(raw.get("category2"), dict)
                        else raw.get("category2"),
            "tags": [s.get("prettyName") for s in (raw.get("skills") or {}).get("skill", [])
                     if isinstance(s, dict)],
            "skills_required": [s.get("prettyName") for s in (raw.get("skills") or {}).get("skill", [])
                                 if isinstance(s, dict)],
            "budget_min": _float(budget.get("amount") or budget.get("min")),
            "budget_max": _float(budget.get("amount") or budget.get("max")),
            "budget_type": "fixed" if raw.get("jobType") == "Fixed" else "hourly",
            "currency": "USD",
            "client_name": buyer.get("name") or buyer.get("display_name"),
            "client_rating": _float(buyer.get("feedback") or buyer.get("rating")),
            "client_jobs_posted": _int(buyer.get("jobs_posted") or buyer.get("jobsPosted")),
            "client_total_spent": _float(buyer.get("totalCharges") or buyer.get("total_spent")),
            "client_hire_rate": _float(buyer.get("hireRate") or buyer.get("hire_rate")),
            "client_country": (buyer.get("location") or {}).get("country") if isinstance(
                buyer.get("location"), dict) else buyer.get("country"),
            "proposals_count": _int(raw.get("proposalsTier") or raw.get("proposals_count")),
            "duration": raw.get("duration") or raw.get("durationLabel"),
            "level": raw.get("tier") or raw.get("experienceLevel"),
            "url": f"https://www.upwork.com/jobs/~{raw.get('id') or raw.get('uid') or ''}",
            "posted_at": raw.get("date_created") or raw.get("dateCreated"),
            "raw_data": raw,
        }


# ── Freelancer ─────────────────────────────────────────────────────────────
class FreelancerClient:
    """
    Freelancer.com API v0.1.
    Docs: https://developers.freelancer.com/
    Auth: Pass FREELANCER_API_KEY as Authorization-Token header.
    """
    SEARCH_URL = "https://api.freelancer.com/api/projects/0.1/projects/active"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def search_jobs(self, query: str = "", limit: int = 50) -> list[dict[str, Any]]:
        if not settings.FREELANCER_API_KEY:
            logger.warning("FREELANCER_API_KEY not set — skipping Freelancer")
            return []

        async with httpx.AsyncClient(timeout=TIMEOUT) as http:
            resp = await http.get(
                self.SEARCH_URL,
                headers={
                    "Authorization-Token": settings.FREELANCER_API_KEY,
                    "Content-Type": "application/json",
                },
                params={
                    "limit": limit,
                    "offset": 0,
                    "orderby": "time_submitted",
                    "query": query,
                    "full_description": True,
                    "job_details": True,
                    "user_details": True,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        projects = (data.get("result") or {}).get("projects") or []
        return [self._normalize(p) for p in projects]

    @staticmethod
    def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
        budget = raw.get("budget") or {}
        owner = raw.get("owner_object") or {}
        jobs = raw.get("jobs") or []
        return {
            "platform": "freelancer",
            "platform_job_id": str(raw.get("id") or ""),
            "title": raw.get("title") or "",
            "description": raw.get("description") or "",
            "category": jobs[0].get("name") if jobs else None,
            "tags": [j.get("name") for j in jobs if j.get("name")],
            "skills_required": [j.get("name") for j in jobs if j.get("name")],
            "budget_min": _float(budget.get("minimum")),
            "budget_max": _float(budget.get("maximum")),
            "budget_type": "fixed" if raw.get("type") == "fixed" else "hourly",
            "currency": "USD",
            "client_name": owner.get("display_name") or owner.get("username"),
            "client_rating": _float((owner.get("status") or {}).get("payment_verified_score")),
            "client_jobs_posted": _int((owner.get("employer_reputation") or {}).get("jobs_posted")),
            "client_total_spent": None,
            "client_hire_rate": None,
            "client_country": (owner.get("location") or {}).get("country", {}).get("name")
                              if isinstance((owner.get("location") or {}).get("country"), dict)
                              else None,
            "proposals_count": _int((raw.get("bid_stats") or {}).get("bid_count")),
            "duration": None,
            "level": None,
            "url": f"https://www.freelancer.com/projects/{raw.get('seo_url') or raw.get('id') or ''}",
            "posted_at": raw.get("time_submitted"),
            "raw_data": raw,
        }


# ── PeoplePerHour ──────────────────────────────────────────────────────────
class PeoplePerHourClient:
    """
    PeoplePerHour API v1.
    Auth: X-API-Key header.
    """
    SEARCH_URL = "https://api.peopleperhour.com/v1/workoffer"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def search_jobs(self, query: str = "", limit: int = 50) -> list[dict[str, Any]]:
        if not settings.PPH_API_KEY:
            logger.warning("PPH_API_KEY not set — skipping PeoplePerHour")
            return []

        async with httpx.AsyncClient(timeout=TIMEOUT) as http:
            resp = await http.get(
                self.SEARCH_URL,
                headers={"X-API-Key": settings.PPH_API_KEY},
                params={"q": query, "per_page": limit, "sort": "created_at"},
            )
            resp.raise_for_status()
            data = resp.json()

        offers = data.get("data") or []
        return [self._normalize(o) for o in offers]

    @staticmethod
    def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "platform": "pph",
            "platform_job_id": str(raw.get("id") or ""),
            "title": raw.get("name") or "",
            "description": raw.get("description") or "",
            "category": raw.get("category_name"),
            "tags": raw.get("skills") or [],
            "skills_required": raw.get("skills") or [],
            "budget_min": _float(raw.get("budget")),
            "budget_max": _float(raw.get("budget")),
            "budget_type": "fixed",
            "currency": raw.get("currency") or "USD",
            "client_name": raw.get("buyer_name"),
            "client_rating": _float(raw.get("buyer_rating")),
            "client_jobs_posted": None,
            "client_total_spent": None,
            "client_hire_rate": None,
            "client_country": raw.get("buyer_location"),
            "proposals_count": _int(raw.get("proposals_count")),
            "duration": raw.get("deadline"),
            "level": None,
            "url": raw.get("url"),
            "posted_at": raw.get("created_at"),
            "raw_data": raw,
        }


# ── Helpers ────────────────────────────────────────────────────────────────
def _float(val: Any) -> float | None:
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _int(val: Any) -> int | None:
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None
