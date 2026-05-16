from __future__ import annotations

import math
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from review_processing_utils import ANALYSIS_PUBLIC_DIR, REPORT_ANALYSIS_DIR, write_csv, write_text


LOCATION_CATALOG_CSV = ANALYSIS_PUBLIC_DIR / "event_location_catalog_gis.csv"
LOCATION_NODES_CSV = ANALYSIS_PUBLIC_DIR / "location_nodes.csv"
LOCATION_DISTANCE_MATRIX_CSV = ANALYSIS_PUBLIC_DIR / "location_distance_matrix.csv"
GIS_DISTANCE_REPORT_MD = REPORT_ANALYSIS_DIR / "gis_distance_matrix_report.md"

WALK_SPEED_KMPH = 4.8
FALLBACK_ROUTE_FACTOR = 1.3


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6_371_008.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def walk_minutes(distance_m: float | None) -> float | None:
    if distance_m is None or pd.isna(distance_m):
        return None
    meters_per_minute = WALK_SPEED_KMPH * 1000 / 60
    return round(float(distance_m) / meters_per_minute, 2)


def boolean_text(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def build_location_nodes(catalog: pd.DataFrame) -> pd.DataFrame:
    nodes = catalog.copy()
    nodes["location_key"] = nodes["normalized_studio_key"].astype(str)
    nodes["location_node_id"] = [f"loc_{index:03d}" for index in range(1, len(nodes) + 1)]
    nodes["latitude"] = pd.to_numeric(nodes["latitude"], errors="coerce")
    nodes["longitude"] = pd.to_numeric(nodes["longitude"], errors="coerce")
    columns = [
        "location_node_id",
        "location_key",
        "display_name",
        "address",
        "latitude",
        "longitude",
        "location_source",
        "source_detail",
        "geocode_method",
        "geocode_confidence",
        "needs_manual_verification",
        "notes",
    ]
    return nodes[columns].sort_values("location_key").reset_index(drop=True)


def try_osmnx_lengths(nodes: pd.DataFrame) -> tuple[dict[tuple[str, str], float], str]:
    valid = nodes[nodes["latitude"].notna() & nodes["longitude"].notna()].copy()
    if valid.empty:
        return {}, "skipped:no_valid_coordinates"

    try:
        import networkx as nx
        import osmnx as ox
    except Exception as exc:  # pragma: no cover - optional dependency
        return {}, f"unavailable:{type(exc).__name__}:{exc}"

    try:
        center_lat = float(valid["latitude"].mean())
        center_lon = float(valid["longitude"].mean())
        max_center_distance = max(
            haversine_m(center_lat, center_lon, float(row["latitude"]), float(row["longitude"]))
            for _, row in valid.iterrows()
        )
        graph_radius_m = max(2_000, min(6_000, int(max_center_distance + 1_500)))

        ox.settings.use_cache = True
        ox.settings.log_console = False
        ox.settings.requests_timeout = 90
        graph = ox.graph_from_point(
            (center_lat, center_lon),
            dist=graph_radius_m,
            network_type="walk",
            simplify=True,
        )
        nearest_nodes: dict[str, Any] = {}
        for _, row in valid.iterrows():
            nearest_nodes[str(row["location_key"])] = ox.distance.nearest_nodes(
                graph,
                X=float(row["longitude"]),
                Y=float(row["latitude"]),
            )

        lengths: dict[tuple[str, str], float] = {}
        for origin_key, origin_node in nearest_nodes.items():
            for destination_key, destination_node in nearest_nodes.items():
                if origin_key == destination_key:
                    lengths[(origin_key, destination_key)] = 0.0
                    continue
                try:
                    length = nx.shortest_path_length(
                        graph,
                        source=origin_node,
                        target=destination_node,
                        weight="length",
                    )
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue
                lengths[(origin_key, destination_key)] = float(length)
        return lengths, f"success:graph_radius_m={graph_radius_m}:nodes={len(graph.nodes)}:edges={len(graph.edges)}"
    except Exception as exc:  # pragma: no cover - network/service/runtime dependent
        return {}, f"failed:{type(exc).__name__}:{exc}"


def build_distance_matrix(nodes: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    osmnx_lengths, osmnx_status = try_osmnx_lengths(nodes)
    rows: list[dict[str, object]] = []
    for _, origin in nodes.iterrows():
        for _, destination in nodes.iterrows():
            origin_key = str(origin["location_key"])
            destination_key = str(destination["location_key"])
            is_same = origin_key == destination_key
            straight_distance = haversine_m(
                float(origin["latitude"]),
                float(origin["longitude"]),
                float(destination["latitude"]),
                float(destination["longitude"]),
            )
            if is_same:
                straight_distance = 0.0

            fallback_distance = straight_distance * FALLBACK_ROUTE_FACTOR
            osmnx_distance = osmnx_lengths.get((origin_key, destination_key))
            if osmnx_distance is not None:
                chosen_distance = osmnx_distance
                method = "osmnx_walk_network"
                note = "OpenStreetMap walking network shortest path"
            else:
                chosen_distance = fallback_distance
                method = "straight_line_1.3_multiplier"
                note = "Fallback estimate: straight-line distance multiplied by 1.3"

            rows.append(
                {
                    "origin_location_key": origin_key,
                    "origin_display_name": origin["display_name"],
                    "origin_latitude": origin["latitude"],
                    "origin_longitude": origin["longitude"],
                    "destination_location_key": destination_key,
                    "destination_display_name": destination["display_name"],
                    "destination_latitude": destination["latitude"],
                    "destination_longitude": destination["longitude"],
                    "is_same_location": is_same,
                    "straight_distance_m": round(straight_distance, 2),
                    "straight_distance_km": round(straight_distance / 1000, 3),
                    "fallback_walk_distance_m": round(fallback_distance, 2),
                    "fallback_walk_minutes": walk_minutes(fallback_distance),
                    "osmnx_walk_distance_m": round(osmnx_distance, 2) if osmnx_distance is not None else "",
                    "osmnx_walk_minutes": walk_minutes(osmnx_distance),
                    "walk_distance_m": round(chosen_distance, 2),
                    "walk_minutes": walk_minutes(chosen_distance),
                    "walk_method": method,
                    "distance_quality_note": note,
                    "osmnx_status": osmnx_status,
                    "walk_speed_kmph": WALK_SPEED_KMPH,
                    "fallback_route_factor": FALLBACK_ROUTE_FACTOR,
                    "origin_needs_manual_verification": boolean_text(origin.get("needs_manual_verification")),
                    "destination_needs_manual_verification": boolean_text(
                        destination.get("needs_manual_verification")
                    ),
                }
            )
    return pd.DataFrame(rows), osmnx_status


def markdown_table(frame: pd.DataFrame, columns: list[str], rows: int = 10) -> str:
    subset = frame.head(rows)[columns].fillna("")
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for _, row in subset.iterrows():
        body.append("| " + " | ".join(str(row[column]).replace("|", "/") for column in columns) + " |")
    return "\n".join([header, separator, *body])


def write_report(nodes: pd.DataFrame, matrix: pd.DataFrame, osmnx_status: str) -> None:
    non_self = matrix[~matrix["is_same_location"]].copy()
    nearest = non_self.sort_values("walk_distance_m").head(10)
    farthest = non_self.sort_values("walk_distance_m", ascending=False).head(10)
    manual_count = nodes["needs_manual_verification"].astype(str).str.lower().eq("true").sum()
    osmnx_pairs = matrix["walk_method"].eq("osmnx_walk_network").sum()
    if manual_count:
        manual_note = (
            "- Rows with `needs_manual_verification=true` should be checked against "
            "the event operator or a primary map source before external publication."
        )
    else:
        manual_note = "- No active location nodes currently require manual coordinate verification."

    report = f"""# GIS Distance Matrix Report

Generated: {date.today().isoformat()}

## Purpose

This report records the venue-to-venue distance layer for the 2026 Yeonhui Yoga Week GIS analysis.

## Method

- Location nodes: {len(nodes)}
- Distance matrix rows: {len(matrix)}
- Walking speed assumption: {WALK_SPEED_KMPH} km/h
- Fallback route factor: straight-line distance x {FALLBACK_ROUTE_FACTOR}
- OSMnx status: `{osmnx_status}`
- Rows using OSMnx walking network: {int(osmnx_pairs)}
- Location nodes needing manual verification: {int(manual_count)}

## Nearest Venue Pairs

{markdown_table(nearest, ["origin_display_name", "destination_display_name", "walk_distance_m", "walk_minutes", "walk_method"])}

## Farthest Venue Pairs

{markdown_table(farthest, ["origin_display_name", "destination_display_name", "walk_distance_m", "walk_minutes", "walk_method"])}

## Limits

- OSMnx distances depend on current OpenStreetMap coverage and the downloaded walking network.
- If OSMnx is unavailable or a path cannot be found, `walk_distance_m` uses the documented straight-line fallback.
{manual_note}
"""
    write_text(GIS_DISTANCE_REPORT_MD, report)


def main() -> None:
    if not LOCATION_CATALOG_CSV.exists():
        raise FileNotFoundError(f"Missing location catalog. Run build_gis_tables.py first: {LOCATION_CATALOG_CSV}")

    catalog = pd.read_csv(LOCATION_CATALOG_CSV, dtype=str, keep_default_na=False)
    nodes = build_location_nodes(catalog)
    matrix, osmnx_status = build_distance_matrix(nodes)

    write_csv(nodes, LOCATION_NODES_CSV)
    write_csv(matrix, LOCATION_DISTANCE_MATRIX_CSV)
    write_report(nodes, matrix, osmnx_status)

    print(f"Wrote {LOCATION_NODES_CSV}")
    print(f"Wrote {LOCATION_DISTANCE_MATRIX_CSV}")
    print(f"Wrote {GIS_DISTANCE_REPORT_MD}")
    print(f"OSMnx status: {osmnx_status}")


if __name__ == "__main__":
    main()
