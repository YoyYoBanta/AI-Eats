"""
FastAPI application — serves the REST API and the static frontend.

Endpoints:
    GET  /api/v1/locations        → list of available locations
    GET  /api/v1/cuisines         → list of available cuisines
    POST /api/v1/recommendations  → run the recommendation pipeline
    GET  /                        → serve the frontend index.html
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from data.startup import initialise, restaurant_repo
from models.preferences import PreferenceNormalizer, UserPreference
from models.restaurant import BudgetTier
from services.recommender import RecommenderService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Lifespan: load data on startup ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the Zomato dataset into the repository at startup."""
    logger.info("Starting up — loading dataset…")
    initialise()
    logger.info("Dataset loaded. Ready to serve requests.")
    yield


# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Eats — Restaurant Recommender API",
    description="AI-powered restaurant recommendations using Groq LLM.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Schemas ──────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    location: str = Field(..., description="Location/neighbourhood to search.")
    budget: BudgetTier = Field(..., description="Budget tier: low, medium, high.")
    cuisine: str | None = Field(default=None, description="Preferred cuisine.")
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Minimum rating.")
    additional_preferences: str | None = Field(default=None, max_length=500)


class LocationsResponse(BaseModel):
    locations: list[str]


class CuisinesResponse(BaseModel):
    cuisines: list[str]


# ── API Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/v1/locations", response_model=LocationsResponse)
async def get_locations():
    """Return all available locations from the dataset."""
    locations = restaurant_repo.get_locations()
    return LocationsResponse(locations=locations)


@app.get("/api/v1/cuisines", response_model=CuisinesResponse)
async def get_cuisines():
    """Return all unique cuisines from the dataset."""
    all_restaurants = restaurant_repo.get_all()
    cuisine_set: set[str] = set()
    for r in all_restaurants:
        for c in r.cuisines:
            if c.strip():
                cuisine_set.add(c.strip())
    return CuisinesResponse(cuisines=sorted(cuisine_set))


@app.post("/api/v1/recommendations")
async def get_recommendations(req: RecommendationRequest):
    """Run the full recommendation pipeline and return results."""
    normalizer = PreferenceNormalizer(restaurant_repo.get_locations())
    
    try:
        prefs = normalizer.normalize(req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    recommender = RecommenderService(restaurant_repo)
    
    try:
        result = recommender.recommend(prefs, top_k=5)
    except Exception as e:
        logger.error("Recommendation pipeline failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {e}")

    return result.model_dump()


# ── Serve Frontend ──────────────────────────────────────────────────────────

FRONTEND_DIR = Path(__file__).parent / "frontend"


@app.get("/")
async def serve_frontend():
    """Serve the main frontend HTML file."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Frontend not found.")
