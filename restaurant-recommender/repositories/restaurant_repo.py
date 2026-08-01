"""
Restaurant repository — in-memory store with query methods.

Provides read-only access to the preprocessed restaurant data.
Designed to be populated once at startup and queried at request time.

Maps to: Architecture §3.1 — RestaurantRepository component.
"""

from __future__ import annotations

import logging
from typing import Sequence

from models.restaurant import BudgetTier, Restaurant

logger = logging.getLogger(__name__)


class RestaurantRepository:
    """In-memory repository of ``Restaurant`` records.

    Populated via :meth:`load` at application startup. Supports filtering
    and querying by location, cuisine, budget tier, and minimum rating.
    """

    def __init__(self) -> None:
        self._restaurants: list[Restaurant] = []
        self._locations: list[str] = []
        self._loaded = False

    # ── Lifecycle ────────────────────────────────────────────────────────

    def load(self, restaurants: Sequence[Restaurant]) -> None:
        """Populate the repository with preprocessed restaurant records.

        Parameters
        ----------
        restaurants:
            Iterable of ``Restaurant`` instances produced by the Preprocessor.
        """
        self._restaurants = list(restaurants)
        self._locations = sorted(
            {r.location for r in self._restaurants if r.location}
        )
        self._loaded = True
        logger.info(
            "Repository loaded: %d restaurants across %d locations.",
            len(self._restaurants),
            len(self._locations),
        )

    @property
    def is_loaded(self) -> bool:
        """Return True if the repository has been populated."""
        return self._loaded

    # ── Read API ─────────────────────────────────────────────────────────

    def get_all(self) -> list[Restaurant]:
        """Return all restaurant records."""
        self._ensure_loaded()
        return list(self._restaurants)

    def get_locations(self) -> list[str]:
        """Return a sorted, deduplicated list of supported locations / neighbourhoods."""
        self._ensure_loaded()
        return list(self._locations)

    def count(self) -> int:
        """Return the total number of restaurants."""
        return len(self._restaurants)

    # ── Filtering ────────────────────────────────────────────────────────

    def filter_by_location(self, location: str) -> list[Restaurant]:
        """Return restaurants matching the given location (case-insensitive).

        Parameters
        ----------
        location:
            Location / city name to filter by.

        Returns
        -------
        list[Restaurant]
            Matching restaurants (may be empty).
        """
        self._ensure_loaded()
        loc_lower = location.strip().lower()
        return [
            r
            for r in self._restaurants
            if r.location.lower() == loc_lower
        ]

    def filter_by_cuisine(
        self,
        restaurants: list[Restaurant],
        cuisine: str,
    ) -> list[Restaurant]:
        """Filter restaurants whose cuisine list contains the given cuisine.

        The match is case-insensitive and uses substring matching so that
        ``"Italian"`` matches ``"South Italian"`` etc.

        Parameters
        ----------
        restaurants:
            Pre-filtered list to narrow down.
        cuisine:
            Cuisine name to search for.

        Returns
        -------
        list[Restaurant]
            Matching restaurants.
        """
        cuisine_lower = cuisine.strip().lower()
        if not cuisine_lower:
            return restaurants
        return [
            r
            for r in restaurants
            if any(cuisine_lower in c.lower() for c in r.cuisines)
        ]

    def filter_by_budget(
        self,
        restaurants: list[Restaurant],
        budget_tier: BudgetTier,
    ) -> list[Restaurant]:
        """Filter restaurants matching the given budget tier.

        Parameters
        ----------
        restaurants:
            Pre-filtered list to narrow down.
        budget_tier:
            One of ``"low"``, ``"medium"``, ``"high"``.

        Returns
        -------
        list[Restaurant]
            Matching restaurants.
        """
        return [r for r in restaurants if r.budget_tier == budget_tier]

    def filter_by_min_rating(
        self,
        restaurants: list[Restaurant],
        min_rating: float,
    ) -> list[Restaurant]:
        """Filter restaurants with rating ≥ ``min_rating``.

        Parameters
        ----------
        restaurants:
            Pre-filtered list to narrow down.
        min_rating:
            Minimum acceptable rating (0.0–5.0).

        Returns
        -------
        list[Restaurant]
            Matching restaurants.
        """
        return [r for r in restaurants if r.rating >= min_rating]

    # ── Internal ─────────────────────────────────────────────────────────

    def _ensure_loaded(self) -> None:
        """Raise if the repository hasn't been populated yet."""
        if not self._loaded:
            raise RuntimeError(
                "RestaurantRepository has not been loaded. "
                "Call `load()` with preprocessed data first."
            )
