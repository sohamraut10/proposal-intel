from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/proposal_intel"
    JOB_RETENTION_DAYS: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Google OAuth
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""

    # Claude / Anthropic
    ANTHROPIC_API_KEY: str = ""
    PROPOSAL_MODEL: str = "claude-sonnet-4-6"
    PROPOSAL_MAX_TOKENS: int = 500
    PROPOSAL_TEMPERATURE: float = 0.7
    ANTHROPIC_API_RATE_LIMIT: int = 30  # req/min

    # Upwork
    UPWORK_API_KEY: str = ""
    UPWORK_API_SECRET: str = ""
    UPWORK_API_RATE_LIMIT: int = 20  # req/min

    # Freelancer
    FREELANCER_API_KEY: str = ""
    FREELANCER_API_RATE_LIMIT: int = 10  # req/min

    # PeoplePerHour
    PPH_API_KEY: str = ""

    # Scheduler
    AGGREGATION_INTERVAL_SECONDS: int = 300  # 5 minutes

    # Job filtering thresholds
    MIN_BUDGET_USD: float = 50.0
    MAX_BUDGET_USD: float = 50000.0
    MIN_CLIENT_RATING: float = 4.0
    MIN_CLIENT_JOBS_POSTED: int = 3

    # Qualified categories (comma-separated in env, list here as default)
    QUALIFIED_CATEGORIES: List[str] = [
        "writing", "copywriting", "content-writing", "data-entry", "translation",
        "proofreading", "editing", "scripting", "python", "javascript",
        "web-development", "web development", "backend", "frontend", "api",
        "data science", "machine learning", "ai", "automation", "devops", "cloud",
        "node", "react", "typescript",
    ]

    # Disqualifying keywords in title/description
    DISQUALIFYING_KEYWORDS: List[str] = [
        "design", "logo", "illustration", "video editing", "3d model",
        "ui/ux", "app development", "saas", "enterprise", "long-term",
        "permanent", "full-time",
    ]

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
