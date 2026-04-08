"""Data enrichment: parse GeoJSON and add derived recommendation fields."""
import json
import math
import re
from pathlib import Path
from typing import Any

# Dalat city center coordinates (approximate)
DALAT_CENTER_LAT = 11.946
DALAT_CENTER_LON = 108.448

# Max distance in km for normalization (furthest attraction in dataset)
MAX_DISTANCE_KM = 15.0

# Known prices for famous attractions (osm_id prefix → price_level 0-4)
KNOWN_PRICES: dict[str, int] = {
    "Hang Nga": 2,
    "Crazy House": 2,
    "Valley of Love": 2,
    "Thung Lũng Tình Yêu": 2,
    "Dalat Market": 1,
    "Chợ Đà Lạt": 1,
    "Chợ đêm": 1,
    "Datanla": 2,
    "Thác Datanla": 2,
    "Thác Prenn": 2,
    "Prenn": 2,
    "Railway Station": 1,
    "Ga Đà Lạt": 1,
    "Clay Tunnel": 2,
    "Đường Hầm Đất": 2,
    "Robin Hill": 1,
    "Đồi Robin": 1,
    "Coffee Plantation": 2,
    "Cà Phê Mê Linh": 2,
    "Mê Linh": 2,
    "Poly": 1,
    "Lang Biang": 1,
    "Lâm Đồng": 1,
    "Cáp treo": 2,
    "Cable car": 2,
    "Aquarium": 2,
    "Thủy Cung": 2,
    "Palace": 2,
    "Dinh": 2,
}

