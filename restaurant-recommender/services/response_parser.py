"""
LLM JSON response parsing.

Validates the raw JSON string returned by Groq against the
RecommendationList Pydantic schema.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from models.recommendation import RecommendationList

logger = logging.getLogger(__name__)


class ResponseParser:
    """Parses and validates LLM JSON output against our Pydantic schemas."""

    def parse(
        self, raw_json: str, metadata: dict[str, Any] | None = None
    ) -> RecommendationList:
        """Parse raw LLM output into a RecommendationList.

        Parameters
        ----------
        raw_json:
            The JSON string returned by the LLM.
        metadata:
            Optional metadata to attach (e.g. candidates considered, filters applied).

        Returns
        -------
        RecommendationList
            The validated recommendation model.

        Raises
        ------
        ValueError
            If the raw string is not valid JSON.
        ValidationError
            If the JSON does not match the expected schema.
        """
        try:
            parsed_data = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode JSON from LLM: %s", exc)
            logger.debug("Raw output was: %s", raw_json)
            raise ValueError(f"LLM did not return valid JSON: {exc}") from exc

        if metadata:
            parsed_data["metadata"] = metadata

        try:
            return RecommendationList(**parsed_data)
        except ValidationError as exc:
            logger.error("LLM JSON failed schema validation: %s", exc)
            logger.debug("Parsed JSON was: %s", parsed_data)
            raise
