"""Feature matrix builder: convert enriched attractions into a 20-dimensional feature matrix."""
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np

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


def build_feature_matrix(enriched_data: list[dict]) -> tuple[np.ndarray, list[str], list[dict]]:
    """
    Build feature matrix from enriched data.

    Returns:
        X: numpy array of shape (n_attractions, 20)
        osm_ids: list of @id strings
        meta: list of enrichment dicts (with coordinates, name, etc.)
    """
    n = len(enriched_data)
    X = np.zeros((n, len(FEATURE_KEYS)), dtype=np.float32)
    osm_ids = []
    meta = []

    # Find max price for normalization
    all_prices = [item.get("price_level", 0.0) for item in enriched_data]
    max_price = max(all_prices) if all_prices else 1.0
    if max_price == 0:
        max_price = 1.0

    for i, item in enumerate(enriched_data):
        for j, key in enumerate(FEATURE_KEYS):
            val = item.get(key, 0.0)
            # Normalize price_level to [0, 1]
            if key == "f_price_level":
                val = val / max_price
            X[i, j] = val
        osm_ids.append(item["@id"])
        meta.append(item)

    return X, osm_ids, meta


def normalize_matrix(X: np.ndarray) -> np.ndarray:
    """L2-normalize each row (required for cosine similarity via dot product)."""
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def build_and_save(enriched_path: str | Path, output_dir: str | Path) -> None:
    """Load enriched data, build feature matrix, normalize, and save artifacts."""
    with open(enriched_path, encoding="utf-8") as f:
        enriched_data = json.load(f)

    X, osm_ids, meta = build_feature_matrix(enriched_data)
    X_norm = normalize_matrix(X)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save feature matrix (normalized)
    with open(output_dir / "feature_matrix.pkl", "wb") as f:
        pickle.dump(X_norm, f)

    # Save raw feature matrix for debugging
    with open(output_dir / "feature_matrix_raw.pkl", "wb") as f:
        pickle.dump(X, f)

    # Save osm IDs
    with open(output_dir / "attraction_ids.pkl", "wb") as f:
        pickle.dump(osm_ids, f)

    # Save metadata
    with open(output_dir / "attraction_meta.pkl", "wb") as f:
        pickle.dump(meta, f)

    print(f"Feature matrix: shape={X.shape}")
    print(f"Normalized matrix saved to {output_dir / 'feature_matrix.pkl'}")
    print(f"Osm IDs ({len(osm_ids)}) saved to {output_dir / 'attraction_ids.pkl'}")

    # Print feature statistics
    print("\nFeature statistics:")
    for j, key in enumerate(FEATURE_KEYS):
        col = X[:, j]
        print(f"  {key}: min={col.min():.2f}, max={col.max():.2f}, mean={col.mean():.3f}")


if __name__ == "__main__":
    script_dir = Path(__file__).parent.parent
    enriched_path = script_dir / "data" / "enriched_data.json"
    output_dir = script_dir / "models_storage"
    build_and_save(enriched_path, output_dir)
