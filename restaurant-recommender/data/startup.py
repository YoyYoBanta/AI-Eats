"""
Application startup — loads and preprocesses data once.

Call :func:`initialise` at app startup (e.g. from ``streamlit_app.py`` or
``__main__.py``) to populate the global :data:`restaurant_repo` singleton.

Usage::

    from data.startup import initialise, restaurant_repo

    initialise()                          # loads data once
    all_restaurants = restaurant_repo.get_all()
    locations = restaurant_repo.get_locations()
"""

from __future__ import annotations

import logging

from data.ingestion.loader import DatasetLoader
from data.ingestion.preprocessor import Preprocessor
from repositories.restaurant_repo import RestaurantRepository

logger = logging.getLogger(__name__)

# ── Global singleton repository ─────────────────────────────────────────────
restaurant_repo = RestaurantRepository()


def initialise(
    *,
    dataset_name: str | None = None,
    force_reload: bool = False,
) -> RestaurantRepository:
    """Load and preprocess the Zomato dataset, populating the global repository.

    This function is idempotent — subsequent calls are no-ops unless
    ``force_reload=True``.

    Parameters
    ----------
    dataset_name:
        Override the Hugging Face dataset identifier (useful for testing).
    force_reload:
        If *True*, reload even if the repository is already populated.

    Returns
    -------
    RestaurantRepository
        The populated global repository singleton.

    Raises
    ------
    RuntimeError
        If dataset loading or preprocessing fails.
    """
    if restaurant_repo.is_loaded and not force_reload:
        logger.info("Repository already loaded (%d restaurants). Skipping.", restaurant_repo.count())
        return restaurant_repo

    logger.info("Initialising data pipeline …")

    # Step 1: Load raw data
    loader = DatasetLoader(dataset_name=dataset_name)
    raw_df = loader.load_raw()

    # Step 2: Preprocess
    preprocessor = Preprocessor()
    restaurants = preprocessor.preprocess(raw_df)

    if not restaurants:
        raise RuntimeError(
            "Preprocessing produced zero valid restaurants. "
            "Check the dataset and preprocessing logic."
        )

    # Step 3: Populate repository
    restaurant_repo.load(restaurants)

    logger.info(
        "Data pipeline initialised: %d restaurants in %d locations.",
        restaurant_repo.count(),
        len(restaurant_repo.get_locations()),
    )
    return restaurant_repo
