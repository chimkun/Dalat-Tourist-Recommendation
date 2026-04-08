"""Test script for the Da Lat Recommendation API."""
import sys

# Fix Windows console encoding to UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(__file__).replace("\\", "/").rsplit("/", 1)[0] + "/..")

from backend.main import load_recommender

# Load the recommender
r = load_recommender()
print(f"Loaded {r.n_attractions} attractions")
print(f"Categories: {list(r.get_categories().keys())}")
print()

# Test 1: sunny + kids + low budget + park
print("=" * 60)
print("TEST 1: sunny + kids + low budget + park")
print("=" * 60)
results = r.recommend(
    weather="sunny",
    has_kids=True,
    budget="low",
    category="park",
    limit=5
)
for i, item in enumerate(results, 1):
    print(f"\n{i}. {item['name:en']}")
    print(f"   Category: {item['category']}")
    print(f"   Coordinates: {item['coordinates']}")
    print(f"   Score: {round(item['score'], 3)}")
    print(f"   Reason: {item['reason']}")

# Test 2: rainy + no kids + high budget + museum
print()
print("=" * 60)
print("TEST 2: rainy + no kids + high budget + museum")
print("=" * 60)
results = r.recommend(
    weather="rainy",
    has_kids=False,
    budget="high",
    category="museum",
    limit=5
)
for i, item in enumerate(results, 1):
    print(f"\n{i}. {item['name:en']}")
    print(f"   Category: {item['category']}")
    print(f"   Coordinates: {item['coordinates']}")
    print(f"   Score: {round(item['score'], 3)}")
    print(f"   Reason: {item['reason']}")

# Test 3: All categories top 3 each
print()
print("=" * 60)
print("TEST 3: All categories - top 3 each")
print("=" * 60)
for cat in r.get_categories().keys():
    results = r.recommend(weather="sunny", has_kids=False, budget="medium",
                          category=cat, limit=3)
    print(f"\n{cat.upper()}:")
    for item in results:
        print(f"  - {item['name:en']} (score={round(item['score'], 3)}, "
              f"coords={item['coordinates']})")

# Test 4: List all attractions
print()
print("=" * 60)
print("TEST 4: All attractions (first 10)")
print("=" * 60)
all_items = r.get_all_attractions(limit=10)
for i, item in enumerate(all_items, 1):
    print(f"{i}. {item['name:en']} | {item['category']} | "
          f"{item['coordinates']} | indoor={item['indoor_outdoor']} | "
          f"kids={item['kid_score']} | price={item['price_level']}")

print()
print("All tests completed!")
