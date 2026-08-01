"""
Unit tests for the data ingestion preprocessor.

Covers:
- Rating parsing (normal, NEW, -, NaN, edge cases)
- Cost parsing (normal, comma-separated, non-numeric)
- Budget tier derivation (low / medium / high boundaries)
- Location normalisation (trim, title-case, alias mapping)
- Yes/No boolean parsing
- Full preprocessing pipeline on synthetic data
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

from data.ingestion.preprocessor import Preprocessor


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_settings() -> MagicMock:
    """Create a mock Settings object with default budget thresholds."""
    settings = MagicMock()
    settings.BUDGET_LOW_MAX = 500
    settings.BUDGET_MEDIUM_MAX = 1500
    return settings


@pytest.fixture()
def preprocessor(mock_settings: MagicMock) -> Preprocessor:
    """Create a Preprocessor instance with mock settings."""
    return Preprocessor(settings=mock_settings)


@pytest.fixture()
def sample_raw_df() -> pd.DataFrame:
    """Create a minimal raw DataFrame mimicking the HF dataset schema."""
    return pd.DataFrame(
        {
            "url": [
                "https://zomato.com/test1",
                "https://zomato.com/test2",
                "https://zomato.com/test3",
            ],
            "name": ["Test Restaurant", "Another Place", "Third Spot"],
            "address": ["123 Main St", "456 Oak Ave", "789 Elm Rd"],
            "location": ["Banashankari", "  koramangala  ", "Bengaluru"],
            "cuisines": [
                "North Indian, Chinese",
                "Italian, Pizza",
                "South Indian",
            ],
            "approx_cost(for two people)": ["800", "300", "2,000"],
            "rate": ["4.1/5", "3.5/5", "NEW"],
            "votes": [100, 50, 0],
            "online_order": ["Yes", "No", "Yes"],
            "book_table": ["Yes", "No", "No"],
            "rest_type": ["Casual Dining", "Quick Bites", "Cafe"],
            "reviews_list": ["[]", "[]", "[]"],
            "menu_item": ["[]", "[]", "[]"],
            "dish_liked": ["Pasta", None, "Dosa"],
            "listed_in(type)": ["Buffet", "Delivery", "Dine-out"],
            "listed_in(city)": ["Banashankari", "Koramangala", "Bangalore"],
            "phone": ["123456", "789012", "345678"],
        }
    )


# ── Rating Parsing ───────────────────────────────────────────────────────────


class TestParseRating:
    """Tests for ``Preprocessor._parse_rating``."""

    def test_normal_rating(self) -> None:
        assert Preprocessor._parse_rating("4.1/5") == 4.1

    def test_perfect_rating(self) -> None:
        assert Preprocessor._parse_rating("5.0/5") == 5.0

    def test_zero_rating(self) -> None:
        assert Preprocessor._parse_rating("0.0/5") == 0.0

    def test_new_rating(self) -> None:
        assert Preprocessor._parse_rating("NEW") == 0.0

    def test_dash_rating(self) -> None:
        assert Preprocessor._parse_rating("-") == 0.0

    def test_nan_rating(self) -> None:
        assert Preprocessor._parse_rating(float("nan")) == 0.0

    def test_none_rating(self) -> None:
        assert Preprocessor._parse_rating(None) == 0.0

    def test_plain_float_string(self) -> None:
        assert Preprocessor._parse_rating("3.7") == 3.7

    def test_rating_clamped_above_five(self) -> None:
        assert Preprocessor._parse_rating("6.0/5") == 5.0

    def test_rating_with_whitespace(self) -> None:
        assert Preprocessor._parse_rating("  4.2 / 5  ") == 4.2


# ── Cost Parsing ─────────────────────────────────────────────────────────────


class TestParseCost:
    """Tests for ``Preprocessor._parse_cost``."""

    def test_normal_cost(self) -> None:
        assert Preprocessor._parse_cost("800") == 800

    def test_comma_separated_cost(self) -> None:
        assert Preprocessor._parse_cost("1,200") == 1200

    def test_cost_with_whitespace(self) -> None:
        assert Preprocessor._parse_cost("  500  ") == 500

    def test_nan_cost(self) -> None:
        assert Preprocessor._parse_cost(float("nan")) == 0

    def test_none_cost(self) -> None:
        assert Preprocessor._parse_cost(None) == 0

    def test_non_numeric_cost(self) -> None:
        assert Preprocessor._parse_cost("free") == 0

    def test_float_cost(self) -> None:
        assert Preprocessor._parse_cost("799.5") == 799

    def test_zero_cost(self) -> None:
        assert Preprocessor._parse_cost("0") == 0


# ── Budget Tier Derivation ───────────────────────────────────────────────────


class TestDeriveBudgetTier:
    """Tests for ``Preprocessor._derive_budget_tier``."""

    def test_low_tier_at_boundary(self, preprocessor: Preprocessor) -> None:
        assert preprocessor._derive_budget_tier(500) == "low"

    def test_low_tier_below_boundary(self, preprocessor: Preprocessor) -> None:
        assert preprocessor._derive_budget_tier(300) == "low"

    def test_low_tier_zero(self, preprocessor: Preprocessor) -> None:
        assert preprocessor._derive_budget_tier(0) == "low"

    def test_medium_tier_at_lower_boundary(
        self, preprocessor: Preprocessor
    ) -> None:
        assert preprocessor._derive_budget_tier(501) == "medium"

    def test_medium_tier_at_upper_boundary(
        self, preprocessor: Preprocessor
    ) -> None:
        assert preprocessor._derive_budget_tier(1500) == "medium"

    def test_medium_tier_mid(self, preprocessor: Preprocessor) -> None:
        assert preprocessor._derive_budget_tier(800) == "medium"

    def test_high_tier_at_boundary(self, preprocessor: Preprocessor) -> None:
        assert preprocessor._derive_budget_tier(1501) == "high"

    def test_high_tier_well_above(self, preprocessor: Preprocessor) -> None:
        assert preprocessor._derive_budget_tier(5000) == "high"


# ── Location Normalisation ───────────────────────────────────────────────────


class TestNormaliseLocation:
    """Tests for ``Preprocessor._normalise_location``."""

    def test_title_case(self) -> None:
        assert Preprocessor._normalise_location("banashankari") == "Banashankari"

    def test_trim_whitespace(self) -> None:
        assert Preprocessor._normalise_location("  koramangala  ") == "Koramangala"

    def test_alias_mapping(self) -> None:
        assert Preprocessor._normalise_location("Bengaluru") == "Bangalore"

    def test_nan_location(self) -> None:
        assert Preprocessor._normalise_location(float("nan")) == ""

    def test_none_location(self) -> None:
        assert Preprocessor._normalise_location(None) == ""

    def test_already_normalised(self) -> None:
        assert Preprocessor._normalise_location("Indiranagar") == "Indiranagar"


# ── Yes/No Boolean Parsing ───────────────────────────────────────────────────


class TestParseYesNo:
    """Tests for ``Preprocessor._parse_yes_no``."""

    def test_yes(self) -> None:
        assert Preprocessor._parse_yes_no("Yes") is True

    def test_no(self) -> None:
        assert Preprocessor._parse_yes_no("No") is False

    def test_case_insensitive(self) -> None:
        assert Preprocessor._parse_yes_no("YES") is True

    def test_nan(self) -> None:
        assert Preprocessor._parse_yes_no(float("nan")) is False

    def test_none(self) -> None:
        assert Preprocessor._parse_yes_no(None) is False

    def test_empty_string(self) -> None:
        assert Preprocessor._parse_yes_no("") is False


# ── Full Pipeline ────────────────────────────────────────────────────────────


class TestPreprocessPipeline:
    """Integration-style tests for the full ``preprocess`` method."""

    def test_basic_pipeline(
        self,
        preprocessor: Preprocessor,
        sample_raw_df: pd.DataFrame,
    ) -> None:
        """All three sample rows should be processed successfully."""
        restaurants = preprocessor.preprocess(sample_raw_df)
        assert len(restaurants) == 3

    def test_restaurant_names(
        self,
        preprocessor: Preprocessor,
        sample_raw_df: pd.DataFrame,
    ) -> None:
        """Restaurant names should be preserved."""
        restaurants = preprocessor.preprocess(sample_raw_df)
        names = {r.restaurant_name for r in restaurants}
        assert "Test Restaurant" in names
        assert "Another Place" in names
        assert "Third Spot" in names

    def test_location_normalised(
        self,
        preprocessor: Preprocessor,
        sample_raw_df: pd.DataFrame,
    ) -> None:
        """Locations should be trimmed, title-cased, and alias-mapped."""
        restaurants = preprocessor.preprocess(sample_raw_df)
        locations = {r.location for r in restaurants}
        assert "Banashankari" in locations
        assert "Koramangala" in locations
        # "Bengaluru" → "Bangalore" via alias
        assert "Bangalore" in locations

    def test_cuisines_parsed(
        self,
        preprocessor: Preprocessor,
        sample_raw_df: pd.DataFrame,
    ) -> None:
        """Cuisine strings should be split into lists."""
        restaurants = preprocessor.preprocess(sample_raw_df)
        r0 = next(r for r in restaurants if r.restaurant_name == "Test Restaurant")
        assert r0.cuisines == ["North Indian", "Chinese"]

    def test_budget_tiers(
        self,
        preprocessor: Preprocessor,
        sample_raw_df: pd.DataFrame,
    ) -> None:
        """Budget tiers should match the configured thresholds."""
        restaurants = preprocessor.preprocess(sample_raw_df)
        tiers = {r.restaurant_name: r.budget_tier for r in restaurants}
        # 800 → medium (501–1500)
        assert tiers["Test Restaurant"] == "medium"
        # 300 → low (≤ 500)
        assert tiers["Another Place"] == "low"
        # 2000 → high (> 1500)
        assert tiers["Third Spot"] == "high"

    def test_rating_parsing(
        self,
        preprocessor: Preprocessor,
        sample_raw_df: pd.DataFrame,
    ) -> None:
        """Ratings should be parsed from 'X/5' format."""
        restaurants = preprocessor.preprocess(sample_raw_df)
        ratings = {r.restaurant_name: r.rating for r in restaurants}
        assert ratings["Test Restaurant"] == 4.1
        assert ratings["Another Place"] == 3.5
        # "NEW" → 0.0
        assert ratings["Third Spot"] == 0.0

    def test_boolean_fields(
        self,
        preprocessor: Preprocessor,
        sample_raw_df: pd.DataFrame,
    ) -> None:
        """Yes/No fields should be converted to booleans."""
        restaurants = preprocessor.preprocess(sample_raw_df)
        r0 = next(r for r in restaurants if r.restaurant_name == "Test Restaurant")
        assert r0.online_order is True
        assert r0.book_table is True

        r1 = next(r for r in restaurants if r.restaurant_name == "Another Place")
        assert r1.online_order is False
        assert r1.book_table is False

    def test_drops_rows_missing_name(
        self,
        preprocessor: Preprocessor,
    ) -> None:
        """Rows with missing restaurant name should be dropped."""
        df = pd.DataFrame(
            {
                "name": [None, "Valid"],
                "location": ["Somewhere", "Here"],
                "cuisines": ["Indian", "Chinese"],
                "approx_cost(for two people)": ["500", "600"],
                "rate": ["4.0/5", "3.0/5"],
                "votes": [10, 20],
                "online_order": ["Yes", "No"],
                "book_table": ["No", "No"],
                "rest_type": ["Cafe", "Cafe"],
                "url": ["http://a", "http://b"],
                "address": ["addr1", "addr2"],
            }
        )
        restaurants = preprocessor.preprocess(df)
        assert len(restaurants) == 1
        assert restaurants[0].restaurant_name == "Valid"

    def test_drops_rows_missing_location(
        self,
        preprocessor: Preprocessor,
    ) -> None:
        """Rows with missing location should be dropped."""
        df = pd.DataFrame(
            {
                "name": ["Valid", "Also Valid"],
                "location": ["", "Here"],
                "cuisines": ["Indian", "Chinese"],
                "approx_cost(for two people)": ["500", "600"],
                "rate": ["4.0/5", "3.0/5"],
                "votes": [10, 20],
                "online_order": ["Yes", "No"],
                "book_table": ["No", "No"],
                "rest_type": ["Cafe", "Cafe"],
                "url": ["http://a", "http://b"],
                "address": ["addr1", "addr2"],
            }
        )
        restaurants = preprocessor.preprocess(df)
        assert len(restaurants) == 1
        assert restaurants[0].restaurant_name == "Also Valid"

    def test_restaurant_ids_assigned(
        self,
        preprocessor: Preprocessor,
        sample_raw_df: pd.DataFrame,
    ) -> None:
        """Each restaurant should get a unique sequential ID."""
        restaurants = preprocessor.preprocess(sample_raw_df)
        ids = [r.restaurant_id for r in restaurants]
        assert ids == [0, 1, 2]
