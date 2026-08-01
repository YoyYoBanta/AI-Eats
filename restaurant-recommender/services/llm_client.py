"""
Groq LLM Client.

Wraps the Groq Python SDK for chat completions, enforcing
JSON output formats.
"""

from __future__ import annotations

import logging

from groq import Groq

from config.settings import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper around the Groq API for chat completions."""

    def __init__(self, api_key: str | None = None) -> None:
        # Favour explicit parameter over environment setting
        key = api_key if api_key is not None else settings.GROQ_API_KEY.get_secret_value()
        
        if not key:
            # Allow instantiation without key for tests (mocking), 
            # but log a warning.
            logger.warning("GROQ_API_KEY is not set.")
            
        self.model = settings.LLM_MODEL
        self.timeout = settings.LLM_TIMEOUT_SECONDS
        
        self.client = Groq(
            api_key=key,
            timeout=self.timeout,
        )

    def get_recommendations(self, prompt: str) -> str:
        """Send the prompt to the Groq LLM and return the JSON string response.

        Parameters
        ----------
        prompt:
            The fully assembled prompt text.

        Returns
        -------
        str
            Raw JSON string from the LLM.

        Raises
        ------
        Exception
            If the API call fails or times out.
        """
        logger.info("Sending prompt to Groq model: %s", self.model)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.3,  # Low temperature for consistent JSON output
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        
        result = response.choices[0].message.content
        if not result:
            raise ValueError("Groq returned an empty response.")
            
        if response.usage:
            logger.info(
                "Groq response received. Tokens: prompt=%s, completion=%s",
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
            )
            
        return result
