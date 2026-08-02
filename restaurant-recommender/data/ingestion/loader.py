"""
Dataset loader — fetches the Zomato dataset from Hugging Face.

Loads the ``ManikaSaini/zomato-restaurant-recommendation`` dataset using the
``datasets`` library and converts it to a pandas DataFrame for downstream
preprocessing.

Maps to: Architecture §3.1 — DatasetLoader component.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd
from datasets import load_dataset

if TYPE_CHECKING:
    from datasets import Dataset

logger = logging.getLogger(__name__)


class DatasetLoader:
    """Downloads and caches the Zomato restaurant dataset from Hugging Face.

    Parameters
    ----------
    dataset_name:
        Hugging Face dataset identifier.
        Defaults to the value from ``config.settings``.
    split:
        Which split to load (the dataset only has ``"train"``).
    """

    def __init__(
        self,
        dataset_name: str | None = None,
        split: str = "train",
    ) -> None:
        if dataset_name is None:
            from config.settings import settings

            dataset_name = settings.HF_DATASET_NAME
        self._dataset_name = dataset_name
        self._split = split

    # ── Public API ───────────────────────────────────────────────────────

    def load_raw(self) -> pd.DataFrame:
        """Load the dataset and return it as a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Raw, unprocessed DataFrame with the original column names from
            the Hugging Face dataset.

        Raises
        ------
        RuntimeError
            If the dataset cannot be fetched (network error, invalid name, etc.).
        """
        logger.info(
            "Loading dataset '%s' (split=%s) directly via pandas …",
            self._dataset_name,
            self._split,
        )
        try:
            from pathlib import Path
            # Load local highly-compressed parquet file for instant startup
            parquet_path = Path(__file__).parent.parent / "zomato.parquet"
            df = pd.read_parquet(parquet_path)
            
            logger.info(
                "Dataset loaded: %d rows × %d columns.",
                len(df),
                len(df.columns),
            )
            logger.debug("Columns: %s", list(df.columns))
            return df
        except Exception as exc:
            msg = (
                f"Failed to load dataset '{self._dataset_name}': {exc}"
            )
            logger.error(msg)
            raise RuntimeError(msg) from exc
