"""
Preprocessor — normalises raw Zomato data into ``Restaurant`` records.

Handles column renaming, missing-value imputation, cuisine parsing,
budget-tier derivation, and location normalisation.

Maps to: Architecture §3.1 — Preprocessor component.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import pandas as pd

from models.restaurant import Restaurant

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)

# ── Raw → Canonical column mapping ──────────────────────────────────────────
# The Hugging Face dataset uses these raw column names.
RAW_COLUMN_MAP: dict[str, str] = {
    "name": "restaurant_name",
    "location": "location",
    "cuisines": "cuisines",
    "approx_cost(for two people)": "average_cost_for_two",
    "rate": "rating",
    "votes": "votes",
    "address": "address",
    "online_order": "online_order",
    "book_table": "book_table",
    "rest_type": "restaurant_type",
    "url": "url",
}

# ── Location alias map ──────────────────────────────────────────────────────
# Normalise common alternate spellings to a single canonical form.
LOCATION_ALIASES: dict[str, str] = {
    "Bengaluru": "Bangalore",
    "Bengaluru South": "Bangalore",
    "Bengaluru North": "Bangalore",
}

# ── Rating pattern ──────────────────────────────────────────────────────────
# Raw ratings are strings like "4.1/5", "NEW", "-", or NaN.
_RATING_RE = re.compile(r"^([\d.]+)\s*/\s*5$")


class Preprocessor:
    """Cleans and transforms a raw Zomato DataFrame into ``Restaurant`` records.

    Parameters
    ----------
    settings:
        Application settings (used for budget-tier thresholds).
        If *None*, the global singleton is imported.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        if settings is None:
            from config.settings import settings as _s

            settings = _s
        self._budget_low_max = settings.BUDGET_LOW_MAX
        self._budget_medium_max = settings.BUDGET_MEDIUM_MAX

    # ── Public API ───────────────────────────────────────────────────────

    def preprocess(self, raw_df: pd.DataFrame) -> list[Restaurant]:
        """Run the full preprocessing pipeline.

        Steps
        -----
        1. Rename columns to canonical names.
        2. Drop rows missing critical fields (name, location, rating).
        3. Parse and normalise each field.
        4. Convert to ``Restaurant`` model instances.

        Returns
        -------
        list[Restaurant]
            Cleaned restaurant records ready for the repository.
        """
        df = raw_df.copy()
        initial_count = len(df)
        logger.info("Preprocessing %d raw rows …", initial_count)

        # Step 1: Rename columns
        df = self._rename_columns(df)

        # Step 2: Parse rating first (needed for dropping rows)
        df["rating"] = df["rating"].apply(self._parse_rating)

        # Step 3: Drop rows missing critical fields
        df = self._drop_incomplete(df)

        # Step 3.5: Drop duplicates
        df = self._drop_duplicates(df)

        # Step 4: Parse cost
        df["average_cost_for_two"] = df["average_cost_for_two"].apply(
            self._parse_cost
        )

        # Step 5: Derive budget tier
        df["budget_tier"] = df["average_cost_for_two"].apply(
            self._derive_budget_tier
        )

        # Step 6: Normalise locations
        df["location"] = df["location"].apply(self._normalise_location)

        # Step 7: Parse boolean fields
        df["online_order"] = df["online_order"].apply(self._parse_yes_no)
        df["book_table"] = df["book_table"].apply(self._parse_yes_no)

        # Step 8: Ensure votes is int
        df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)

        # Step 9: Clean string fields
        for col in ("restaurant_name", "address", "restaurant_type", "url"):
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        # Step 10: Assign restaurant_id (row index)
        df = df.reset_index(drop=True)
        df["restaurant_id"] = df.index

        # Step 11: Convert to Restaurant model instances
        restaurants = self._to_models(df)

        logger.info(
            "Preprocessing complete: %d → %d records (%d dropped).",
            initial_count,
            len(restaurants),
            initial_count - len(restaurants),
        )
        return restaurants

    # ── Internal helpers ─────────────────────────────────────────────────

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename raw HF columns to canonical names."""
        rename_map = {
            raw: canonical
            for raw, canonical in RAW_COLUMN_MAP.items()
            if raw in df.columns
        }
        df = df.rename(columns=rename_map)
        return df

    def _drop_incomplete(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop rows missing name, location, or with unparseable rating."""
        before = len(df)

        # Drop rows where critical text fields are missing / empty
        for col in ("restaurant_name", "location"):
            if col in df.columns:
                df = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]

        # Drop rows where rating could not be parsed (stayed as 0.0 is ok,
        # but NaN means truly unparseable — those were already set to 0.0
        # by _parse_rating, so we keep them).

        after = len(df)
        if before != after:
            logger.info(
                "Dropped %d rows with missing name/location.",
                before - after,
            )
        return df

    def _drop_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop duplicate restaurants based on name and address."""
        before = len(df)
        subset_cols = ["restaurant_name", "location"]
        if "address" in df.columns:
            subset_cols.append("address")
            
        df = df.drop_duplicates(subset=subset_cols, keep="first")
        
        after = len(df)
        if before != after:
            logger.info("Dropped %d duplicate rows.", before - after)
        return df

    @staticmethod
    def _parse_rating(raw: object) -> float:
        """Parse rating from strings like ``'4.1/5'``.

        Returns 0.0 for unparseable values (``'NEW'``, ``'-'``, NaN).
        """
        if pd.isna(raw):
            return 0.0
        raw_str = str(raw).strip()
        m = _RATING_RE.match(raw_str)
        if m:
            val = float(m.group(1))
            return max(0.0, min(5.0, val))
        # Try plain float
        try:
            val = float(raw_str)
            return max(0.0, min(5.0, val))
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_cost(raw: object) -> int:
        """Parse cost from strings like ``'800'`` or ``'1,200'``.

        Returns 0 for unparseable values.
        """
        if pd.isna(raw):
            return 0
        raw_str = str(raw).strip().replace(",", "")
        try:
            return max(0, int(float(raw_str)))
        except (ValueError, TypeError):
            return 0

    def _derive_budget_tier(self, cost: int) -> str:
        """Map ``average_cost_for_two`` to a budget tier.

        Thresholds from ``config.settings``:
        - ``low``   : cost ≤ BUDGET_LOW_MAX  (default 500)
        - ``medium``: cost ≤ BUDGET_MEDIUM_MAX (default 1500)
        - ``high``  : cost > BUDGET_MEDIUM_MAX
        """
        if cost <= self._budget_low_max:
            return "low"
        if cost <= self._budget_medium_max:
            return "medium"
        return "high"

    @staticmethod
    def _normalise_location(raw: object) -> str:
        """Trim, title-case, and apply alias mapping to a location string."""
        if pd.isna(raw):
            return ""
        loc = str(raw).strip().title()
        return LOCATION_ALIASES.get(loc, loc)

    @staticmethod
    def _parse_yes_no(raw: object) -> bool:
        """Convert ``'Yes'``/``'No'`` strings to boolean."""
        if pd.isna(raw):
            return False
        return str(raw).strip().lower() == "yes"

    @staticmethod
    def _to_models(df: pd.DataFrame) -> list[Restaurant]:
        """Convert a cleaned DataFrame to a list of ``Restaurant`` instances.

        Rows that fail Pydantic validation are logged and skipped.
        """
        restaurants: list[Restaurant] = []
        for _, row in df.iterrows():
            try:
                r = Restaurant(
                    restaurant_id=int(row.get("restaurant_id", 0)),
                    restaurant_name=str(row.get("restaurant_name", "")),
                    location=str(row.get("location", "")),
                    cuisines=row.get("cuisines", ""),
                    average_cost_for_two=int(row.get("average_cost_for_two", 0)),
                    budget_tier=str(row.get("budget_tier", "low")),
                    rating=float(row.get("rating", 0.0)),
                    votes=int(row.get("votes", 0)),
                    address=row.get("address") or None,
                    online_order=bool(row.get("online_order", False)),
                    book_table=bool(row.get("book_table", False)),
                    restaurant_type=row.get("restaurant_type") or None,
                    url=row.get("url") or None,
                )
                restaurants.append(r)
            except Exception:
                logger.debug(
                    "Skipping row %s due to validation error.",
                    row.get("restaurant_id", "?"),
                    exc_info=True,
                )
        return restaurants
