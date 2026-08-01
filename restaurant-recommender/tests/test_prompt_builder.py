"""
Unit tests for the PromptBuilder and ContextManager.

Covers:
- Loading the prompt template.
- Injecting preferences and JSON candidates into the template.
- Context truncation logic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from models.preferences import UserPreference
from models.restaurant import Restaurant
from services.prompt_builder import ContextManager, PromptBuilder


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_template_path(tmp_path: Path) -> Path:
    """Create a temporary dummy prompt template."""
    template_content = (
        "Loc: {location}, Bud: {budget}, Cuis: {cuisine}, "
        "MinRating: {min_rating}, Add: {additional_preferences}, "
        "TopK: {top_k}\nCands: {candidates_json}"
    )
    p = tmp_path / "test_prompt.txt"
    p.write_text(template_content, encoding="utf-8")
    return p


@pytest.fixture
def builder(mock_template_path: Path) -> PromptBuilder:
    """Provide a PromptBuilder with the dummy template."""
    return PromptBuilder(mock_template_path)


@pytest.fixture
def sample_candidates() -> list[Restaurant]:
    """Provide sample candidates for prompt building."""
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
            restaurant_name="Sushi Spot",
            location="Indiranagar",
            cuisines=["Japanese"],
            average_cost_for_two=1200,
            budget_tier="medium",
            rating=4.6,
            votes=300,
        ),
    ]


@pytest.fixture
def sample_prefs() -> UserPreference:
    """Provide a sample UserPreference."""
    return UserPreference(
        location="Indiranagar",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        additional_preferences="Outdoor seating",
    )


# ── PromptBuilder Tests ──────────────────────────────────────────────────────


class TestPromptBuilder:
    def test_missing_template(self) -> None:
        """Should raise FileNotFoundError if template doesn't exist."""
        with pytest.raises(FileNotFoundError):
            PromptBuilder("does_not_exist.txt")

    def test_build_prompt(
        self,
        builder: PromptBuilder,
        sample_prefs: UserPreference,
        sample_candidates: list[Restaurant],
    ) -> None:
        """Prompt should format correctly with injected variables."""
        prompt = builder.build_prompt(sample_prefs, sample_candidates, top_k=3)

        assert "Loc: Indiranagar" in prompt
        assert "Bud: medium" in prompt
        assert "Cuis: Italian" in prompt
        assert "MinRating: 4.0" in prompt
        assert "Add: Outdoor seating" in prompt
        assert "TopK: 3" in prompt

        # Check JSON injection
        json_str = prompt.split("Cands: ")[1]
        cands_data = json.loads(json_str)
        assert len(cands_data) == 2
        assert cands_data[0]["restaurant_name"] == "Pizza Palace"
        assert cands_data[0]["budget_tier"] == "medium"

    def test_build_prompt_empty_fields(
        self,
        builder: PromptBuilder,
        sample_candidates: list[Restaurant],
    ) -> None:
        """Empty optional fields should fallback to defaults."""
        prefs = UserPreference(
            location="Indiranagar",
            budget="low",
            # missing cuisine, min_rating, additional_preferences
        )
        prompt = builder.build_prompt(prefs, sample_candidates, top_k=5)

        assert "Cuis: Any" in prompt
        assert "MinRating: Any" in prompt
        assert "Add: None" in prompt


# ── ContextManager Tests ─────────────────────────────────────────────────────


class TestContextManager:
    def test_no_truncation_needed(
        self,
        builder: PromptBuilder,
        sample_prefs: UserPreference,
        sample_candidates: list[Restaurant],
    ) -> None:
        """If prompt is well within limits, return candidates untouched."""
        cm = ContextManager(max_prompt_tokens=1000)  # Huge limit
        cands = cm.truncate_candidates(builder, sample_prefs, sample_candidates)
        assert len(cands) == 2

    def test_truncation_removes_from_bottom(
        self,
        builder: PromptBuilder,
        sample_prefs: UserPreference,
        sample_candidates: list[Restaurant],
    ) -> None:
        """If limit is too small, pop candidates from the end."""
        # Calculate exactly how big one candidate is
        full_prompt = builder.build_prompt(sample_prefs, sample_candidates)
        char_len = len(full_prompt)

        # Set limit to be just less than the full prompt
        # but big enough to hold 1 candidate.
        max_chars = char_len - 50
        cm = ContextManager(max_prompt_tokens=max_chars // 4)
        
        cands = cm.truncate_candidates(builder, sample_prefs, sample_candidates)
        assert len(cands) == 1
        # The second candidate (Sushi Spot) should have been popped
        assert cands[0].restaurant_name == "Pizza Palace"

    def test_truncation_to_zero(
        self,
        builder: PromptBuilder,
        sample_prefs: UserPreference,
        sample_candidates: list[Restaurant],
    ) -> None:
        """If limit is extremely small, it might pop all candidates."""
        cm = ContextManager(max_prompt_tokens=1)  # 4 characters
        cands = cm.truncate_candidates(builder, sample_prefs, sample_candidates)
        assert len(cands) == 0
