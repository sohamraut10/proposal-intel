"""Thin API wrappers for Upwork, Freelancer, and PeoplePerHour."""
import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(30.0)


class UpworkClient:
    BASE_URL = "https://www.upwork.com/api"

    def __init__(self) -> None:
        self._token: str | None = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                "https://www.upwork.com/api/v3/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.UPWORK_CLIENT_ID,
                    "client_secret": settings.UPWORK_CLIENT_SECRET,
                },
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
        return self._token  # type: ignore[return-value]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_jobs(self, query: str = "", limit: int = 50) -> list[dict[str, Any]]:
        if not settings.UPWORK_CLIENT_ID:
            logger.warning("Upwork credentials not configured — skipping")
            return []
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                f"{self.BASE_URL}/profiles/v2/search/jobs.json",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": query, "paging": f"0;{limit}"},
            )
            resp.raise_for_status()
            data = resp.json()
        jobs = data.get("jobs", {}).get("job", [])
        return [self._normalize(j) for j in jobs]

    @staticmethod
    def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "platform": "upwork",
            "platform_job_id": str(raw.get("id", "")),
            "title": raw.get("title", ""),
            "description": raw.get("snippet", ""),
            "category": raw.get("category2", {}).get("name") if isinstance(raw.get("category2"), dict) else None,
            "skills_required": str([s.get("prettyName") for s in raw.get("skills", {}).get("skill", [])]),
            "budget_min": raw.get("budget", {}).get("amount") if isinstance(raw.get("budget"), dict) else None,
            "budget_max": raw.get("budget", {}).get("amount") if isinstance(raw.get("budget"), dict) else None,
            "budget_type": "fixed" if raw.get("jobType") == "Fixed" else "hourly",
            "client_country": raw.get("clientCountry"),
            "client_rating": float(raw.get("clientFeedback", 0) or 0),
            "client_total_spent": float(raw.get("totalCharges", 0) or 0),
            "proposals_count": int(raw.get("proposalsTier", 0) or 0),
            "duration": raw.get("duration"),
            "experience_level": raw.get("experienceLevel"),
            "url": f"https://www.upwork.com/jobs/~{raw.get('id', '')}",
        }


class FreelancerClient:
    BASE_URL = "https://www.freelancer.com/api"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_jobs(self, query: str = "", limit: int = 50) -> list[dict[str, Any]]:
        if not settings.FREELANCER_CLIENT_ID:
            logger.warning("Freelancer credentials not configured — skipping")
            return []
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                f"{self.BASE_URL}/projects/0.1/projects/active",
                headers={"freelancer-oauth-v1": settings.FREELANCER_CLIENT_ID},
                params={"query": query, "limit": limit, "full_description": True},
            )
            resp.raise_for_status()
            data = resp.json()
        projects = data.get("result", {}).get("projects", [])
        return [self._normalize(p) for p in projects]

    @staticmethod
    def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
        budget = raw.get("budget", {}) or {}
        return {
            "platform": "freelancer",
            "platform_job_id": str(raw.get("id", "")),
            "title": raw.get("title", ""),
            "description": raw.get("description", ""),
            "category": raw.get("jobs", [{}])[0].get("name") if raw.get("jobs") else None,
            "skills_required": str([j.get("name") for j in raw.get("jobs", [])]),
            "budget_min": float(budget.get("minimum", 0) or 0),
            "budget_max": float(budget.get("maximum", 0) or 0),
            "budget_type": "fixed" if raw.get("type") == "fixed" else "hourly",
            "client_country": raw.get("owner_location", {}).get("country", {}).get("name"),
            "client_rating": None,
            "client_total_spent": None,
            "proposals_count": int(raw.get("bid_stats", {}).get("bid_count", 0) or 0),
            "duration": None,
            "experience_level": None,
            "url": f"https://www.freelancer.com/projects/{raw.get('seo_url', raw.get('id', ''))}",
        }


class PeoplePerHourClient:
    BASE_URL = "https://api.peopleperhour.com/v1"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_jobs(self, query: str = "", limit: int = 50) -> list[dict[str, Any]]:
        if not settings.PPH_API_KEY:
            logger.warning("PPH API key not configured — skipping")
            return []
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                f"{self.BASE_URL}/workoffer",
                headers={"X-API-Key": settings.PPH_API_KEY},
                params={"q": query, "per_page": limit},
            )
            resp.raise_for_status()
            data = resp.json()
        offers = data.get("data", [])
        return [self._normalize(o) for o in offers]

    @staticmethod
    def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "platform": "pph",
            "platform_job_id": str(raw.get("id", "")),
            "title": raw.get("name", ""),
            "description": raw.get("description", ""),
            "category": raw.get("category_name"),
            "skills_required": str(raw.get("skills", [])),
            "budget_min": float(raw.get("budget", 0) or 0),
            "budget_max": float(raw.get("budget", 0) or 0),
            "budget_type": "fixed",
            "client_country": raw.get("buyer_location"),
            "client_rating": float(raw.get("buyer_rating", 0) or 0),
            "client_total_spent": None,
            "proposals_count": int(raw.get("proposals_count", 0) or 0),
            "duration": raw.get("deadline"),
            "experience_level": None,
            "url": raw.get("url"),
        }
