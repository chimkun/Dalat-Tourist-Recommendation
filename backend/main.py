"""FastAPI backend for Da Lat Tourist Recommendation System."""
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.models.recommender import Recommender

# Paths (relative to this file's location)
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models_storage"

# Global recommender instance (loaded once at startup)
recommender: Optional[Recommender] = None


# ─── Pydantic schemas ──────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    weather: str = Field(default="sunny", pattern="^(sunny|rainy|cloudy)$")
    has_kids: bool = Field(default=False)
    kid_count: int = Field(default=1, ge=1, le=5)
    budget: str = Field(default="medium", pattern="^(low|medium|high)$")
    time_available: float = Field(default=2.0, ge=0.5, le=12.0)
    category: str = Field(default="all")
    max_distance_km: Optional[float] = Field(default=None, ge=1.0, le=50.0)
    limit: int = Field(default=10, ge=1, le=50)


class Recommendation(BaseModel):
    osm_id: str
    name: str
    name_vi: str = Field(alias="name:vi")
    name_en: str = Field(alias="name:en")
    category: str
    primary_type: str
    score: float
    reason: str
    indoor_outdoor: str
    kid_score: float
    weather_rainy_score: float
    weather_sunny_score: float
    price_level: float
    coordinates: list[float]
    address: str
    opening_hours: str
    estimated_visit_min: int
    distance_km: float
    phone: str
    website: str
    has_name: bool

    class Config:
        populate_by_name = True


class RecommendResponse(BaseModel):
    recommendations: list[dict]
    total: int
    filters_applied: dict


class AttractionResponse(BaseModel):
    osm_id: str
    name: str
    name_vi: str = Field(alias="name:vi")
    name_en: str = Field(alias="name:en")
    category: str
    primary_type: str
    indoor_outdoor: str
    kid_score: float
    price_level: float
    coordinates: list[float]
    address: str
    opening_hours: str
    estimated_visit_min: int
    distance_km: float
    phone: str
    website: str

    class Config:
        populate_by_name = True


# ─── App lifecycle ────────────────────────────────────────────────────────────

def load_recommender() -> Recommender:
    """Load the recommender model on startup."""
    return Recommender(
        feature_matrix_path=MODEL_DIR / "feature_matrix.pkl",
        attraction_ids_path=MODEL_DIR / "attraction_ids.pkl",
        attraction_meta_path=MODEL_DIR / "attraction_meta.pkl",
    )


# ─── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Da Lat Tourist Recommendation API",
    description="ML-powered tourist attraction recommendation for Da Lat, Vietnam",
    version="1.0.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    global recommender
    recommender = load_recommender()
    print(f"Loaded {recommender.n_attractions} attractions")


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/categories")
def get_categories() -> dict:
    """Return available attraction categories and their primary types."""
    if recommender is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return recommender.get_categories()


@app.get("/api/attractions")
def get_attractions(
    category: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """Return all attractions, optionally filtered by category."""
    if recommender is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    results = recommender.get_all_attractions(category=category, limit=limit)
    return {"attractions": results, "total": len(results)}


@app.get("/api/attraction/{osm_id}")
def get_attraction(osm_id: str) -> dict:
    """Return a single attraction by OSM ID."""
    if recommender is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    for meta in recommender.meta:
        if meta["@id"] == osm_id:
            return meta
    raise HTTPException(status_code=404, detail=f"Attraction '{osm_id}' not found")


@app.post("/api/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest) -> dict:
    """
    Core recommendation endpoint.
    Takes user preferences and returns ranked attractions with scores and reasons.
    """
    if recommender is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    results = recommender.recommend(
        weather=request.weather,
        has_kids=request.has_kids,
        kid_count=request.kid_count,
        budget=request.budget,
        time_available=request.time_available,
        category=request.category,
        max_distance_km=request.max_distance_km,
        limit=request.limit,
    )

    return {
        "recommendations": results,
        "total": len(results),
        "filters_applied": {
            "weather": request.weather,
            "has_kids": request.has_kids,
            "kid_count": request.kid_count,
            "budget": request.budget,
            "time_available": request.time_available,
            "category": request.category,
            "max_distance_km": request.max_distance_km,
        },
    }


# ─── Run locally ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