# Estimated visiting time in minutes for known attractions
KNOWN_VISIT_TIME: dict[str, int] = {
    "Crazy House": 60,
    "Hang Nga": 60,
    "Valley of Love": 120,
    "Thung Lũng Tình Yêu": 120,
    "Datanla": 90,
    "Thác Datanla": 90,
    "Thác Prenn": 60,
    "Prenn": 60,
    "Railway Station": 30,
    "Ga Đà Lạt": 30,
    "Clay Tunnel": 45,
    "Đường Hầm Đất": 45,
    "Robin Hill": 60,
    "Đồi Robin": 60,
    "Lang Biang": 120,
    "Cable car": 45,
    "Cáp treo": 45,
    "Aquarium": 45,
    "Thủy Cung": 45,
    "Palace": 30,
    "Dinh": 30,
    "Market": 60,
    "Chợ": 60,
    "Coffee Plantation": 45,
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_centroid(geometry: dict) -> tuple[float, float]:
    """Extract centroid from geometry (Point, Polygon, MultiPolygon)."""
    gtype = geometry.get("type", "")
    if gtype == "Point":
        return geometry["coordinates"][1], geometry["coordinates"][0]
    if gtype in ("Polygon", "MultiPolygon"):
        coords = geometry["coordinates"]
        if gtype == "Polygon":
            flat = [c for ring in coords for c in ring]
        else:  # MultiPolygon
            flat = [c for poly in coords for ring in poly for c in ring]
        if not flat:
            return DALAT_CENTER_LAT, DALAT_CENTER_LON
        avg_lat = sum(c[1] for c in flat) / len(flat)
        avg_lon = sum(c[0] for c in flat) / len(flat)
        return avg_lat, avg_lon
    return DALAT_CENTER_LAT, DALAT_CENTER_LON


def _classify_indoor_outdoor(props: dict) -> tuple[int, int]:
    """
    Returns (indoor, outdoor) as 0/1 each.
    indoor=1 means mostly indoor; outdoor=1 means mostly outdoor.
    Both can be 1 for semi-outdoor (marketplace).
    """
    indoor, outdoor = 0, 0
    if props.get("building"):
        indoor = 1
    tourism = props.get("tourism", "")
    if tourism == "museum":
        indoor = 1
    amenity = props.get("amenity", "")
    if amenity == "bar":
        indoor = 1
    if amenity == "marketplace":
        indoor = 1
        outdoor = 1  # semi-outdoor
    leisure = props.get("leisure", "")
    if leisure in ("park", "garden"):
        outdoor = 1
    natural = props.get("natural", "")
    if natural:
        outdoor = 1
    if tourism == "viewpoint":
        outdoor = 1
    historic = props.get("historic", "")
    if historic in ("monument", "memorial"):
        if not props.get("building"):
            outdoor = 1
    # If neither set, default to outdoor (most Da Lat attractions are outdoors)
    if indoor == 0 and outdoor == 0:
        outdoor = 1
    return indoor, outdoor


def _calc_kid_score(props: dict) -> float:
    """Calculate kid-friendliness score 0-10."""
    score = 0.0
    leisure = props.get("leisure", "")
    if leisure == "park":
        score += 5
    elif leisure == "garden":
        score += 4
    tourism = props.get("tourism", "")
    if tourism == "attraction":
        score += 3
    elif tourism == "viewpoint":
        score += 2
    elif tourism == "museum":
        score += 2
    amenity = props.get("amenity", "")
    if amenity == "bar":
        score -= 5
    elif amenity == "marketplace":
        score -= 2
    historic = props.get("historic", "")
    if historic in ("monument", "memorial"):
        score -= 1
    # Named attractions are more established/verified
    if any(props.get(f"name:{lang}") or props.get("name") for lang in ("", "en", "vi")):
        score += 1
    else:
        score -= 1
    return max(0.0, min(10.0, score))


def _calc_weather_scores(props: dict) -> tuple[float, float]:
    """
    Returns (rainy_score, sunny_score) each 0-10.
    rainy_score: how suitable for rainy/cloudy weather (higher = better)
    sunny_score: how suitable for sunny weather (higher = better)
    """
    indoor, outdoor = _classify_indoor_outdoor(props)
    leisure = props.get("leisure", "")
    tourism = props.get("tourism", "")
    amenity = props.get("amenity", "")

    # Base from indoor/outdoor
    rainy_base = indoor * 8
    sunny_base = outdoor * 6

    # Type adjustments
    if amenity == "marketplace":
        rainy_base = 6  # covered market is great for rain
        sunny_base = 3  # can be hot inside
    if tourism == "viewpoint":
        sunny_base = 7  # viewpoints best in clear/sunny weather
        rainy_base = 1  # fog/rain ruins views
    if leisure in ("park", "garden"):
        sunny_base = 6  # great for picnics in sun
        rainy_base = 3  # muddy but still visitable

    return (
        max(0.0, min(10.0, rainy_base)),
        max(0.0, min(10.0, sunny_base)),
    )


def _estimate_price_level(props: dict, name: str) -> float:
    """Estimate price level 0-4. Higher = more expensive."""
    # Check known attractions
    for key, price in KNOWN_PRICES.items():
        if key.lower() in name.lower():
            return float(price)

    # Type-based defaults
    tourism = props.get("tourism", "")
    leisure = props.get("leisure", "")
    amenity = props.get("amenity", "")
    historic = props.get("historic", "")

    if amenity == "marketplace":
        return 1.0
    if tourism == "museum":
        return 2.0
    if tourism == "attraction":
        return 2.5
    if leisure in ("park", "garden"):
        return 0.5
    if historic in ("monument", "memorial"):
        return 0.0
    if tourism == "viewpoint":
        return 0.5
    # Generic
    return 1.0


def _parse_opening_hours(props: dict) -> dict:
    """Parse opening_hours tag into structured fields."""
    oh = props.get("opening_hours", "")
    result = {
        "has_opening_hours": 0,
        "weekend_open": 0,
        "opens_early": 0,
        "closes_late": 0,
    }
    if not oh:
        return result

    result["has_opening_hours"] = 1
    oh_lower = oh.lower()

    # Weekend open: Mo-Su or explicitly includes weekend
    if "mo-su" in oh_lower or "mo-fr" not in oh_lower and any(
        d in oh_lower for d in ("sa", "su", "weekend")
    ):
        result["weekend_open"] = 1

    # Parse time ranges like "07:30-17:00"
    times = re.findall(r"(\d{1,2}):(\d{2})", oh)
    if times:
        hours = [int(t[0]) + int(t[1]) / 60 for t in times]
        if hours:
            open_time = min(hours)
            close_time = max(hours)
            if open_time < 8.0:
                result["opens_early"] = 1
            if close_time > 18.0:
                result["closes_late"] = 1

    return result


def _estimate_visit_time(props: dict, name: str, tourism: str, leisure: str) -> int:
    """Estimate typical visiting time in minutes."""
    # Check known attractions
    name_lower = name.lower()
    for key, minutes in KNOWN_VISIT_TIME.items():
        if key.lower() in name_lower:
            return minutes

    # Type-based defaults
    if tourism == "museum":
        return 60
    if leisure in ("park", "garden"):
        return 45
    if tourism == "attraction":
        return 60
    if tourism == "viewpoint":
        return 30
    if props.get("amenity") == "marketplace":
        return 60
    if props.get("historic") in ("monument", "memorial"):
        return 20
    return 30


def _classify_category(props: dict) -> str:
    """Classify attraction into a broad category."""
    tourism = props.get("tourism", "")
    leisure = props.get("leisure", "")
    amenity = props.get("amenity", "")
    historic = props.get("historic", "")
    natural = props.get("natural", "")
    waterway = props.get("waterway", "")

    if leisure in ("park", "garden"):
        return "park"
    if tourism == "museum":
        return "museum"
    if tourism == "viewpoint":
        return "viewpoint"
    if amenity == "marketplace":
        return "market"
    if historic in ("monument", "memorial", "archaeological", "building"):
        return "historic"
    if tourism == "attraction":
        return "attraction"
    if waterway == "waterfall":
        return "nature"
    if natural:
        return "nature"
    if amenity == "bar":
        return "nightlife"
    return "other"


def _get_primary_type(props: dict) -> str:
    """Return the most specific OSM type for display."""
    tourism = props.get("tourism", "")
    leisure = props.get("leisure", "")
    amenity = props.get("amenity", "")
    historic = props.get("historic", "")
    natural = props.get("natural", "")
    waterway = props.get("waterway", "")

    return waterway or natural or historic or tourism or leisure or amenity or "unknown"


def _build_name(props: dict) -> tuple[str, str, str]:
    """Return (name, name_vi, name_en) preferring available translations."""
    name = props.get("name", "")
    name_vi_raw = props.get("name:vi", "")
    name_en_raw = props.get("name:en", "")

    # NOTE: In this dataset, 'name' is Vietnamese, but 'name:vi' is actually
    # the English translation (a quirk of the OSM export).
    # So: name:vi field -> use as English name
    #     name field -> use as Vietnamese name
    name_en = name_en_raw or name_vi_raw  # prefer explicit English, else use name:vi (English translation)
    name_vi = name  # 'name' is Vietnamese

    if not name_en:
        name_en = name_vi
    if not name_vi:
        name_vi = name_en
    if not name:
        primary = _get_primary_type(props)
        name = f"Unnamed {primary.title()}"
        name_vi = name
        name_en = name_en or name

    return name, name_vi, name_en


def _build_address(props: dict) -> str:
    """Build a display address from available address fields."""
    parts = []
    if props.get("addr:street"):
        hn = props.get("addr:housenumber", "")
        parts.append(f"{hn} {props['addr:street']}".strip() if hn else props["addr:street"])
    if props.get("addr:subdistrict"):
        parts.append(props["addr:subdistrict"])
    if props.get("addr:district"):
        parts.append(props["addr:district"])
    city = props.get("addr:city") or props.get("addr:province") or "Da Lat"
    if city not in parts:
        parts.append(city)
    return ", ".join(parts) if parts else ""


def enrich_feature(props: dict, geometry: dict) -> dict:
    """Enrich a single GeoJSON feature with derived recommendation fields."""
    lat, lon = _get_centroid(geometry)
    distance_km = _haversine(DALAT_CENTER_LAT, DALAT_CENTER_LON, lat, lon)

    name, name_vi, name_en = _build_name(props)
    tourism = props.get("tourism", "")
    leisure = props.get("leisure", "")
    amenity = props.get("amenity", "")
    historic = props.get("historic", "")

    indoor, outdoor = _classify_indoor_outdoor(props)
    kid_score = _calc_kid_score(props)
    rainy_score, sunny_score = _calc_weather_scores(props)
    price_level = _estimate_price_level(props, name)
    oh_fields = _parse_opening_hours(props)
    category = _classify_category(props)
    primary_type = _get_primary_type(props)
    visit_time = _estimate_visit_time(props, name, tourism, leisure)
    address = _build_address(props)

    # Indoor/outdoor string for display
    if indoor and outdoor:
        indoor_outdoor = "both"
    elif indoor:
        indoor_outdoor = "indoor"
    else:
        indoor_outdoor = "outdoor"

    # Tourism one-hot
    tourism_attraction = 1 if tourism == "attraction" else 0
    tourism_museum = 1 if tourism == "museum" else 0
    tourism_viewpoint = 1 if tourism == "viewpoint" else 0
    tourism_other = 1 if tourism and tourism not in ("attraction", "museum", "viewpoint") else 0

    # Leisure one-hot
    leisure_park = 1 if leisure == "park" else 0
    leisure_garden = 1 if leisure == "garden" else 0

    # Historic
    is_historic = 1 if historic in ("monument", "memorial") else 0

    return {
        "@id": props.get("@id", ""),
        "name": name,
        "name:vi": name_vi,
        "name:en": name_en,
        "category": category,
        "primary_type": primary_type,
        "tourism": tourism,
        "leisure": leisure,
        "amenity": amenity,
        "historic": historic,
        "indoor_outdoor": indoor_outdoor,
        "indoor": indoor,
        "outdoor": outdoor,
        "kid_score": kid_score,
        "weather_rainy_score": rainy_score,
        "weather_sunny_score": sunny_score,
        "price_level": price_level,
        "has_opening_hours": oh_fields["has_opening_hours"],
        "opening_hours": props.get("opening_hours", ""),
        "weekend_open": oh_fields["weekend_open"],
        "opens_early": oh_fields["opens_early"],
        "closes_late": oh_fields["closes_late"],
        "distance_km": round(distance_km, 2),
        "distance_normalized": round(distance_km / MAX_DISTANCE_KM, 4),
        "has_name": 1 if name and "Unnamed" not in name else 0,
        "address": address,
        "phone": props.get("phone", ""),
        "website": props.get("website", ""),
        "coordinates": [lon, lat],
        "geometry_type": geometry.get("type", ""),
        "estimated_visit_min": visit_time,
        # Feature matrix inputs
        "f_tourism_attraction": tourism_attraction,
        "f_tourism_museum": tourism_museum,
        "f_tourism_viewpoint": tourism_viewpoint,
        "f_tourism_other": tourism_other,
        "f_leisure_park": leisure_park,
        "f_leisure_garden": leisure_garden,
        "f_amenity_marketplace": 1 if amenity == "marketplace" else 0,
        "f_historic_monument": is_historic,
        "f_indoor": indoor,
        "f_outdoor": outdoor,
        "f_kid_score": kid_score,
        "f_weather_rainy_score": rainy_score,
        "f_weather_sunny_score": sunny_score,
        "f_price_level": price_level,
        "f_has_opening_hours": oh_fields["has_opening_hours"],
        "f_weekend_open": oh_fields["weekend_open"],
        "f_opens_early": oh_fields["opens_early"],
        "f_closes_late": oh_fields["closes_late"],
        "f_distance_normalized": round(distance_km / MAX_DISTANCE_KM, 4),
        "f_has_name": 1 if name and "Unnamed" not in name else 0,
    }


def enrich_geojson(input_path: str | Path, output_path: str | Path) -> list[dict]:
    """Load GeoJSON, enrich all features, save to output path. Returns enriched list."""
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    enriched = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if not geometry:
            continue
        enriched_feature = enrich_feature(props, geometry)
        # Attach original geometry for map rendering
        enriched_feature["_geometry"] = geometry
        enriched.append(enriched_feature)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    return enriched


if __name__ == "__main__":
    script_dir = Path(__file__).parent.parent
    input_file = script_dir.parent / "dataset" / "data.geojson"
    output_file = script_dir / "data" / "enriched_data.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    enriched = enrich_geojson(input_file, output_file)
    print(f"Enriched {len(enriched)} attractions -> {output_file}")

    # Summary stats
    categories = {}
    for e in enriched:
        cat = e["category"]
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
