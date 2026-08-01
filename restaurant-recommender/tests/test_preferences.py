"""
Unit tests for the UserPreference schema and PreferenceNormalizer.

Covers:
- Validations (location, budget enum, rating clamping)
- Normalisation (lowercase budget, trimming text, canonical locations)
- Edge cases (missing location, unknown location, exceeding max length)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.preferences import PreferenceNormalizer, UserPreference


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def valid_locations() -> list[str]:
    """Sample valid locations from the repository."""
    return ["Indiranagar", "Koramangala", "Banashankari", "Whitefield"]


@pytest.fixture
def normalizer(valid_locations: list[str]) -> PreferenceNormalizer:
    """Configured normalizer with sample locations."""
    return PreferenceNormalizer(valid_locations)


# ── PreferenceNormalizer Tests ───────────────────────────────────────────────


class TestPreferenceNormalizer:
    def test_valid_input(self, normalizer: PreferenceNormalizer) -> None:
        """Valid input should be parsed into a UserPreference model."""
        raw = {
            "location": "Indiranagar",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
            "additional_preferences": "Outdoor seating",
        }
        pref = normalizer.normalize(raw)
        assert pref.location == "Indiranagar"
        assert pref.budget == "medium"
        assert pref.cuisine == "Italian"
        assert pref.min_rating == 4.0
        assert pref.additional_preferences == "Outdoor seating"

    def test_case_insensitive_location(self, normalizer: PreferenceNormalizer) -> None:
        """Location match should be case-insensitive and map to canonical name."""
        raw = {"location": "   iNdIrAnAgAr   ", "budget": "low"}
        pref = normalizer.normalize(raw)
        assert pref.location == "Indiranagar"  # Canonical capitalization

    def test_missing_location(self, normalizer: PreferenceNormalizer) -> None:
        """Missing location should raise ValueError."""
        with pytest.raises(ValueError, match="Location is required"):
            normalizer.normalize({"budget": "low"})

    def test_empty_location(self, normalizer: PreferenceNormalizer) -> None:
        """Empty or whitespace location should raise ValueError."""
        with pytest.raises(ValueError, match="Location is required"):
            normalizer.normalize({"location": "   ", "budget": "low"})

    def test_unknown_location(self, normalizer: PreferenceNormalizer) -> None:
        """Unknown location should raise ValueError listing valid locations."""
        with pytest.raises(ValueError) as exc_info:
            normalizer.normalize({"location": "New York", "budget": "low"})
        msg = str(exc_info.value)
        assert "Unknown location 'New York'" in msg
        assert "Banashankari, Indiranagar, Koramangala, Whitefield" in msg


# ── UserPreference Field Validators ──────────────────────────────────────────


class TestUserPreferenceValidators:
    def test_budget_enum(self) -> None:
        """Budget must be one of 'low', 'medium', 'high'."""
        pref = UserPreference(location="A", budget="HIGH")
        assert pref.budget == "high"  # Case-normalized
        
        pref = UserPreference(location="A", budget="   medium   ")
        assert pref.budget == "medium"  # Stripped

        with pytest.raises(ValidationError):
            UserPreference(location="A", budget="cheap")

    def test_rating_clamp(self) -> None:
        """min_rating should be clamped to [0.0, 5.0]."""
        assert UserPreference(location="A", budget="low", min_rating=6.5).min_rating == 5.0
        assert UserPreference(location="A", budget="low", min_rating=-2.0).min_rating == 0.0
        assert UserPreference(location="A", budget="low", min_rating="3.5").min_rating == 3.5

    def test_rating_invalid_string(self) -> None:
        """Unparseable min_rating falls back to 0.0."""
        pref = UserPreference(location="A", budget="low", min_rating="five")
        assert pref.min_rating == 0.0

    def test_cuisine_trim(self) -> None:
        """Cuisine string should be trimmed, and empty strings become None."""
        assert UserPreference(location="A", budget="low", cuisine="  Italian  ").cuisine == "Italian"
        assert UserPreference(location="A", budget="low", cuisine="   ").cuisine is None
        assert UserPreference(location="A", budget="low", cuisine=None).cuisine is None

    def test_additional_preferences_trim_and_cap(self) -> None:
        """additional_preferences should be trimmed, empty -> None, and capped at 500 chars."""
        # Trim
        pref = UserPreference(location="A", budget="low", additional_preferences="  Quiet place  ")
        assert pref.additional_preferences == "Quiet place"
        
        # Empty string
        pref2 = UserPreference(location="A", budget="low", additional_preferences="   ")
        assert pref2.additional_preferences is None
        
        # Max length cap (500 chars)
        long_str = "x" * 600
        pref3 = UserPreference(location="A", budget="low", additional_preferences=long_str)
        assert len(pref3.additional_preferences) == 500
        assert pref3.additional_preferences == "x" * 500
