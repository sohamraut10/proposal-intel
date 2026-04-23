"""6-dimensional job qualification scoring.

Each dimension returns (passed: bool, score: 0-100, detail: str).
All 6 must pass for a job to be QUALIFIED.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from config import get_settings

settings = get_settings()

# ── Qualification tiers ────────────────────────────────────────────────────
TIER_EXCELLENT = 80   # all pass, avg ≥ 80 → 95 qualification score
TIER_GOOD      = 70   # all pass, avg ≥ 70 → 80 qualification score
TIER_FAIR      = 60   # some fail, avg ≥ 60 → 60 qualification score
TIER_POOR      = 30   # some fail, avg ≥ 30 → 30 qualification score
# below 30 → REJECTED (0)


@dataclass
class DimensionResult:
    name: str
    passed: bool
    score: int          # 0-100
    detail: str


@dataclass
class QualificationResult:
    is_qualified: bool
    score: int          # 0-100 overall
    tier: str           # EXCELLENT | GOOD | FAIR | POOR | REJECTED
    reasoning: str
    details: dict[str, Any] = field(default_factory=dict)
    dimension_scores: dict[str, int] = field(default_factory=dict)


class JobFilter:

    def qualify_job(self, job: dict[str, Any]) -> QualificationResult:
        dims = [
            self._check_budget(job),
            self._check_client(job),
            self._check_category(job),
            self._check_description(job),
            self._check_scope(job),
            self._check_timeline(job),
        ]

        all_pass = all(d.passed for d in dims)
        avg_score = int(sum(d.score for d in dims) / len(dims))

        if all_pass and avg_score >= TIER_EXCELLENT:
            tier, qual_score = "EXCELLENT", 95
        elif all_pass and avg_score >= TIER_GOOD:
            tier, qual_score = "GOOD", 80
        elif avg_score >= TIER_FAIR:
            tier, qual_score = "FAIR", 60
        elif avg_score >= TIER_POOR:
            tier, qual_score = "POOR", 30
        else:
            tier, qual_score = "REJECTED", 0

        is_qualified = all_pass and avg_score >= TIER_GOOD

        failed = [d.name for d in dims if not d.passed]
        reasoning_parts = [f"{d.name}: {d.detail}" for d in dims]
        reasoning = " | ".join(reasoning_parts)
        if failed:
            reasoning = f"Failed: {', '.join(failed)}. " + reasoning

        return QualificationResult(
            is_qualified=is_qualified,
            score=qual_score,
            tier=tier,
            reasoning=reasoning,
            details={d.name: {"passed": d.passed, "score": d.score, "detail": d.detail} for d in dims},
            dimension_scores={d.name: d.score for d in dims},
        )

    # ── 1. Budget ──────────────────────────────────────────────────────────
    def _check_budget(self, job: dict[str, Any]) -> DimensionResult:
        bmin = job.get("budget_min") or 0
        bmax = job.get("budget_max") or bmin
        budget = (bmin + bmax) / 2 if bmax else bmin

        if budget <= 0:
            return DimensionResult("budget", False, 20, "No budget specified")
        if budget < settings.MIN_BUDGET_USD:
            return DimensionResult("budget", False, 10,
                                   f"${budget:.0f} below minimum ${settings.MIN_BUDGET_USD:.0f}")
        if budget > settings.MAX_BUDGET_USD:
            return DimensionResult("budget", False, 30,
                                   f"${budget:.0f} above maximum ${settings.MAX_BUDGET_USD:.0f}")

        # sweet spot $200–$2,000
        if 200 <= budget <= 2000:
            score = 95
        elif 100 <= budget < 200 or 2000 < budget <= 5000:
            score = 75
        else:
            score = 55

        return DimensionResult("budget", True, score,
                               f"${budget:.0f} ({job.get('budget_type', 'fixed')})")

    # ── 2. Client ──────────────────────────────────────────────────────────
    def _check_client(self, job: dict[str, Any]) -> DimensionResult:
        rating = job.get("client_rating")
        jobs_posted = job.get("client_jobs_posted") or job.get("proposals_count") or 0

        # Hard fails
        if rating is not None and rating < 3.5:
            return DimensionResult("client", False, 20,
                                   f"Rating {rating:.1f} too low (min 3.5)")
        if jobs_posted < settings.MIN_CLIENT_JOBS_POSTED:
            return DimensionResult("client", False, 25,
                                   f"Only {jobs_posted} jobs posted (min {settings.MIN_CLIENT_JOBS_POSTED})")

        # Score rating
        if rating is None:
            rating_score = 50
        elif rating >= 4.5:
            rating_score = 100
        elif rating >= 4.0:
            rating_score = 70
        else:
            rating_score = 45

        # Score jobs posted
        if jobs_posted >= 20:
            jobs_score = 100
        elif jobs_posted >= 10:
            jobs_score = 80
        elif jobs_posted >= 5:
            jobs_score = 60
        else:
            jobs_score = 40

        score = int((rating_score + jobs_score) / 2)
        rating_str = f"{rating:.1f}★" if rating else "unrated"
        return DimensionResult("client", True, score,
                               f"{rating_str}, {jobs_posted} jobs posted")

    # ── 3. Category ────────────────────────────────────────────────────────
    def _check_category(self, job: dict[str, Any]) -> DimensionResult:
        category = (job.get("category") or "").lower()
        title = (job.get("title") or "").lower()
        skills = job.get("skills_required")
        if isinstance(skills, list):
            skills_str = " ".join(skills).lower()
        else:
            skills_str = (skills or "").lower()

        combined = f"{category} {title} {skills_str}"

        # Check disqualifying keywords first
        for kw in settings.DISQUALIFYING_KEYWORDS:
            if kw in combined:
                return DimensionResult("category", False, 10,
                                       f"Disqualifying keyword: '{kw}'")

        # Check qualified categories
        matches = [kw for kw in settings.QUALIFIED_CATEGORIES if kw in combined]
        if len(matches) >= 3:
            return DimensionResult("category", True, 100,
                                   f"Strong match: {', '.join(matches[:3])}")
        if len(matches) == 2:
            return DimensionResult("category", True, 85,
                                   f"Good match: {', '.join(matches)}")
        if len(matches) == 1:
            return DimensionResult("category", True, 65,
                                   f"Partial match: {matches[0]}")

        return DimensionResult("category", False, 40,
                               f"No qualified category match (category='{category}')")

    # ── 4. Description ─────────────────────────────────────────────────────
    def _check_description(self, job: dict[str, Any]) -> DimensionResult:
        desc = (job.get("description") or "").lower()
        if not desc:
            return DimensionResult("description", False, 20, "No description")

        score = 60
        notes = []

        word_count = len(desc.split())
        if word_count >= 200:
            score += 15
            notes.append(f"{word_count} words")
        elif word_count < 50:
            score -= 20
            notes.append(f"too short ({word_count} words)")

        if any(w in desc for w in ("specific", "exact", "precisely")):
            score += 10
            notes.append("specific requirements")
        if any(w in desc for w in ("complex", "difficult", "advanced")):
            score -= 20
            notes.append("complex scope")
        if any(w in desc for w in ("urgent", "asap", "immediately")):
            score -= 10
            notes.append("urgency flag")
        if any(w in desc for w in ("3d", "video", "design", "photoshop", "illustrator")):
            score -= 30
            notes.append("design/video keywords")

        score = max(20, min(100, score))
        passed = score >= 40
        detail = ", ".join(notes) if notes else f"{word_count} words"
        return DimensionResult("description", passed, score, detail)

    # ── 5. Scope ───────────────────────────────────────────────────────────
    def _check_scope(self, job: dict[str, Any]) -> DimensionResult:
        duration = (job.get("duration") or "").lower()
        level = (job.get("level") or job.get("experience_level") or "").lower()
        proposals = job.get("proposals_count") or 0

        # Score by competition (proposals count)
        if proposals == 0:
            scope_score = 100
        elif proposals <= 5:
            scope_score = 90
        elif proposals <= 15:
            scope_score = 70
        elif proposals <= 30:
            scope_score = 50
        else:
            scope_score = 20

        # Adjust by duration
        if any(x in duration for x in ("less-than-1-month", "2-3-weeks", "week")):
            scope_score = min(scope_score + 10, 100)
            dur_note = "short"
        elif "1-to-3-months" in duration or "1 to 3 months" in duration:
            dur_note = "medium"
        elif any(x in duration for x in ("3-to-6", "6 month", "ongoing")):
            scope_score = max(scope_score - 20, 0)
            dur_note = "long"
        else:
            dur_note = duration or "unspecified"

        # Adjust by level
        if "expert" in level:
            scope_score = max(scope_score - 10, 0)

        passed = scope_score >= 40
        return DimensionResult("scope", passed, scope_score,
                               f"{proposals} bids, {dur_note} duration, {level or 'any'} level")

    # ── 6. Timeline / Freshness ────────────────────────────────────────────
    def _check_timeline(self, job: dict[str, Any]) -> DimensionResult:
        posted_at = job.get("posted_at")
        if not posted_at:
            return DimensionResult("timeline", True, 50, "Post time unknown")

        if isinstance(posted_at, str):
            try:
                from datetime import datetime as dt
                posted_at = dt.fromisoformat(posted_at.replace("Z", "+00:00"))
            except ValueError:
                return DimensionResult("timeline", True, 50, "Could not parse post time")

        now = datetime.now(timezone.utc)
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)

        age_minutes = (now - posted_at).total_seconds() / 60

        if age_minutes <= 30:
            score, label = 100, "<30 min ago"
        elif age_minutes <= 120:
            score, label = 85, "<2 hrs ago"
        elif age_minutes <= 1440:
            score, label = 70, "<24 hrs ago"
        else:
            score, label = 30, f"{age_minutes/1440:.1f} days ago"

        passed = score >= 50
        return DimensionResult("timeline", passed, score, label)

    # ── Bulk operations ────────────────────────────────────────────────────
    def bulk_qualify(
        self, jobs: list[dict[str, Any]], min_score: int = 70
    ) -> list[tuple[dict[str, Any], QualificationResult]]:
        results = [(job, self.qualify_job(job)) for job in jobs]
        results = [(j, r) for j, r in results if r.score >= min_score]
        results.sort(key=lambda x: x[1].score, reverse=True)
        return results

    def recommend_priority(
        self, qualified_jobs: list[tuple[dict[str, Any], QualificationResult]]
    ) -> list[tuple[dict[str, Any], QualificationResult, float]]:
        """Re-rank qualified jobs by win probability.

        Priority = score * budget_multiplier * rating_multiplier * freshness_multiplier
        """
        ranked = []
        for job, result in qualified_jobs:
            priority = result.score

            # Budget fit multiplier (1.3× for sweet-spot $300–$2,000)
            bmin = job.get("budget_min") or 0
            bmax = job.get("budget_max") or bmin
            budget = (bmin + bmax) / 2
            if 300 <= budget <= 2000:
                priority *= 1.3

            # Client rating multiplier
            rating = job.get("client_rating")
            if rating and rating >= 4.5:
                priority *= 1.2

            # Freshness multiplier (decays over 24 hours, max 1.5×)
            posted_at = job.get("posted_at")
            if posted_at:
                if isinstance(posted_at, str):
                    try:
                        posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
                    except ValueError:
                        posted_at = None
                if posted_at:
                    if posted_at.tzinfo is None:
                        posted_at = posted_at.replace(tzinfo=timezone.utc)
                    age_hours = (datetime.now(timezone.utc) - posted_at).total_seconds() / 3600
                    freshness = max(1.0, 1.5 * math.exp(-age_hours / 6))
                    priority *= freshness

            ranked.append((job, result, round(priority, 2)))

        ranked.sort(key=lambda x: x[2], reverse=True)
        return ranked


# Module-level singleton
_filter = JobFilter()


def score_job(job: dict[str, Any]) -> dict[str, Any]:
    """Return score fields dict suitable for DB upsert."""
    result = _filter.qualify_job(job)
    dims = result.details
    return {
        "score_budget":      dims.get("budget", {}).get("score", 0) / 100,
        "score_client":      dims.get("client", {}).get("score", 0) / 100,
        "score_category":    dims.get("category", {}).get("score", 0) / 100,
        "score_description": dims.get("description", {}).get("score", 0) / 100,
        "score_scope":       dims.get("scope", {}).get("score", 0) / 100,
        "score_timeline":    dims.get("timeline", {}).get("score", 0) / 100,
        "score_total":       float(result.score),
        "score_reasoning":   result.reasoning,
        "is_qualified":      result.is_qualified,
    }
