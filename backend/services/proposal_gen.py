"""OpenAI proposal generation — strategies, bid calculation, win probability."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """You are {name}, a skilled freelancer with expertise in {skills}.
Your task is to write conversion-optimized proposals that:
1. Address client's specific pain points (not generic)
2. Demonstrate clear understanding of project scope
3. Highlight relevant past experience
4. Build trust through specificity
5. Include clear timeline and deliverables

CONSTRAINTS:
- Keep under 350 words
- Use "I" statements (personal voice)
- Avoid jargon unless client used it
- Lead with strongest relevant skill
- Always end with call-to-action
- Be honest (never overpromise)

{strategy_modifier}"""

STRATEGY_MODIFIERS = {
    "standard": "STRATEGY: Balanced approach — professional tone, fair pricing, universal appeal.",
    "aggressive": (
        "STRATEGY: Aggressive — lead with 'I'm the perfect fit' energy. "
        "Emphasise strengths, slightly undercut market rate, confident close."
    ),
    "cautious": (
        "STRATEGY: Cautious — 'Let's discuss details' energy. "
        "Premium positioning, risk mitigation, conservative delivery estimates."
    ),
}

USER_PROMPT_TEMPLATE = """PROJECT: {title}
Budget: ${budget_min}-${budget_max} ({budget_type})
Client: {client_name} ({client_rating}⭐, {client_jobs_posted} jobs)
Category: {category}
Duration: {duration}
Level: {level}

DESCRIPTION:
{description}

FREELANCER PROFILE:
Name: {name}
Headline: {headline}
Bio: {bio}
Skills: {skills}
Certifications: {certifications}

RELEVANT PAST PROJECTS:
{past_projects}

