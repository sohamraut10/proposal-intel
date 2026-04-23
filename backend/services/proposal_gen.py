"""Claude API proposal generation with prompt caching."""
import logging
from typing import Any

import anthropic

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are an expert freelance proposal writer with 10+ years of experience winning high-value contracts on Upwork, Freelancer, and PeoplePerHour.

Your proposals are:
- Concise (250-400 words)
- Client-centric: lead with their problem, not your credentials
- Specific: reference details from the job description
- Credible: include 1-2 relevant past wins or skills
- Action-oriented: end with a clear next step

Do not use generic openers like "I saw your job posting" or "I am interested in your project".
Format: plain text, no markdown headers, natural paragraphs."""


async def generate_proposal(
    job: dict[str, Any],
    user_profile: dict[str, Any],
) -> dict[str, str | int]:
    """Generate a proposal for a job using Claude with prompt caching.

    Returns dict with keys: content, cover_letter, model_used, tokens_used.
    """
    job_context = _format_job(job)
    profile_context = _format_profile(user_profile)

    message = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Freelancer profile:\n{profile_context}\n\n"
                    f"Job details:\n{job_context}\n\n"
                    "Write a winning proposal for this job."
                ),
            }
        ],
    )

    content = message.content[0].text
    tokens = message.usage.input_tokens + message.usage.output_tokens

    cover_letter = await _generate_cover_letter(job_context, profile_context, content)

    logger.info("Proposal generated — model=%s tokens=%d", message.model, tokens)
    return {
        "content": content,
        "cover_letter": cover_letter,
        "model_used": message.model,
        "tokens_used": tokens,
    }


async def _generate_cover_letter(
    job_context: str,
    profile_context: str,
    proposal: str,
) -> str:
    message = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=300,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Freelancer profile:\n{profile_context}\n\n"
                    f"Job details:\n{job_context}\n\n"
                    f"Full proposal:\n{proposal}\n\n"
                    "Write a 2-sentence cover letter summary for the platform's subject line / intro field."
                ),
            }
        ],
    )
    return message.content[0].text


def _format_job(job: dict[str, Any]) -> str:
    lines = [
        f"Title: {job.get('title', 'N/A')}",
        f"Platform: {job.get('platform', 'N/A')}",
        f"Category: {job.get('category', 'N/A')}",
        f"Budget: ${job.get('budget_min', 0)}–${job.get('budget_max', 0)} ({job.get('budget_type', 'N/A')})",
        f"Duration: {job.get('duration', 'N/A')}",
        f"Experience level: {job.get('experience_level', 'N/A')}",
        f"Skills required: {job.get('skills_required', 'N/A')}",
        f"Description:\n{job.get('description', 'No description provided')}",
    ]
    return "\n".join(lines)


def _format_profile(profile: dict[str, Any]) -> str:
    lines = [
        f"Name: {profile.get('full_name', 'N/A')}",
        f"Skills: {profile.get('skills', 'N/A')}",
        f"Hourly rate: ${profile.get('hourly_rate', 'N/A')}",
        f"Bio: {profile.get('bio', 'N/A')}",
    ]
    return "\n".join(lines)
