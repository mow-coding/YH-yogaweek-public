from __future__ import annotations

import json
import math
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DRIVE = ROOT / "data" / "raw" / "google_drive_shared" / "rightnow_yogi"
PUBLIC_DIR = ROOT / "data" / "processed" / "analysis" / "public"
REPORT_DIR = ROOT / "reports" / "google_drive"

FNB_XLSX = RAW_DRIVE / "files" / "fnb_partner_brands.xlsx"
DRIVE_MANIFEST = REPORT_DIR / "rightnow_yogi_full_archive_manifest.csv"
LOCATION_NODES = PUBLIC_DIR / "location_nodes.csv"

FNB_PUBLIC = PUBLIC_DIR / "fnb_partner_brands_public.csv"
FNB_GEOJSON = PUBLIC_DIR / "fnb_partner_brands_gis.geojson"
SPONSOR_PUBLIC = PUBLIC_DIR / "sponsor_asset_inventory_public.csv"
REPORT = REPORT_DIR / "fnb_sponsor_gis_analysis_report.md"

ARCGIS_ENDPOINT = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def brand_key(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", value).strip()


def clean_address_for_geocoding(address: str) -> str:
    text = clean_text(address)
    text = text.replace(".", " ")
    if text and not text.startswith("서울"):
        text = "서울특별시 서대문구 " + text
    return re.sub(r"\s+", " ", text).strip()


def geocode_address(address: str) -> dict[str, Any]:
    if not address:
        return {
            "latitude": None,
            "longitude": None,
            "geocoded_address": "",
            "geocode_score": None,
            "geocode_addr_type": "",
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
            "needs_manual_verification": True,
        }
    top = candidates[0]
    attrs = top.get("attributes", {})
    loc = top.get("location", {})
    score = float(attrs.get("Score") or top.get("score") or 0)
    addr_type = str(attrs.get("Addr_type") or "")
    needs_manual = not (score >= 95 and addr_type in {"PointAddress", "StreetAddress"})
    return {
        "latitude": loc.get("y"),
        "longitude": loc.get("x"),
        "geocoded_address": attrs.get("Match_addr") or top.get("address") or "",
        "geocode_score": score,
        "geocode_addr_type": addr_type,
        "needs_manual_verification": needs_manual,
    }


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def summarize_terms(text: str) -> str:
    text = clean_text(text)
    text = text.replace("•", "")
    if len(text) <= 160:
        return text
    return text[:157].rstrip() + "..."


def parse_fnb_sheet() -> pd.DataFrame:
    if not FNB_XLSX.exists():
        raise SystemExit(f"Missing F&B file: {FNB_XLSX}")
    raw = pd.read_excel(FNB_XLSX, sheet_name=0, header=None)
    header_index = None
    header_columns: dict[str, int] = {}
    for idx, row in raw.iterrows():
        values = [clean_text(value) for value in row.tolist()]
        if "브랜드" in values and "분류" in values and "위치" in values:
            header_index = idx
            header_columns = {value: col_index for col_index, value in enumerate(values) if value}
            break
    if header_index is None:
        raise SystemExit("Could not find F&B header row.")
    brand_col = header_columns["브랜드"]
    number_col = brand_col - 1
    category_col = header_columns["분류"]
    address_col = header_columns["위치"]
    terms_col = header_columns["협업내용"]

    records = []
    for _, row in raw.iloc[header_index + 1 :].iterrows():
        number = clean_text(row.iloc[number_col] if len(row) > number_col else "")
        name = clean_text(row.iloc[brand_col] if len(row) > brand_col else "")
        category = clean_text(row.iloc[category_col] if len(row) > category_col else "")
        address = clean_text(row.iloc[address_col] if len(row) > address_col else "")
        terms = clean_text(row.iloc[terms_col] if len(row) > terms_col else "")
        if not number or not name:
            continue
        if not re.match(r"^\d+", number):
            continue
        records.append(
            {
                "fnb_partner_order": int(float(number)),
                "fnb_brand_key": brand_key(name),
                "fnb_brand_name": name,
                "fnb_category": category,
                "address_text": address,
                "collaboration_terms_summary": summarize_terms(terms),
                "coupon_type": "1000krw_discount_or_menu_benefit",
                "source_file": "fnb_partner_brands.xlsx",
                "needs_manual_review": False,
            }
        )
    return pd.DataFrame(records)


def attach_geocoding_and_distance(fnb: pd.DataFrame) -> pd.DataFrame:
    fnb = fnb.copy()
    geocode_cache: dict[str, dict[str, Any]] = {}
    for address in fnb["address_text"].fillna("").unique():
        cleaned = clean_address_for_geocoding(address)
        if cleaned not in geocode_cache:
            geocode_cache[cleaned] = geocode_address(cleaned)
            time.sleep(0.2)

    geocoded_rows = []
    for _, row in fnb.iterrows():
        result = geocode_cache[clean_address_for_geocoding(row["address_text"])]
        geocoded_rows.append(result)
    geocoded = pd.concat([fnb.reset_index(drop=True), pd.DataFrame(geocoded_rows)], axis=1)
    geocoded = apply_public_place_verification_overrides(geocoded)

    if not LOCATION_NODES.exists():
        geocoded["nearest_location_key"] = ""
        geocoded["nearest_location_distance_km"] = pd.NA
        return geocoded

    locations = pd.read_csv(LOCATION_NODES)
    nearest_rows = []
    for _, row in geocoded.iterrows():
        lat = row.get("latitude")
        lon = row.get("longitude")
        if pd.isna(lat) or pd.isna(lon):
            nearest_rows.append({"nearest_location_key": "", "nearest_location_distance_km": pd.NA})
            continue
        candidates = []
        for _, loc in locations.iterrows():
            loc_lat = loc.get("latitude")
            loc_lon = loc.get("longitude")
            if pd.isna(loc_lat) or pd.isna(loc_lon):
                continue
            candidates.append(
                {
                    "nearest_location_key": loc.get("location_key", loc.get("display_name", "")),
                    "nearest_location_distance_km": haversine_km(float(lat), float(lon), float(loc_lat), float(loc_lon)),
                }
            )
        if candidates:
            nearest_rows.append(min(candidates, key=lambda item: item["nearest_location_distance_km"]))
        else:
            nearest_rows.append({"nearest_location_key": "", "nearest_location_distance_km": pd.NA})
    nearest = pd.DataFrame(nearest_rows)
    geocoded = pd.concat([geocoded.reset_index(drop=True), nearest], axis=1)
    geocoded["nearest_location_distance_km"] = geocoded["nearest_location_distance_km"].round(3)
    geocoded["needs_manual_review"] = geocoded["needs_manual_review"] | geocoded["needs_manual_verification"].astype(bool)
    return geocoded


def apply_public_place_verification_overrides(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    umma_mask = output["fnb_brand_key"].astype(str).eq("엄마식탁")
    if umma_mask.any():
        output.loc[umma_mask, "address_text"] = "연희맛로 17-21"
        output.loc[umma_mask, "geocoded_address"] = "서울특별시 서대문구 연희맛로 17-21"
        output.loc[umma_mask, "geocode_addr_type"] = "PointAddress"
        output.loc[umma_mask, "geocode_score"] = 100.0
        output.loc[umma_mask, "needs_manual_verification"] = False
        output.loc[umma_mask, "needs_manual_review"] = False
    return output


def build_geojson(fnb: pd.DataFrame) -> None:
    features = []
    for _, row in fnb.iterrows():
        lat = row.get("latitude")
        lon = row.get("longitude")
        if pd.isna(lat) or pd.isna(lon):
            continue
        properties = {
            "fnb_brand_key": row["fnb_brand_key"],
            "fnb_brand_name": row["fnb_brand_name"],
            "fnb_category": row["fnb_category"],
            "address_text": row["address_text"],
            "nearest_location_key": row.get("nearest_location_key", ""),
            "nearest_location_distance_km": row.get("nearest_location_distance_km", None),
            "needs_manual_review": bool(row.get("needs_manual_review", False)),
        }
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                "properties": properties,
            }
        )
    geojson = {"type": "FeatureCollection", "features": features}
    FNB_GEOJSON.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_sponsor_inventory() -> pd.DataFrame:
    if not DRIVE_MANIFEST.exists():
        raise SystemExit(f"Missing Drive manifest: {DRIVE_MANIFEST}")
    manifest = pd.read_csv(DRIVE_MANIFEST)
    sponsor = manifest[manifest["source_path"].str.contains("/3스폰서/", na=False)].copy()
    sponsor = sponsor[sponsor["status"].isin({"downloaded", "downloaded_export_fallback", "existing_local_copy"})]
    sponsor["sponsor_folder"] = sponsor["source_path"].map(lambda path: str(path).split("/")[2] if len(str(path).split("/")) > 2 else "")
    sponsor["sponsor_name"] = sponsor["sponsor_folder"].map(lambda value: re.sub(r"^\d+\s*", "", value).strip())
    sponsor["asset_type"] = sponsor.apply(lambda row: classify_asset_type(str(row["source_mime_type"]), str(row["local_path"])), axis=1)
    summary = (
        sponsor.groupby(["sponsor_name"], dropna=False)
        .agg(
            sponsor_asset_count=("source_id", "count"),
            image_asset_count=("asset_type", lambda s: int((s == "image").sum())),
            design_source_count=("asset_type", lambda s: int((s == "design_source").sum())),
            document_asset_count=("asset_type", lambda s: int((s == "document").sum())),
            archive_asset_count=("asset_type", lambda s: int((s == "archive").sum())),
        )
        .reset_index()
        .sort_values(["sponsor_asset_count", "sponsor_name"], ascending=[False, True])
    )
    summary["sponsor_key"] = summary["sponsor_name"].map(brand_key)
    summary["source_basis"] = "Google Drive sponsor folder asset inventory"
    summary["needs_manual_review"] = summary["sponsor_name"].eq("")
    cols = [
        "sponsor_key",
        "sponsor_name",
        "sponsor_asset_count",
        "image_asset_count",
        "design_source_count",
        "document_asset_count",
        "archive_asset_count",
        "source_basis",
        "needs_manual_review",
    ]
    return summary[cols]


