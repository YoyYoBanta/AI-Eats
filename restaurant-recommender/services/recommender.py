"""
Recommender orchestration service.

Wires together the data repository, filter engine, prompt builder,
LLM client, and parser to form the complete end-to-end pipeline.
Provides rule-based fallbacks on failure.

Maps to: Architecture §3.4 — Recommendation Engine.
"""

from __future__ import annotations

import logging
from pathlib import Path

from config.settings import settings
from models.preferences import UserPreference
from models.recommendation import Recommendation, RecommendationList
from models.restaurant import Restaurant
from repositories.restaurant_repo import RestaurantRepository
from services.filter_engine import CandidateSelector
from services.llm_client import LLMClient
from services.prompt_builder import ContextManager, PromptBuilder
from services.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class FallbackRanker:
    """Provides rule-based ranking if the LLM fails."""

    def rank(self, candidates: list[Restaurant], top_k: int) -> list[Recommendation]:
        """Rank candidates based purely on rating.
        
        Note: Candidates are assumed to be already sorted by rating
        descending by the CandidateSelector.
        """
        top_candidates = candidates[:top_k]

        recs = []
        for i, c in enumerate(top_candidates, start=1):
            recs.append(
                Recommendation(
                    restaurant_id=c.restaurant_id,
                    restaurant_name=c.restaurant_name,
                    cuisines=c.cuisines,
                    rating=c.rating,
                    estimated_cost_for_two=c.average_cost_for_two,
                    budget_tier=c.budget_tier,
                    location=c.location,
                    rank=i,
                    explanation="Recommended based on rating and your filters (Fallback AI).",
                    address=c.address,
                )
            )
        return recs


class RecommenderService:
    """Orchestrates the full recommendation pipeline."""

    def __init__(self, repo: RestaurantRepository) -> None:
        self.repo = repo
        self.selector = CandidateSelector(repo)

        # Determine prompt template path
        base_dir = Path(__file__).parent.parent
        template_path = base_dir / "config" / "prompts" / "recommendation_v1.txt"

        self.prompt_builder = PromptBuilder(template_path)
        self.context_manager = ContextManager()

        self.llm_client = LLMClient()
        self.parser = ResponseParser()
        self.fallback = FallbackRanker()

    def recommend(
        self, prefs: UserPreference, top_k: int | None = None
    ) -> RecommendationList:
        """Generate recommendations for the given preferences.

        Executes the filter -> prompt -> LLM -> parse pipeline.
        Falls back to rule-based ranking if the LLM fails and
        ENABLE_FALLBACK_RANKER is True.

        Parameters
        ----------
        prefs:
            Validated user preferences.
        top_k:
            Number of top results to request (default from settings).

        Returns
        -------
        RecommendationList
            The structured recommendations.
        """
        top_k_val = top_k if top_k is not None else settings.TOP_K_RESULTS

        # 1. Select Candidates (Filter Engine)
        candidates, relaxed_filters = self.selector.select(prefs)

        metadata = {
            "candidates_considered": len(candidates),
            "filters_relaxed": relaxed_filters,
            "llm_model": self.llm_client.model,
            "fallback_used": False,
        }

        # Handle zero candidates gracefully
        if not candidates:
            logger.warning("No candidates found even after filter relaxation.")
            return RecommendationList(
                summary="We couldn't find any restaurants matching your location and preferences.",
                recommendations=[],
                metadata=metadata,
            )

        # 2. Build Prompt
        final_candidates = self.context_manager.truncate_candidates(
            self.prompt_builder, prefs, candidates, top_k=top_k_val
        )
        metadata["candidates_considered"] = len(final_candidates)

        prompt = self.prompt_builder.build_prompt(
            prefs, final_candidates, top_k=top_k_val
        )

        # 3. Call LLM
        fallback_triggered = False
        try:
            raw_json = self.llm_client.get_recommendations(prompt)
            result = self.parser.parse(raw_json, metadata=metadata)
            return self._enrich_addresses(result, final_candidates)
        except Exception as exc:
            logger.error("LLM pipeline failed: %s", exc)
            if not settings.ENABLE_FALLBACK_RANKER:
                raise
            fallback_triggered = True

        # 4. Fallback Logic
        if fallback_triggered:
            metadata["fallback_used"] = True
            fallback_recs = self.fallback.rank(final_candidates, top_k_val)
            result = RecommendationList(
                summary="Showing top rated restaurants based on your filters. (AI generation is currently unavailable)",
                recommendations=fallback_recs,
                metadata=metadata,
            )
            return self._enrich_addresses(result, final_candidates)

        raise RuntimeError("Unexpected execution path in RecommenderService.")

    def _enrich_addresses(
        self, result: RecommendationList, candidates: list[Restaurant]
    ) -> RecommendationList:
        """Merge omitted optional fields (address) back into the recommendations."""
        cand_map = {str(c.restaurant_id): c for c in candidates}

        for r in result.recommendations:
            matched = cand_map.get(str(r.restaurant_id))
            if matched:
                r.address = matched.address

        return result
