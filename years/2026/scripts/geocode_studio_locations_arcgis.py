from __future__ import annotations

import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
LOCATION_PATH = ROOT / "data" / "external" / "studio_locations_public.csv"
REPORT_PATH = ROOT / "reports" / "analysis" / "gis_geocoding_report.md"
ARCGIS_ENDPOINT = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"


def clean_address_for_geocoding(address: object) -> str:
    text = "" if pd.isna(address) else str(address).strip()
    for token in [" B1층", " 지층", " 1층", " 2층", " 3층", " 4층", " 5층"]:
        text = text.replace(token, "")
    return text.strip()


def geocode_address(address: str) -> dict[str, object]:
    if not address:
        return {
            "latitude": None,
            "longitude": None,
            "geocoded_address": "",
            "geocode_score": None,
            "geocode_addr_type": "",
            "geocode_method": "ArcGIS World Geocoding Service",
            "geocode_confidence": None,
            "needs_manual_verification": True,
        }

    response = requests.get(
        ARCGIS_ENDPOINT,
        params={
            "SingleLine": address,
            "f": "json",
            "maxLocations": 1,
            "outFields": "Match_addr,Addr_type,Score",
        },
        timeout=20,
    )
    response.raise_for_status()
    candidates = response.json().get("candidates", [])
    if not candidates:
        return {
            "latitude": None,
            "longitude": None,
            "geocoded_address": "",
            "geocode_score": None,
            "geocode_addr_type": "",
            "geocode_method": "ArcGIS World Geocoding Service",
            "geocode_confidence": None,
            "needs_manual_verification": True,
        }

    top = candidates[0]
    location = top.get("location", {})
    attributes = top.get("attributes", {})
    score = float(attributes.get("Score") or top.get("score") or 0)
    addr_type = str(attributes.get("Addr_type") or "")
    is_point = addr_type in {"PointAddress", "StreetAddress"}
    needs_manual = not (score >= 95 and is_point)

    return {
        "latitude": location.get("y"),
        "longitude": location.get("x"),
        "geocoded_address": attributes.get("Match_addr") or top.get("address") or "",
        "geocode_score": score,
        "geocode_addr_type": addr_type,
        "geocode_method": "ArcGIS World Geocoding Service",
        "geocode_confidence": round(score / 100, 4),
        "needs_manual_verification": needs_manual,
    }


def write_report(frame: pd.DataFrame) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    geocoded = frame["latitude"].notna() & frame["longitude"].notna()
    needs_manual = frame["needs_manual_verification"].astype(str).str.lower().eq("true")
    manual_table = markdown_table(
        frame.loc[
            needs_manual,
            ["studio_key", "display_name", "address", "geocoded_address", "geocode_score", "geocode_addr_type", "notes"],
        ].fillna("")
    )
    report = f"""# GIS Geocoding Report

Generated: {date.today().isoformat()}

## Purpose

This report records how event venue/studio addresses were converted into latitude/longitude coordinates for the 2026 Yeonhui Yoga Week GIS analysis.

## Inputs

- Location seed table: `data/external/studio_locations_public.csv`
- Address source: ON STUDIO class descriptions

## Method

- Geocoder: ArcGIS World Geocoding Service
- Endpoint: `{ARCGIS_ENDPOINT}`
- Query unit: one unique address string per venue/studio
- Confidence rule:
  - `needs_manual_verification=false` when the top candidate score is at least 95 and the address type is `PointAddress` or `StreetAddress`
  - otherwise `needs_manual_verification=true`

## Result

- Rows in location table: {len(frame)}
- Rows with coordinates: {int(geocoded.sum())}
- Rows needing manual verification: {int(needs_manual.sum())}

## Rows Needing Manual Verification

{manual_table}
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows_"
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in frame.iterrows():
        values = [str(row[column]).replace("|", "/") for column in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def main() -> None:
    locations = pd.read_csv(LOCATION_PATH)
    text_columns = ["geocoded_address", "geocode_addr_type", "geocode_method"]
    numeric_columns = ["latitude", "longitude", "geocode_score", "geocode_confidence"]
    for column in text_columns:
        if column not in locations.columns:
            locations[column] = ""
        locations[column] = locations[column].fillna("").astype(object)
    for column in numeric_columns:
        if column not in locations.columns:
            locations[column] = None
        locations[column] = pd.to_numeric(locations[column], errors="coerce")
    locations["needs_manual_verification"] = locations["needs_manual_verification"].astype(object)

    geocode_cache: dict[str, dict[str, object]] = {}

    for raw_address in locations["address"].dropna().unique():
        address = clean_address_for_geocoding(raw_address)
        if not address:
            continue
        if address not in geocode_cache:
            geocode_cache[address] = geocode_address(address)
            time.sleep(0.2)

    for index, row in locations.iterrows():
        cleaned = clean_address_for_geocoding(row.get("address"))
        result = geocode_cache.get(cleaned) or geocode_address("")
        for key, value in result.items():
            locations.loc[index, key] = value
        note = str(row.get("notes") or "")
        if "정확한" in note or "최종 확인" in note:
            locations.loc[index, "needs_manual_verification"] = True

    locations.to_csv(LOCATION_PATH, index=False, encoding="utf-8-sig")
    write_report(locations)

    geocoded_count = int(locations["latitude"].notna().sum())
    manual_count = int(locations["needs_manual_verification"].astype(str).str.lower().eq("true").sum())
    print(f"Updated {LOCATION_PATH}")
    print(f"Geocoded rows: {geocoded_count}")
    print(f"Rows needing manual verification: {manual_count}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