def classify_asset_type(mime: str, local_path: str) -> str:
    suffix = Path(local_path).suffix.lower()
    if mime.startswith("image/") or suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return "image"
    if suffix in {".ai", ".psd", ".svg"}:
        return "design_source"
    if "document" in mime or suffix in {".docx", ".pdf", ".txt"}:
        return "document"
    if suffix == ".zip":
        return "archive"
    return "other"


def write_report(fnb: pd.DataFrame, sponsor: pd.DataFrame) -> None:
    geocoded_count = int(fnb["latitude"].notna().sum())
    manual_count = int(fnb["needs_manual_review"].astype(bool).sum())
    near_count = int((fnb["nearest_location_distance_km"] <= 0.3).sum())
    lines = [
        "# F&B and Sponsor GIS Analysis Report",
        "",
        f"작성일: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## 요약",
        "",
        f"- F&B 협업 브랜드: {len(fnb)}개",
        f"- F&B 좌표 확보: {geocoded_count}개",
        f"- 수동 검토 필요: {manual_count}개",
        f"- 행사 장소 300m 이내 F&B 후보: {near_count}개",
        f"- 스폰서 asset inventory 브랜드/폴더: {len(sponsor)}개",
        f"- 스폰서 asset 총합: {int(sponsor['sponsor_asset_count'].sum())}개",
        "",
        "## F&B 거리 후보",
        "",
    ]
    for row in fnb.sort_values("nearest_location_distance_km").itertuples(index=False):
        lines.append(
            f"- {row.fnb_brand_name} ({row.fnb_category}): nearest={row.nearest_location_key}, "
            f"distance_km={row.nearest_location_distance_km}"
        )
    lines.extend(
        [
            "",
            "## 해석",
            "",
            "- 이 분석은 실제 쿠폰 사용 기록이 아니라, F&B 협업표와 주소 기반 동선 가능성 분석이다.",
            "- 가까운 F&B 브랜드는 다음 회차에서 지도, 체크인 안내, 웰니스 맵, 쿠폰 동선 설계에 활용할 수 있다.",
            "- 스폰서 asset inventory는 후원사별 자료 보유량을 보여줄 뿐, 후원 가치나 관계의 우열을 뜻하지 않는다.",
            "",
            "## 산출물",
            "",
            f"- `{FNB_PUBLIC.relative_to(ROOT)}`",
            f"- `{FNB_GEOJSON.relative_to(ROOT)}`",
            f"- `{SPONSOR_PUBLIC.relative_to(ROOT)}`",
            "",
            "## 한계",
            "",
            "- 주소는 Google Drive 협업표 기준이며, 실제 영업 위치/폐업/이전 여부는 별도 확인이 필요하다.",
            "- 거리는 직선거리다. 실제 보행 시간은 OSMnx 보행 네트워크 분석으로 확장할 수 있다.",
            "- 쿠폰 사용 실제 로그가 없으므로 지역 소비 효과는 아직 가능성 분석 단계다.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fnb = parse_fnb_sheet()
    fnb = attach_geocoding_and_distance(fnb)
    sponsor = parse_sponsor_inventory()

    fnb.to_csv(FNB_PUBLIC, index=False, encoding="utf-8-sig")
    build_geojson(fnb)
    sponsor.to_csv(SPONSOR_PUBLIC, index=False, encoding="utf-8-sig")
    write_report(fnb, sponsor)

    print(f"F&B rows: {len(fnb)}")
    print(f"F&B geocoded rows: {int(fnb['latitude'].notna().sum())}")
    print(f"Sponsor rows: {len(sponsor)}")
    print(f"Report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
