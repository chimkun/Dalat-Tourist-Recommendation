"""Content-based recommender using cosine similarity on feature vectors."""
import pickle
from pathlib import Path
from typing import Optional

import numpy as np

# Feature index mapping (matches features.py FEATURE_KEYS order)
FEATURE_KEYS = [
    "f_tourism_attraction",
    "f_tourism_museum",
    "f_tourism_viewpoint",
    "f_tourism_other",
    "f_leisure_park",
    "f_leisure_garden",
    "f_amenity_marketplace",
    "f_historic_monument",
    "f_indoor",
    "f_outdoor",
    "f_kid_score",
    "f_weather_rainy_score",
    "f_weather_sunny_score",
    "f_price_level",
    "f_has_opening_hours",
    "f_weekend_open",
    "f_opens_early",
    "f_closes_late",
    "f_distance_normalized",
    "f_has_name",
]


class Recommender:
    """Content-based cosine similarity recommender."""

    def __init__(
        self,
        feature_matrix_path: str | Path,
        attraction_ids_path: str | Path,
        attraction_meta_path: str | Path,
    ):
        with open(feature_matrix_path, "rb") as f:
            self.X_norm: np.ndarray = pickle.load(f)

        with open(attraction_ids_path, "rb") as f:
            self.osm_ids: list[str] = pickle.load(f)

        with open(attraction_meta_path, "rb") as f:
            self.meta: list[dict] = pickle.load(f)

        self.n_attractions = len(self.osm_ids)

    def build_preference_vector(
        self,
        weather: str,
        has_kids: bool,
        kid_count: int = 1,
        budget: float = 200000.0,
        time_available: float = 2.0,
        category: str = "all",
        max_distance_km: Optional[float] = None,
    ) -> np.ndarray:
        """
        Build a user preference vector in the same 20-d feature space.
        This vector is NOT normalized — we use it for dot-product scoring against
        the pre-normalized attraction vectors.
        """
        P = np.zeros(len(FEATURE_KEYS), dtype=np.float32)

        # --- Category preferences ---
        cat = category.lower() if category else "all"
        if cat == "museum":
            P[FEATURE_KEYS.index("f_tourism_museum")] = 1.0
        elif cat == "park" or cat == "garden":
            P[FEATURE_KEYS.index("f_leisure_park")] = 1.0
            P[FEATURE_KEYS.index("f_leisure_garden")] = 1.0
        elif cat == "viewpoint":
            P[FEATURE_KEYS.index("f_tourism_viewpoint")] = 1.0
        elif cat == "market":
            P[FEATURE_KEYS.index("f_amenity_marketplace")] = 1.0
        elif cat == "historic":
            P[FEATURE_KEYS.index("f_historic_monument")] = 1.0
        elif cat == "attraction":
            P[FEATURE_KEYS.index("f_tourism_attraction")] = 1.0
        elif cat == "nature":
            P[FEATURE_KEYS.index("f_outdoor")] = 1.0
        # "all" → no category boost

        # --- Weather preferences ---
        # rainy/cloudy → boost indoor and weather_rainy_score
        # sunny → boost outdoor and weather_sunny_score
        weather_idx_rainy = FEATURE_KEYS.index("f_weather_rainy_score")
        weather_idx_sunny = FEATURE_KEYS.index("f_weather_sunny_score")
        indoor_idx = FEATURE_KEYS.index("f_indoor")
        outdoor_idx = FEATURE_KEYS.index("f_outdoor")

        if weather in ("rainy", "cloudy"):
            P[weather_idx_rainy] = 1.0
            P[indoor_idx] = 0.5  # soft boost for indoor venues
            P[weather_idx_sunny] = 0.0
            P[outdoor_idx] = -0.3  # slight penalty for outdoor
        elif weather == "sunny":
            P[weather_idx_sunny] = 1.0
            P[outdoor_idx] = 0.5
            P[weather_idx_rainy] = 0.0
            P[indoor_idx] = -0.3
        else:
            # Default: no weather bias
            P[weather_idx_rainy] = 0.3
            P[weather_idx_sunny] = 0.3

        # --- Kid preferences ---
        if has_kids:
            P[FEATURE_KEYS.index("f_kid_score")] = 1.0 * min(kid_count, 3)
            # Parks/gardens are great for kids
            P[FEATURE_KEYS.index("f_leisure_park")] += 0.3
            P[FEATURE_KEYS.index("f_leisure_garden")] += 0.2
        else:
            P[FEATURE_KEYS.index("f_kid_score")] = 0.0

        # --- Budget preferences ---
        # Budget is now the user's max price in VND (hard filter already applied).
        # We keep the price feature neutral in the preference vector.
        # budget_idx = FEATURE_KEYS.index("f_price_level")
        # P[budget_idx] = 0.0  # neutral — hard filter handles it

        # --- Time availability ---
        # Close-late venues better for short visits, opens-early for long days
        if time_available <= 1.5:
            P[FEATURE_KEYS.index("f_closes_late")] = 0.3
        elif time_available >= 4.0:
            P[FEATURE_KEYS.index("f_weekend_open")] = 0.2
            P[FEATURE_KEYS.index("f_opens_early")] = 0.2

        # --- Distance preference ---
        dist_idx = FEATURE_KEYS.index("f_distance_normalized")
        if max_distance_km is not None and max_distance_km > 0:
            # Invert: lower distance_normalized is better
            # We encode this negatively so dot product penalizes distant places
            P[dist_idx] = -1.0
        else:
            P[dist_idx] = 0.0

        # --- Named attractions are more reliable ---
        P[FEATURE_KEYS.index("f_has_name")] = 0.2

        return P

    def score(self, preference_vector: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity scores between preference vector and all attractions.
        Uses dot product since attraction vectors are L2-normalized.
        """
        # Normalize the preference vector too
        norm = np.linalg.norm(preference_vector)
        if norm == 0:
            return np.zeros(self.n_attractions)
        P_norm = preference_vector / norm
        return np.dot(self.X_norm, P_norm)

    def recommend(
        self,
        weather: str = "sunny",
        has_kids: bool = False,
        kid_count: int = 1,
        budget: float = 200000.0,
        time_available: float = 2.0,
        category: str = "all",
        max_distance_km: Optional[float] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Main recommendation method. Returns a ranked list of attraction dicts.

        budget: max price in VND the user is willing to pay.
        price_level in metadata is already in VND.
        """
        # price_upper is the user's max budget in VND
        price_upper = budget
        # price_lower is 0 (no minimum)

        # Max distance filter (km)
        max_dist = max_distance_km if max_distance_km is not None else 20.0

        P = self.build_preference_vector(
            weather=weather,
            has_kids=has_kids,
            kid_count=kid_count,
            budget=budget,
            time_available=time_available,
            category=category,
            max_distance_km=max_distance_km,
        )
        raw_scores = self.score(P)

        # Build result list with hard filters
        filtered_indices = []
        for i in range(self.n_attractions):
            meta = self.meta[i]

            # Hard filter: price must be within budget (price_lower=0, price_upper=budget in VND)
            price = meta.get("price_level", 10000.0)
            if price > price_upper:
                continue  # HARD SKIP

            # Hard filter: distance
            dist = meta.get("distance_km", 0.0)
            if dist > max_dist:
                continue  # HARD SKIP

            # Hard filter: category must match requested category
            if category and category != "all":
                if meta.get("category") != category:
                    continue  # HARD SKIP

            filtered_indices.append(i)

        # Sort filtered indices by score (descending)
        filtered_scores = raw_scores[filtered_indices]
        sorted_order = np.argsort(filtered_scores)[::-1]
        top_indices = [filtered_indices[i] for i in sorted_order[:limit]]

        results = []
        for idx in top_indices:
            meta = self.meta[idx]
            score = float(raw_scores[idx])
            reason = self._generate_reason(meta, weather, has_kids, budget)
            results.append(
                {
                    "osm_id": meta["@id"],
                    "name": meta["name"],
                    "name:vi": meta.get("name:vi", meta["name"]),
                    "name:en": meta.get("name:en", meta["name"]),
                    "category": meta["category"],
                    "primary_type": meta.get("primary_type", ""),
                    "score": round(score, 3),
                    "reason": reason,
                    "indoor_outdoor": meta.get("indoor_outdoor", "outdoor"),
                    "kid_score": meta.get("kid_score", 0),
                    "weather_rainy_score": meta.get("weather_rainy_score", 0),
                    "weather_sunny_score": meta.get("weather_sunny_score", 0),
                    "price_level": meta.get("price_level", 1),
                    "coordinates": meta.get("coordinates", []),
                    "address": meta.get("address", ""),
                    "opening_hours": meta.get("opening_hours", ""),
                    "estimated_visit_min": meta.get("estimated_visit_min", 30),
                    "distance_km": meta.get("distance_km", 0),
                    "phone": meta.get("phone", ""),
                    "website": meta.get("website", ""),
                    "has_name": meta.get("has_name", 0) == 1,
                    "geometry": meta.get("_geometry", {}),
                }
            )

        return results

    def _generate_reason(
        self, meta: dict, weather: str, has_kids: bool, budget: str
    ) -> str:
        """Generate a human-readable reason for the recommendation."""
        reasons = []
        cat = meta.get("category", "")
        name = meta.get("name", "this place")

        if has_kids and meta.get("kid_score", 0) >= 5:
            reasons.append("Great for kids")
        elif has_kids and meta.get("kid_score", 0) >= 3:
            reasons.append("Kid-friendly")

        if weather in ("rainy", "cloudy") and meta.get("indoor_outdoor") == "indoor":
            reasons.append("Perfect for rainy weather — indoor venue")
        elif weather in ("rainy", "cloudy") and meta.get("indoor_outdoor") == "both":
            reasons.append("Good for rainy days — covered area available")
        elif weather == "sunny" and meta.get("indoor_outdoor") == "outdoor":
            reasons.append("Best enjoyed in sunny weather")
        elif weather == "sunny" and meta.get("indoor_outdoor") == "both":
            reasons.append("Great for sunny days with shaded areas")

        price = meta.get("price_level", 1)
        if budget == "low" and price <= 1:
            reasons.append("Budget-friendly")
        elif budget == "low" and price <= 2:
            reasons.append("Moderate cost")
        elif budget == "high" and price >= 3:
            reasons.append("Premium experience")

        if meta.get("has_opening_hours") == 1:
            if meta.get("weekend_open") == 1:
                reasons.append("Open on weekends")
            if meta.get("closes_late") == 1:
                reasons.append("Open late")

        if cat == "park":
            reasons.append("Beautiful green space")
        elif cat == "viewpoint":
            reasons.append("Scenic views")
        elif cat == "museum":
            reasons.append("Cultural & educational")
        elif cat == "market":
            reasons.append("Local shopping & food")

        if not reasons:
            reasons.append(f"Popular {cat} attraction in Da Lat")

        return " • ".join(reasons[:3])  # Max 3 reasons

    def get_all_attractions(self, category: Optional[str] = None, limit: int = 50) -> list[dict]:
        """Return all attractions, optionally filtered by category."""
        results = []
        for meta in self.meta:
            if category and category != "all" and meta.get("category") != category:
                continue
            results.append(
                {
                    "osm_id": meta["@id"],
                    "name": meta["name"],
                    "name:vi": meta.get("name:vi", meta["name"]),
                    "name:en": meta.get("name:en", meta["name"]),
                    "category": meta["category"],
                    "primary_type": meta.get("primary_type", ""),
                    "indoor_outdoor": meta.get("indoor_outdoor", "outdoor"),
                    "kid_score": meta.get("kid_score", 0),
                    "price_level": meta.get("price_level", 1),
                    "coordinates": meta.get("coordinates", []),
                    "address": meta.get("address", ""),
                    "opening_hours": meta.get("opening_hours", ""),
                    "estimated_visit_min": meta.get("estimated_visit_min", 30),
                    "distance_km": meta.get("distance_km", 0),
                    "phone": meta.get("phone", ""),
                    "website": meta.get("website", ""),
                    "geometry": meta.get("_geometry", {}),
                }
            )
            if limit and len(results) >= limit:
                break
        return results

    def get_categories(self) -> dict[str, list[str]]:
        """Return available categories and their primary types."""
        categories: dict[str, set] = {}
        for meta in self.meta:
            cat = meta.get("category", "other")
            ptype = meta.get("primary_type", "")
            if cat not in categories:
                categories[cat] = set()
            if ptype:
                categories[cat].add(ptype)
        return {cat: sorted(types) for cat, types in sorted(categories.items())}
