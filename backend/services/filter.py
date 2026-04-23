"""6-dimensional job scoring: budget, client, category, description, scope, timeline."""
from typing import Any

QUALIFY_THRESHOLD = 60.0

PREFERRED_CATEGORIES = {
    "web development", "mobile development", "api", "backend", "frontend",
    "python", "javascript", "typescript", "react", "node", "data science",
    "machine learning", "ai", "automation", "devops", "cloud",
}

SPAM_KEYWORDS = {"urgent", "asap", "guaranteed", "get rich", "easy money", "100% profit"}


def score_job(job: dict[str, Any]) -> dict[str, Any]:
    s_budget = _score_budget(job)
    s_client = _score_client(job)
    s_category = _score_category(job)
    s_description = _score_description(job)
    s_scope = _score_scope(job)
    s_timeline = _score_timeline(job)

    total = (
        s_budget * 0.25
        + s_client * 0.20
        + s_category * 0.15
        + s_description * 0.20
        + s_scope * 0.10
        + s_timeline * 0.10
    ) * 100

    return {
        "score_budget": round(s_budget, 4),
        "score_client": round(s_client, 4),
        "score_category": round(s_category, 4),
        "score_description": round(s_description, 4),
        "score_scope": round(s_scope, 4),
        "score_timeline": round(s_timeline, 4),
        "score_total": round(total, 2),
        "is_qualified": total >= QUALIFY_THRESHOLD,
    }


def _score_budget(job: dict[str, Any]) -> float:
    bmin = job.get("budget_min") or 0
    bmax = job.get("budget_max") or bmin
    budget = (bmin + bmax) / 2 if bmax else bmin
    if budget <= 0:
        return 0.3
    if budget >= 5000:
        return 1.0
    if budget >= 1000:
        return 0.8
    if budget >= 300:
        return 0.6
    if budget >= 100:
        return 0.4
    return 0.2


def _score_client(job: dict[str, Any]) -> float:
    score = 0.5  # neutral when unknown
    rating = job.get("client_rating")
    if rating is not None:
        score = min(float(rating) / 5.0, 1.0)
    spent = job.get("client_total_spent") or 0
    if spent >= 10000:
        score = min(score + 0.2, 1.0)
    elif spent >= 1000:
        score = min(score + 0.1, 1.0)
    hire_rate = job.get("client_hire_rate")
    if hire_rate and hire_rate >= 0.7:
        score = min(score + 0.1, 1.0)
    return score


def _score_category(job: dict[str, Any]) -> float:
    category = (job.get("category") or "").lower()
    skills = (job.get("skills_required") or "").lower()
    combined = f"{category} {skills}"
    matches = sum(1 for kw in PREFERRED_CATEGORIES if kw in combined)
    if matches >= 3:
        return 1.0
    if matches == 2:
        return 0.8
    if matches == 1:
        return 0.6
    return 0.3


def _score_description(job: dict[str, Any]) -> float:
    desc = (job.get("description") or "").lower()
    if not desc:
        return 0.2
    word_count = len(desc.split())
    spam_hits = sum(1 for kw in SPAM_KEYWORDS if kw in desc)
    if spam_hits:
        return 0.1
    if word_count >= 200:
        return 1.0
    if word_count >= 100:
        return 0.8
    if word_count >= 50:
        return 0.6
    return 0.4


def _score_scope(job: dict[str, Any]) -> float:
    proposals = job.get("proposals_count") or 0
    if proposals == 0:
        return 1.0
    if proposals <= 5:
        return 0.9
    if proposals <= 15:
        return 0.7
    if proposals <= 30:
        return 0.5
    return 0.2


def _score_timeline(job: dict[str, Any]) -> float:
    duration = (job.get("duration") or "").lower()
    if not duration:
        return 0.5
    if any(x in duration for x in ("month", "week")):
        if "1 month" in duration or "less" in duration:
            return 0.7
        return 0.9
    if "hour" in duration or "day" in duration:
        return 0.5
    return 0.6