TASK: Write a compelling, personalised proposal. Respond with valid JSON only:
{{
  "cover_letter": "...",
  "proposal": "...",
  "approach": "...",
  "strengths": ["...", "..."]
}}"""


class ProposalGenerator:

    def __init__(self) -> None:
        self.model = settings.PROPOSAL_MODEL
        self.max_tokens = settings.PROPOSAL_MAX_TOKENS
        self.temperature = settings.PROPOSAL_TEMPERATURE

    async def generate_proposal(
        self,
        job: dict[str, Any],
        freelancer_profile: dict[str, Any],
        strategy: str = "standard",
    ) -> dict[str, Any]:
        strategy = strategy if strategy in STRATEGY_MODIFIERS else "standard"
        system_content = SYSTEM_PROMPT.format(
            name=freelancer_profile.get("name") or freelancer_profile.get("full_name") or "Freelancer",
            skills=_format_skills(freelancer_profile),
            strategy_modifier=STRATEGY_MODIFIERS[strategy],
        )
        user_content = self._build_user_prompt(job, freelancer_profile)

        response = await client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
        )

        raw = response.choices[0].message.content or ""
        parsed = self._parse_proposal(raw)
        tokens = response.usage.total_tokens if response.usage else 0

        bid_amount = self._calculate_bid(job, freelancer_profile, strategy)
        win_probability = self._estimate_win_probability(job, freelancer_profile)
        quality_score = self._estimate_quality_score(parsed)

        logger.info(
            "Proposal generated — strategy=%s tokens=%d win_prob=%.0f%%",
            strategy, tokens, win_probability * 100,
        )
        return {
            "proposal_text": parsed.get("proposal", raw),
            "cover_letter": parsed.get("cover_letter"),
            "approach": parsed.get("approach"),
            "highlighted_strengths": parsed.get("strengths", []),
            "bid_amount": bid_amount,
            "currency": job.get("currency", "USD"),
            "strategy": strategy,
            "quality_score": quality_score,
            "win_probability": win_probability,
            "estimated_response_time": "10-15 min",
            "model_used": response.model,
            "tokens_used": tokens,
        }

    async def generate_batch(
        self,
        jobs: list[dict[str, Any]],
        freelancer_profile: dict[str, Any],
        max_proposals: int = 10,
        strategy: str = "standard",
    ) -> list[dict[str, Any]]:
        jobs = jobs[:max_proposals]
        semaphore = asyncio.Semaphore(3)

        async def _generate(job: dict[str, Any]) -> dict[str, Any] | None:
            async with semaphore:
                try:
                    result = await self.generate_proposal(job, freelancer_profile, strategy)
                    result["job_id"] = job.get("id")
                    return result
                except Exception as exc:
                    logger.error("Batch generation failed for job %s: %s", job.get("id"), exc)
                    return None

        results = await asyncio.gather(*[_generate(j) for j in jobs])
        return [r for r in results if r is not None]

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _build_user_prompt(self, job: dict[str, Any], profile: dict[str, Any]) -> str:
        past = profile.get("past_projects") or []
        if isinstance(past, list):
            past_str = "\n".join(
                f"- {p.get('title', 'Project')}: {p.get('description', '')}" for p in past[:3]
            ) or "No past projects listed"
        else:
            past_str = str(past)

        return USER_PROMPT_TEMPLATE.format(
            title=job.get("title", "N/A"),
            budget_min=job.get("budget_min") or 0,
            budget_max=job.get("budget_max") or 0,
            budget_type=job.get("budget_type", "fixed"),
            client_name=job.get("client_name", "Client"),
            client_rating=job.get("client_rating") or "N/A",
            client_jobs_posted=job.get("client_jobs_posted") or "N/A",
            category=job.get("category", "N/A"),
            duration=job.get("duration", "N/A"),
            level=job.get("level") or job.get("experience_level") or "N/A",
            description=job.get("description") or "No description provided",
            name=profile.get("name") or profile.get("full_name") or "Freelancer",
            headline=profile.get("headline") or "Freelancer",
            bio=profile.get("bio") or "N/A",
            skills=_format_skills(profile),
            certifications=", ".join(profile.get("certifications") or []) or "N/A",
            past_projects=past_str,
        )

    @staticmethod
    def _parse_proposal(raw: str) -> dict[str, Any]:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"proposal": raw, "cover_letter": None, "approach": None, "strengths": []}

    @staticmethod
    def _calculate_bid(
        job: dict[str, Any],
        profile: dict[str, Any],
        strategy: str,
    ) -> float | None:
        hourly_rate = profile.get("hourly_rate")
        estimated_hours = profile.get("estimated_hours_per_project")
        bmin = job.get("budget_min") or 0
        bmax = job.get("budget_max") or bmin
        market_mid = (bmin + bmax) / 2 if bmax else bmin

        if not market_mid:
            return None

        cost = hourly_rate * estimated_hours if (hourly_rate and estimated_hours) else market_mid

        if strategy == "aggressive":
            bid = min(cost * 0.9, market_mid)
        elif strategy == "cautious":
            bid = max(cost * 1.1, bmin)
        else:
            bid = max(bmin, min(cost, market_mid))

        return round(bid / 5) * 5

    @staticmethod
    def _estimate_win_probability(job: dict[str, Any], profile: dict[str, Any]) -> float:
        prob = 0.50

        bmin = job.get("budget_min") or 0
        bmax = job.get("budget_max") or bmin
        hourly = profile.get("hourly_rate") or 0
        if hourly and bmin <= hourly <= bmax:
            prob += 0.15

        rating = job.get("client_rating")
        if rating and rating >= 4.5:
            prob += 0.10

        posted_at = job.get("posted_at")
        if posted_at:
            from datetime import datetime, timezone
            if isinstance(posted_at, str):
                try:
                    posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
                except ValueError:
                    posted_at = None
            if posted_at:
                if posted_at.tzinfo is None:
                    posted_at = posted_at.replace(tzinfo=timezone.utc)
                age_hours = (datetime.now(timezone.utc) - posted_at).total_seconds() / 3600
                if age_hours <= 1:
                    prob += 0.15
                elif age_hours <= 6:
                    prob += 0.05

        return min(prob, 0.95)

    @staticmethod
    def _estimate_quality_score(parsed: dict[str, Any]) -> int:
        score = 60
        proposal = parsed.get("proposal") or ""
        if len(proposal.split()) >= 150:
            score += 15
        if parsed.get("cover_letter"):
            score += 10
        if parsed.get("approach"):
            score += 10
        if len(parsed.get("strengths") or []) >= 2:
            score += 5
        return min(score, 100)


def _format_skills(profile: dict[str, Any]) -> str:
    skills = profile.get("skills")
    if isinstance(skills, list):
        return ", ".join(skills)
    return str(skills or "N/A")


_generator = ProposalGenerator()


async def generate_proposal(
    job: dict[str, Any],
    freelancer_profile: dict[str, Any],
    strategy: str = "standard",
) -> dict[str, Any]:
    return await _generator.generate_proposal(job, freelancer_profile, strategy)


async def generate_batch(
    jobs: list[dict[str, Any]],
    freelancer_profile: dict[str, Any],
    max_proposals: int = 10,
    strategy: str = "standard",
) -> list[dict[str, Any]]:
    return await _generator.generate_batch(jobs, freelancer_profile, max_proposals, strategy)
