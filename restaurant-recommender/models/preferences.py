"""
User preference models and normalisation logic.

Defines the typed schema for user inputs and logic to validate
inputs against the dataset's valid locations.

Maps to: Architecture §3.2 — User Input Layer.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from models.restaurant import BudgetTier


class UserPreference(BaseModel):
    """Validated user preferences for the recommendation engine."""

    location: str = Field(
        ...,
        description="Target location/neighbourhood. Must match a known location in the dataset.",
    )
    budget: BudgetTier = Field(
        ...,
        description="Budget tier: 'low', 'medium', or 'high'.",
    )
    cuisine: str | None = Field(
        default=None,
        description="Preferred cuisine (partial match).",
    )
    min_rating: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Minimum acceptable rating (0.0 to 5.0).",
    )
    additional_preferences: str | None = Field(
        default=None,
        max_length=500,
        description="Free-text preferences, capped at 500 characters to prevent prompt injection/bloat.",
    )

    # ── Field Validators ──────────────────────────────────────────────────

    @field_validator("min_rating", mode="before")
    @classmethod
    def _clamp_rating(cls, v: Any) -> float:
        """Ensure min_rating is a float clamped between 0.0 and 5.0."""
        try:
            val = float(v)
            return max(0.0, min(5.0, val))
        except (TypeError, ValueError):
            return 0.0

    @field_validator("cuisine", mode="before")
    @classmethod
    def _normalize_cuisine(cls, v: Any) -> str | None:
        """Trim whitespace from cuisine."""
        if not v:
            return None
        val = str(v).strip()
        return val if val else None

    @field_validator("additional_preferences", mode="before")
    @classmethod
    def _sanitize_preferences(cls, v: Any) -> str | None:
        """Trim and cap additional preferences to 500 characters."""
        if not v:
            return None
        sanitized = str(v).strip()
        if len(sanitized) > 500:
            sanitized = sanitized[:500]
        return sanitized if sanitized else None

    @field_validator("budget", mode="before")
    @classmethod
    def _normalize_budget(cls, v: Any) -> str:
        """Ensure budget is lowercase for enum matching."""
        if isinstance(v, str):
            return v.strip().lower()
        return str(v)


class PreferenceNormalizer:
    """Validates raw user inputs against domain rules (e.g. valid locations).

    Parameters
    ----------
    valid_locations:
        List of allowed locations from the repository. Used to validate
        the user's location input.
    """

    def __init__(self, valid_locations: list[str]) -> None:
        # Create a case-insensitive lookup map: lower() -> canonical
        self.valid_locations = {loc.lower(): loc for loc in valid_locations}

    def normalize(self, raw_input: dict[str, Any]) -> UserPreference:
        """Validate and normalize raw input dictionary into a ``UserPreference``.

        Parameters
        ----------
        raw_input:
            Dictionary containing user inputs (e.g. from a web form).

        Returns
        -------
        UserPreference
            Validated preference model.

        Raises
        ------
        ValueError
            If the location is missing or unknown.
        pydantic.ValidationError
            If other fields fail Pydantic validation (e.g. invalid budget).
        """
        raw_location = raw_input.get("location")
        if not raw_location or not str(raw_location).strip():
            raise ValueError("Location is required.")

        loc_key = str(raw_location).strip().lower()
        if loc_key not in self.valid_locations:
            valid_list = ", ".join(sorted(self.valid_locations.values()))
            raise ValueError(
                f"Unknown location '{raw_location}'. Valid locations are: {valid_list}"
            )

        # Overwrite with canonical case
        canonical_loc = self.valid_locations[loc_key]
        normalized_data = dict(raw_input)
        normalized_data["location"] = canonical_loc

        # Let Pydantic handle the rest of the validation (budget, rating, etc.)
        return UserPreference(**normalized_data)
