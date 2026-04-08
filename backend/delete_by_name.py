"""Delete entries from data.geojson by names listed in a text file (one name per line)."""
import json
import sys

if len(sys.argv) < 2:
    print("Usage: python delete_by_name.py <names.txt>")
    sys.exit(1)

names_file = sys.argv[1]
input_path = "dataset/data.geojson"

# Read names to delete from text file
with open(names_file, encoding="utf-8") as f:
    names_to_delete = {line.strip() for line in f if line.strip()}

print(f"Loaded {len(names_to_delete)} name(s) to delete")

with open(input_path, encoding="utf-8") as f:
    data = json.load(f)

original_count = len(data.get("features", []))
data["features"] = [
    f
    for f in data.get("features", [])
    if f.get("properties", {}).get("name") not in names_to_delete
]

removed_count = original_count - len(data["features"])

with open(input_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Removed {removed_count} entry(ies)")
print(f"Remaining features: {len(data['features'])}")
