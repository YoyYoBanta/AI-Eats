"""
Centralized application configuration.

Loads settings from environment variables (and `.env` file) using pydantic-settings.
All configuration variables from architecture §8 are defined here with their defaults.

Usage:
    from config.settings import settings

    print(settings.LLM_MODEL)
    print(settings.GROQ_API_KEY.get_secret_value())
"""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Hugging Face Dataset ─────────────────────────────────────────────
    HF_DATASET_NAME: str = Field(
        default="ManikaSaini/zomato-restaurant-recommendation",
        description="Hugging Face dataset identifier.",
    )

    # ── LLM Provider (Groq) ─────────────────────────────────────────────
    LLM_PROVIDER: str = Field(
        default="groq",
        description="LLM provider — fixed to 'groq' for this project.",
    )

    LLM_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model identifier for chat completions.",
    )

    GROQ_API_KEY: SecretStr = Field(
        default=SecretStr(""),
        description="Groq API key. Obtain from https://console.groq.com/keys.",
    )

    LLM_TIMEOUT_SECONDS: int = Field(
        default=30,
        ge=1,
        description="Groq API call timeout in seconds.",
    )

    # ── Recommendation Tuning ────────────────────────────────────────────
    MAX_CANDIDATES: int = Field(
        default=50,
        ge=1,
        description="Maximum restaurants sent to the LLM context window.",
    )

    TOP_K_RESULTS: int = Field(
        default=5,
        ge=1,
        description="Number of top recommendations returned to the user.",
    )

    # ── Budget Tier Thresholds (INR) ─────────────────────────────────────
    BUDGET_LOW_MAX: int = Field(
        default=500,
        ge=0,
        description="Upper bound for the 'low' budget tier (cost for two, INR).",
    )

    BUDGET_MEDIUM_MAX: int = Field(
        default=1500,
        ge=0,
        description="Upper bound for the 'medium' budget tier (cost for two, INR).",
    )

    # ── Feature Flags ────────────────────────────────────────────────────
    ENABLE_FALLBACK_RANKER: bool = Field(
        default=True,
        description="Use rule-based fallback ranking when Groq call fails.",
    )


# Singleton instance — import this throughout the application.
settings = Settings()
