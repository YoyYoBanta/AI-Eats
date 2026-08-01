"""
Unit tests for the FilterEngine and CandidateSelector.

Covers:
- Standard filtering pipeline (location → budget → cuisine → min_rating).
- Progressive relaxation of filters (cuisine, then budget, then rating).
- Capping at MAX_CANDIDATES.
"""

from __future__ import annotations

import pytest

from models.preferences import UserPreference
from models.restaurant import Restaurant
from repositories.restaurant_repo import RestaurantRepository
from services.filter_engine import CandidateSelector, FilterEngine


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_restaurants() -> list[Restaurant]:
    """Provide a mock list of preprocessed restaurants."""
    return [
        Restaurant(
            restaurant_id=1,
            restaurant_name="Pizza Palace",
            location="Indiranagar",
            cuisines=["Italian", "Pizza"],
            average_cost_for_two=800,
            budget_tier="medium",
            rating=4.5,
            votes=100,
        ),
        Restaurant(
            restaurant_id=2,
            restaurant_name="Cheap Bites",
            location="Indiranagar",
            cuisines=["Fast Food"],
            average_cost_for_two=300,
            budget_tier="low",
            rating=3.0,
            votes=50,
        ),
        Restaurant(
            restaurant_id=3,
            restaurant_name="Fancy Italian",
            location="Indiranagar",
            cuisines=["Italian"],
            average_cost_for_two=2000,
            budget_tier="high",
            rating=4.8,
            votes=200,
        ),
        Restaurant(
            restaurant_id=4,
            restaurant_name="Pasta Corner",
            location="Indiranagar",
            cuisines=["Italian", "Cafe"],
            average_cost_for_two=600,
            budget_tier="medium",
            rating=4.2,
            votes=150,
        ),
        Restaurant(
            restaurant_id=5,
            restaurant_name="Sushi Spot",
            location="Koramangala",
            cuisines=["Japanese"],
            average_cost_for_two=1200,
            budget_tier="medium",
            rating=4.6,
            votes=300,
        ),
    ]


@pytest.fixture
def repo(sample_restaurants: list[Restaurant]) -> RestaurantRepository:
    """Provide a populated RestaurantRepository."""
    r = RestaurantRepository()
    r.load(sample_restaurants)
    return r


# ── FilterEngine Tests ───────────────────────────────────────────────────────


class TestFilterEngine:
    def test_apply_filters_all(self, repo: RestaurantRepository) -> None:
        """Applying all filters strictly."""
        engine = FilterEngine(repo)
        prefs = UserPreference(
            location="Indiranagar",
            budget="medium",
            cuisine="Italian",
            min_rating=4.0,
        )
        base = repo.filter_by_location(prefs.location)
        result = engine.apply_filters(base, prefs)
        
        # Should match Pizza Palace (4.5) and Pasta Corner (4.2)
        # Cheap Bites (low budget, no Italian) -> fail
        # Fancy Italian (high budget) -> fail
        assert len(result) == 2
        names = {r.restaurant_name for r in result}
        assert "Pizza Palace" in names
        assert "Pasta Corner" in names

    def test_apply_filters_partial(self, repo: RestaurantRepository) -> None:
        """Applying filters with cuisine relaxed."""
        engine = FilterEngine(repo)
        prefs = UserPreference(
            location="Indiranagar",
            budget="low",
            cuisine="Italian",  # Cheap bites is not Italian
            min_rating=2.0,
        )
        base = repo.filter_by_location(prefs.location)
        
        # If we relax cuisine, Cheap Bites should match
        result = engine.apply_filters(
            base, prefs, use_budget=True, use_cuisine=False, use_rating=True
        )
        assert len(result) == 1
        assert result[0].restaurant_name == "Cheap Bites"


# ── CandidateSelector Tests ──────────────────────────────────────────────────


class TestCandidateSelector:
    def test_no_location_match(self, repo: RestaurantRepository) -> None:
        """If location fails, return empty immediately."""
        selector = CandidateSelector(repo, min_results_threshold=1)
        prefs = UserPreference(location="Whitefield", budget="medium")
        cands, relaxed = selector.select(prefs)
        assert cands == []
        assert relaxed == []

    def test_strict_match_no_relaxation(self, repo: RestaurantRepository) -> None:
        """If enough results match strict filters, none are relaxed."""
        selector = CandidateSelector(repo, min_results_threshold=2)
        prefs = UserPreference(
            location="Indiranagar",
            budget="medium",
            cuisine="Italian",
            min_rating=4.0,
        )
        cands, relaxed = selector.select(prefs)
        assert len(cands) == 2
        assert relaxed == []
        
        # Should be sorted by rating DESC (Pizza Palace: 4.5, Pasta Corner: 4.2)
        assert cands[0].restaurant_name == "Pizza Palace"
        assert cands[1].restaurant_name == "Pasta Corner"

    def test_relax_cuisine(self, repo: RestaurantRepository) -> None:
        """Relax cuisine if strict matches are below threshold."""
        # Threshold 2. There is only 1 low budget Italian (0 actually).
        # Cheap Bites is low budget, Fast Food.
        selector = CandidateSelector(repo, min_results_threshold=1)
        prefs = UserPreference(
            location="Indiranagar",
            budget="low",
            cuisine="Italian",
            min_rating=2.0,
        )
        cands, relaxed = selector.select(prefs)
        
        # With cuisine disabled, Cheap Bites matches
        assert len(cands) == 1
        assert cands[0].restaurant_name == "Cheap Bites"
        assert relaxed == ["cuisine"]

    def test_relax_budget(self, repo: RestaurantRepository) -> None:
        """Relax budget if dropping cuisine still yields too few results."""
        # We want Indiranagar, low budget, Japanese, min rating 4.0
        # No low budget in Indiranagar has rating > 3.0.
        # If we drop cuisine, we get Cheap Bites (rating 3.0, fails min_rating).
        # If we drop budget, we check Japanese -> none.
        # Wait, if we drop cuisine AND budget, we check min_rating > 4.0.
        # This matches Pizza Palace, Fancy Italian, Pasta Corner.
        selector = CandidateSelector(repo, min_results_threshold=2)
        prefs = UserPreference(
            location="Indiranagar",
            budget="low",
            cuisine="Japanese",
            min_rating=4.0,
        )
        cands, relaxed = selector.select(prefs)
        
        assert len(cands) == 3
        # Sorted by rating DESC: Fancy (4.8), Pizza Palace (4.5), Pasta Corner (4.2)
        assert cands[0].restaurant_name == "Fancy Italian"
        assert cands[1].restaurant_name == "Pizza Palace"
        assert cands[2].restaurant_name == "Pasta Corner"
        assert relaxed == ["cuisine", "budget"]

    def test_max_candidates_cap(self, repo: RestaurantRepository) -> None:
        """Ensure candidates do not exceed MAX_CANDIDATES."""
        selector = CandidateSelector(repo, max_candidates=1, min_results_threshold=1)
        prefs = UserPreference(
            location="Indiranagar",
            budget="medium",
            cuisine="Italian",
        )
        # 2 match strictly, but max is 1.
        cands, relaxed = selector.select(prefs)
        assert len(cands) == 1
        assert cands[0].restaurant_name == "Pizza Palace"  # Highest rated
        assert relaxed == []
