"""Fetch Chapecó traffic signals from OpenStreetMap (Overpass API) → seed CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "services" / "dbt" / "seeds" / "chapeco_intersection_locations.csv"

# Chapecó, SC bounding box (south, west, north, east)
DEFAULT_BBOX = (-27.12, -52.67, -27.06, -52.56)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def build_query(bbox: tuple[float, float, float, float]) -> str:
    south, west, north, east = bbox
    return f"""
[out:json][timeout:90];
(
  node["highway"="traffic_signals"]({south},{west},{north},{east});
);
out body;
"""


def display_name(tags: dict, node_id: int) -> str:
    for key in ("name", "name:pt", "ref", "crossing:ref"):
        value = tags.get(key)
        if value:
            return str(value)
    direction = tags.get("direction")
    if direction:
        return f"Semáforo {node_id} ({direction})"
    return f"Semáforo {node_id}"


def fetch_traffic_signals(bbox: tuple[float, float, float, float]) -> list[dict]:
    query = build_query(bbox)
    request = urllib.request.Request(
        OVERPASS_URL,
        data=query.encode("utf-8"),
        method="POST",
        headers={"User-Agent": "csmp-platform/0.1 (portfolio; local dev seed fetch)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.load(response)
    except urllib.error.URLError as exc:
        raise SystemExit(f"[fetch-osm-seed] Overpass request failed: {exc}") from exc

    rows: list[dict] = []
    for element in payload.get("elements", []):
        if element.get("type") != "node":
            continue
        node_id = int(element["id"])
        rows.append(
            {
                "intersection_id": f"osm-{node_id}",
                "display_name": display_name(element.get("tags", {}), node_id),
                "latitude": round(float(element["lat"]), 6),
                "longitude": round(float(element["lon"]), 6),
                "osm_node_id": node_id,
                "source": "osm",
            }
        )

    rows.sort(key=lambda row: row["intersection_id"])
    return rows


def write_seed_csv(rows: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "intersection_id",
        "display_name",
        "latitude",
        "longitude",
        "osm_node_id",
        "source",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch OSM traffic signals for Chapecó seed CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("SOUTH", "WEST", "NORTH", "EAST"),
        default=DEFAULT_BBOX,
    )
    args = parser.parse_args()

    rows = fetch_traffic_signals(tuple(args.bbox))
    if not rows:
        print("[fetch-osm-seed] no traffic signals found — keeping existing seed file", file=sys.stderr)
        sys.exit(1)

    write_seed_csv(rows, args.output)
    print(f"[fetch-osm-seed] wrote {len(rows)} intersections to {args.output}")


if __name__ == "__main__":
    main()
