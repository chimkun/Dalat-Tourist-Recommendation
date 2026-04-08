"""List all unique names in data.geojson so user knows what to delete."""
import json
from collections import Counter

with open("dataset/data.geojson", encoding="utf-8") as f:
    data = json.load(f)

names = [
    f.get("properties", {}).get("name", "")
    for f in data.get("features", [])
]
names = [n for n in names if n]

duplicates = {name: count for name, count in Counter(names).items() if count > 1}

with open("backend/duplicate_names.txt", "w", encoding="utf-8") as out:
    out.write(f"Total features: {len(data['features'])}\n")
    out.write(f"Unique names: {len(set(names))}\n")
    out.write(f"Duplicate names: {len(duplicates)}\n\n")
    if duplicates:
        out.write("Duplicate names (one per line for delete.txt):\n")
        for name, count in sorted(duplicates.items()):
            out.write(f"x{count}: {name}\n")
        out.write("\nLines below for delete.txt:\n")
        for name in sorted(duplicates.keys()):
            out.write(f"{name}\n")
    else:
        out.write("No duplicate names found.\n")

print(f"Total: {len(data['features'])}, Unique: {len(set(names))}, Duplicates: {len(duplicates)}")
print(f"Results written to backend/duplicate_names.txt")
