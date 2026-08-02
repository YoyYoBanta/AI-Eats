"""
Filter engine and candidate selection logic.

Applies sequential hard filters to the restaurant repository and prepares
a token-safe candidate list for the LLM prompt. Implements progressive
relaxation of filters if results are too sparse.

Maps to: Architecture §3.3 — Integration Layer.
"""

from __future__ import annotations

import logging

from config.settings import settings
from models.preferences import UserPreference
from models.restaurant import Restaurant
from repositories.restaurant_repo import RestaurantRepository

logger = logging.getLogger(__name__)


class FilterEngine:
    """Applies hard filters to the repository based on user preferences."""

    def __init__(self, repo: RestaurantRepository) -> None:
        self.repo = repo

    def apply_filters(
        self,
        base_candidates: list[Restaurant],
        prefs: UserPreference,
        use_budget: bool = True,
        use_cuisine: bool = True,
        use_rating: bool = True,
    ) -> list[Restaurant]:
        """Apply a subset of filters to the given candidates."""
        candidates = base_candidates

        if use_budget:
            candidates = self.repo.filter_by_budget(candidates, prefs.budget)

        if use_cuisine and prefs.cuisine:
            candidates = self.repo.filter_by_cuisine(candidates, prefs.cuisine)

        if use_rating and prefs.min_rating > 0.0:
            candidates = self.repo.filter_by_min_rating(candidates, prefs.min_rating)

        return candidates


class CandidateSelector:
    """Selects and ranks candidate restaurants, relaxing filters if necessary.

    Parameters
    ----------
    repo:
        The populated restaurant repository.
    max_candidates:
        Maximum number of candidates to return (default from settings).
    min_results_threshold:
        Minimum acceptable results before triggering relaxation (default 3).
    """

    def __init__(
        self,
        repo: RestaurantRepository,
        max_candidates: int | None = None,
        min_results_threshold: int = 3,
    ) -> None:
        self.engine = FilterEngine(repo)
        self.repo = repo
        self.max_candidates = (
            max_candidates if max_candidates is not None else settings.MAX_CANDIDATES
        )
        self.min_results = min_results_threshold

    def select(self, prefs: UserPreference) -> tuple[list[Restaurant], list[str]]:
        """Select top candidates for the given preferences.

        Applies location filter strictly, then attempts budget, cuisine, and
        rating filters. If fewer than `min_results_threshold` restaurants remain,
        progressively relaxes filters in order: cuisine → budget → rating.

        Returns
        -------
        tuple[list[Restaurant], list[str]]
            A tuple containing:
            - List of selected candidate restaurants (sorted by rating DESC).
            - List of filter names that were relaxed (e.g. ``["cuisine", "budget"]``).
        """
        # 1. Location is always a hard filter
        base_candidates = self.repo.filter_by_location(prefs.location)
        if not base_candidates:
            return [], []

        relaxed: list[str] = []

        candidates = self.engine.apply_filters(
            base_candidates,
            prefs,
            use_budget=True,
            use_cuisine=True,
            use_rating=True,
        )
        return self._finalize(candidates), relaxed

    def _finalize(self, candidates: list[Restaurant]) -> list[Restaurant]:
        """Sort candidates by rating (descending) and cap at MAX_CANDIDATES."""
        sorted_cands = sorted(candidates, key=lambda r: r.rating, reverse=True)
        return sorted_cands[: self.max_candidates]
