"""
Restaurant data model.

Defines the canonical ``Restaurant`` schema used throughout the application.
Raw Zomato dataset records are normalised into this model by the Preprocessor.

Maps to: Architecture §3.1 — Extracted fields (minimum).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


BudgetTier = Literal["low", "medium", "high"]


class Restaurant(BaseModel):
    """A single restaurant record after preprocessing."""

    restaurant_id: int = Field(
        ...,
        description="Unique identifier (row index from the dataset).",
    )
    restaurant_name: str = Field(
        ...,
        description="Display name of the restaurant.",
    )
    location: str = Field(
        ...,
        description="Normalised locality / area name (e.g. 'Banashankari').",
    )
    cuisines: list[str] = Field(
        default_factory=list,
        description="List of cuisines served (normalised, trimmed).",
    )
    average_cost_for_two: int = Field(
        ...,
        ge=0,
        description="Approximate cost for two people in INR.",
    )
    budget_tier: BudgetTier = Field(
        ...,
        description="Derived budget tier: 'low' ≤ 500, 'medium' 501–1500, 'high' > 1500.",
    )
    rating: float = Field(
        ...,
        ge=0.0,
        le=5.0,
        description="Aggregate rating on a 0.0–5.0 scale.",
    )
    votes: int = Field(
        default=0,
        ge=0,
        description="Total number of votes / reviews.",
    )
    address: str | None = Field(
        default=None,
        description="Full street address (optional, for display).",
    )
    online_order: bool = Field(
        default=False,
        description="Whether the restaurant accepts online orders.",
    )
    book_table: bool = Field(
        default=False,
        description="Whether table booking is available.",
    )
    restaurant_type: str | None = Field(
        default=None,
        description="Type of restaurant (e.g. 'Casual Dining', 'Quick Bites').",
    )
    url: str | None = Field(
        default=None,
        description="Zomato listing URL.",
    )

    # ── Validators ───────────────────────────────────────────────────────

    @field_validator("cuisines", mode="before")
    @classmethod
    def _parse_cuisines(cls, v: object) -> list[str]:
        """Accept a comma-separated string or an existing list."""
        if isinstance(v, str):
            return [c.strip() for c in v.split(",") if c.strip()]
        if isinstance(v, list):
            return [str(c).strip() for c in v if str(c).strip()]
        return []

    @field_validator("rating", mode="before")
    @classmethod
    def _clamp_rating(cls, v: object) -> float:
        """Clamp rating to [0.0, 5.0]."""
        try:
            val = float(v)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(5.0, val))
