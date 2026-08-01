"""
Prompt builder and context management logic.

Assembles the system and user prompt using a template, injects user
preferences and JSON-serialized candidates, and ensures the resulting
prompt fits within the LLM's token budget.

Maps to: Architecture §3.3 — Integration Layer.
"""

from __future__ import annotations

import json
from pathlib import Path

from config.settings import settings
from models.preferences import UserPreference
from models.restaurant import Restaurant


class PromptBuilder:
    """Assembles the LLM prompt from a template and structured data."""

    def __init__(self, template_path: str | Path) -> None:
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {self.template_path}")
        self.template = self.template_path.read_text(encoding="utf-8")

    def build_prompt(
        self,
        prefs: UserPreference,
        candidates: list[Restaurant],
        top_k: int | None = None,
    ) -> str:
        """Format the prompt template with preferences and candidate JSON.

        Parameters
        ----------
        prefs:
            User preferences.
        candidates:
            List of filtered candidate restaurants.
        top_k:
            Number of top recommendations to request (default from settings).

        Returns
        -------
        str
            The fully assembled prompt string.
        """
        top_k_val = top_k if top_k is not None else settings.TOP_K_RESULTS

        # Create minimal candidate representations to save tokens
        cands_data = []
        for c in candidates:
            cands_data.append(
                {
                    "restaurant_id": c.restaurant_id,
                    "restaurant_name": c.restaurant_name,
                    "cuisines": c.cuisines,
                    "rating": c.rating,
                    "average_cost_for_two": c.average_cost_for_two,
                    "budget_tier": c.budget_tier,
                    "location": c.location,
                }
            )

        candidates_json = json.dumps(cands_data, indent=2)

        return self.template.format(
            location=prefs.location,
            budget=prefs.budget,
            cuisine=prefs.cuisine or "Any",
            min_rating=prefs.min_rating if prefs.min_rating > 0.0 else "Any",
            additional_preferences=prefs.additional_preferences or "None",
            candidates_json=candidates_json,
            top_k=top_k_val,
        )


class ContextManager:
    """Estimates prompt length and truncates candidates if necessary.

    Parameters
    ----------
    max_prompt_tokens:
        Maximum allowed tokens for the prompt.
    chars_per_token:
        Heuristic multiplier to convert tokens to character length.
    """

    def __init__(
        self,
        max_prompt_tokens: int = 1500,
        chars_per_token: int = 4,
    ) -> None:
        self.max_chars = max_prompt_tokens * chars_per_token

    def truncate_candidates(
        self,
        prompt_builder: PromptBuilder,
        prefs: UserPreference,
        candidates: list[Restaurant],
        top_k: int | None = None,
    ) -> list[Restaurant]:
        """Iteratively remove candidates until the prompt fits the character budget.

        Removes the lowest-ranked candidate (last in the list) first.
        """
        current_candidates = list(candidates)

        while current_candidates:
            prompt = prompt_builder.build_prompt(
                prefs,
                current_candidates,
                top_k,
            )
            if len(prompt) <= self.max_chars:
                return current_candidates

            # Prompt is too long; remove the lowest-rated candidate
            current_candidates.pop()

        return current_candidates
