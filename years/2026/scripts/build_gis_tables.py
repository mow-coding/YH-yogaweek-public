from __future__ import annotations

import html
import json
import math
from datetime import date
from pathlib import Path

import pandas as pd

from review_processing_utils import (
    ANALYSIS_PUBLIC_DIR,
    CLASS_HYPE_METRICS_PUBLIC,
    REPORT_ANALYSIS_DIR,
    STUDIO_HYPE_METRICS_PUBLIC,
    percentile_0_100,
)


ROOT = Path(__file__).resolve().parents[1]
LOCATION_PATH = ROOT / "data" / "external" / "studio_locations_public.csv"
STUDIO_GIS_CSV = ANALYSIS_PUBLIC_DIR / "studio_hype_gis.csv"
CLASS_GIS_CSV = ANALYSIS_PUBLIC_DIR / "class_hype_gis.csv"
EVENT_LOCATION_CATALOG_GIS_CSV = ANALYSIS_PUBLIC_DIR / "event_location_catalog_gis.csv"
STUDIO_GIS_GEOJSON = ANALYSIS_PUBLIC_DIR / "studio_hype_gis.geojson"
EVENT_LOCATION_CATALOG_GIS_GEOJSON = ANALYSIS_PUBLIC_DIR / "event_location_catalog_gis.geojson"
GIS_MAP_HTML = REPORT_ANALYSIS_DIR / "yeonhui_yoga_week_gis_map.html"
GIS_REPORT_MD = REPORT_ANALYSIS_DIR / "gis_analysis_report.md"


COUNT_COLUMNS = [
    "class_count",
    "reservation_count",
    "cancellation_count",
    "net_reservation_count",
    "review_count",
    "pass_reservation_count",
    "one_time_reservation_count",
    "participant_price_proxy_krw",
    "instructor_tag_count",
    "space_tag_count",
    "atmosphere_tag_count",
    "difficulty_tag_count",
    "recovery_tag_count",
    "revisit_intent_tag_count",
]

RATING_COLUMNS = [
    "avg_overall_rating",
    "avg_class_rating",
    "avg_atmosphere_rating",
    "avg_facility_rating",
    "avg_visit_count",
]


def weighted_average(values: pd.Series, weights: pd.Series) -> float | None:
    numeric_values = pd.to_numeric(values, errors="coerce")
    numeric_weights = pd.to_numeric(weights, errors="coerce").fillna(0)
    valid = numeric_values.notna() & (numeric_weights > 0)
    if not valid.any():
        return None
    return float((numeric_values[valid] * numeric_weights[valid]).sum() / numeric_weights[valid].sum())


def normalize_studio_key(value: object, aliases: dict[str, str]) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    if text in aliases:
        return aliases[text]
    if "|" in text:
        text = text.split("|", 1)[0].strip()
    return aliases.get(text, text)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def rebuild_hype_columns(metrics: pd.DataFrame) -> pd.DataFrame:
    output = metrics.copy()
    total_attempts = output["reservation_count"] + output["cancellation_count"]
    output["cancellation_rate"] = (
        output["cancellation_count"] / total_attempts.where(total_attempts != 0)
    ).fillna(0)
    output["review_rate_per_reservation"] = (
        output["review_count"] / output["reservation_count"].where(output["reservation_count"] != 0)
    ).fillna(0)
    output["reservation_hype"] = percentile_0_100(output["net_reservation_count"])
    review_count_score = percentile_0_100(output["review_count"])
    review_rate_score = percentile_0_100(output["review_rate_per_reservation"])
    output["review_hype"] = [
        round((count_score + rate_score) / 2, 2)
        for count_score, rate_score in zip(review_count_score, review_rate_score, strict=False)
    ]
    output["satisfaction_hype"] = [
        round((value / 5) * 100, 2) if pd.notna(value) else None
        for value in pd.to_numeric(output["avg_overall_rating"], errors="coerce")
    ]
    output["revisit_hype"] = percentile_0_100(output["avg_visit_count"])
    output["payment_hype"] = percentile_0_100(output["participant_price_proxy_krw"])
    output["operations_stability"] = (1 - output["cancellation_rate"]).clip(lower=0, upper=1).mul(100).round(2)
    return output


def build_normalized_studio_metrics(studio_metrics: pd.DataFrame, locations: pd.DataFrame) -> pd.DataFrame:
    aliases = dict(zip(locations["studio_key"], locations["normalized_studio_key"], strict=False))
    studio_metrics = studio_metrics.copy()
    studio_metrics["normalized_studio_key"] = studio_metrics["studio_key"].map(lambda value: normalize_studio_key(value, aliases))

    rows: list[dict[str, object]] = []
    for normalized_key, group in studio_metrics.groupby("normalized_studio_key", dropna=False):
        row: dict[str, object] = {
            "normalized_studio_key": normalized_key,
            "source_studio_keys": ", ".join(sorted(str(value) for value in group["studio_key"].dropna().unique())),
        }
        for column in COUNT_COLUMNS:
            row[column] = pd.to_numeric(group[column], errors="coerce").fillna(0).sum()
        for column in RATING_COLUMNS:
            row[column] = weighted_average(group[column], group["review_count"])
        rows.append(row)

    output = pd.DataFrame(rows)
    for column in COUNT_COLUMNS:
        output[column] = output[column].round().astype(int)

    output = rebuild_hype_columns(output)

    location_one = (
        locations.sort_values(["normalized_studio_key", "needs_manual_verification"])
        .drop_duplicates("normalized_studio_key")
        .copy()
    )
    merged = output.merge(location_one, on="normalized_studio_key", how="left")
    return merged.sort_values(["reservation_count", "review_count"], ascending=[False, False])


def add_spatial_summary(studio_gis: pd.DataFrame) -> pd.DataFrame:
    output = studio_gis.copy()
    valid = output["latitude"].notna() & output["longitude"].notna()
    weights = pd.to_numeric(output.loc[valid, "net_reservation_count"], errors="coerce").clip(lower=0)
    if valid.any() and weights.sum() > 0:
        center_lat = float((output.loc[valid, "latitude"] * weights).sum() / weights.sum())
        center_lon = float((output.loc[valid, "longitude"] * weights).sum() / weights.sum())
    elif valid.any():
        center_lat = float(output.loc[valid, "latitude"].mean())
        center_lon = float(output.loc[valid, "longitude"].mean())
    else:
        center_lat = None
        center_lon = None

    if center_lat is None or center_lon is None:
        output["distance_from_activity_center_km"] = None
        return output

    output["distance_from_activity_center_km"] = [
        round(haversine_km(float(lat), float(lon), center_lat, center_lon), 3)
        if pd.notna(lat) and pd.notna(lon)
        else None
        for lat, lon in zip(output["latitude"], output["longitude"], strict=False)
    ]
    output["activity_center_latitude"] = center_lat
    output["activity_center_longitude"] = center_lon
    return output


def build_class_gis(class_metrics: pd.DataFrame, locations: pd.DataFrame) -> pd.DataFrame:
    aliases = dict(zip(locations["studio_key"], locations["normalized_studio_key"], strict=False))
    class_metrics = class_metrics.copy()
    class_metrics["normalized_studio_key"] = class_metrics["studio_key"].map(lambda value: normalize_studio_key(value, aliases))
    location_one = (
        locations.sort_values(["normalized_studio_key", "needs_manual_verification"])
        .drop_duplicates("normalized_studio_key")
        .copy()
    )
    return class_metrics.merge(location_one, on="normalized_studio_key", how="left")


def build_location_catalog_gis(locations: pd.DataFrame) -> pd.DataFrame:
    output = locations.copy()
    output = output.sort_values(["normalized_studio_key", "needs_manual_verification", "studio_key"])
    output = output.drop_duplicates("normalized_studio_key")
    return output


def frame_to_geojson(frame: pd.DataFrame, path: Path) -> None:
    features = []
    for _, row in frame.iterrows():
        if pd.isna(row.get("latitude")) or pd.isna(row.get("longitude")):
            continue
        properties = {
            key: (None if pd.isna(value) else value)
            for key, value in row.drop(labels=["latitude", "longitude"]).to_dict().items()
        }
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["longitude"]), float(row["latitude"])],
                },
                "properties": properties,
            }
        )
    payload = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_geojson(studio_gis: pd.DataFrame) -> None:
    frame_to_geojson(studio_gis, STUDIO_GIS_GEOJSON)


def marker_color(review_hype: object) -> str:
    value = pd.to_numeric(pd.Series([review_hype]), errors="coerce").iloc[0]
    if pd.isna(value):
        return "#6b7280"
    if value >= 75:
        return "#c2410c"
    if value >= 50:
        return "#15803d"
    return "#2563eb"


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def fmt_metric(value: object, digits: int = 1) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "-"
    if float(numeric).is_integer():
        return f"{int(numeric):,}"
    return f"{float(numeric):,.{digits}f}"


def add_map_chrome(fmap: object, *, title: str, subtitle: str, legend_html: str) -> None:
    control_html = f"""
    <div class="yw-panel yw-title-panel">
      <div class="yw-eyebrow">2026 연희 요가 위크 GIS</div>
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(subtitle)}</p>
    </div>
    <div class="yw-panel yw-legend-panel">
      {legend_html}
    </div>
    <style>
      .leaflet-container {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #fffaf0;
      }}
      .leaflet-control-layers,
      .leaflet-bar a,
      .leaflet-control-scale-line {{
        border-color: rgba(42, 24, 16, 0.14) !important;
        box-shadow: 0 8px 22px rgba(42, 24, 16, 0.12) !important;
      }}
      .leaflet-control-layers {{
        border-radius: 8px;
        color: #2a1810;
      }}
      .leaflet-popup-content-wrapper {{
        border-radius: 8px;
        box-shadow: 0 18px 34px rgba(42, 24, 16, 0.20);
      }}
      .yw-panel {{
        position: fixed;
        z-index: 9999;
        background: rgba(255, 253, 248, 0.92);
        border: 1px solid rgba(229, 220, 200, 0.92);
        border-radius: 8px;
        box-shadow: 0 18px 38px rgba(42, 24, 16, 0.18);
        color: #2a1810;
        backdrop-filter: blur(10px);
      }}
      .yw-title-panel {{
        top: 16px;
        left: 56px;
        width: min(420px, calc(100% - 96px));
        padding: 15px 17px 14px;
      }}
      .yw-title-panel h1 {{
        margin: 2px 0 7px;
        font-size: 19px;
        font-weight: 800;
        line-height: 1.3;
        letter-spacing: 0;
      }}
      .yw-title-panel p {{
        margin: 0;
        color: #64584e;
        font-size: 13px;
        line-height: 1.48;
      }}
      .yw-eyebrow {{
        font-size: 11px;
        letter-spacing: 0;
        color: #9a5a00;
        font-weight: 700;
      }}
      .yw-legend-panel {{
        right: 18px;
        bottom: 28px;
        width: min(320px, calc(100% - 36px));
        padding: 13px 15px;
        font-size: 12px;
        line-height: 1.45;
      }}
      .yw-legend-panel h2 {{
        margin: 0 0 8px;
        font-size: 13px;
      }}
      .yw-row {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 6px 0;
      }}
      .yw-dot {{
        width: 11px;
        height: 11px;
        border-radius: 50%;
        display: inline-block;
        border: 1px solid rgba(42, 24, 16, 0.25);
        flex: 0 0 auto;
      }}
      .yw-line {{
        width: 22px;
        height: 0;
        border-top: 4px solid #15803d;
        border-radius: 999px;
        display: inline-block;
        flex: 0 0 auto;
      }}
      .yw-note {{
        margin-top: 8px;
        color: #6f645a;
      }}
      .yw-popup {{
        min-width: 230px;
        color: #2a1810;
      }}
      .yw-popup h3 {{
        margin: 0 0 7px;
        font-size: 15px;
      }}
      .yw-popup table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
      }}
      .yw-popup td {{
        border-top: 1px solid #efe6d4;
        padding: 5px 0;
        vertical-align: top;
      }}
      .yw-popup td:first-child {{
        color: #75685c;
        padding-right: 10px;
        white-space: nowrap;
      }}
      @media (max-width: 640px) {{
        .yw-title-panel {{
          top: 10px;
          left: 44px;
          width: calc(100% - 58px);
          padding: 11px 12px;
        }}
        .yw-legend-panel {{
          right: 10px;
          bottom: 20px;
          padding: 10px 12px;
        }}
      }}
    </style>
    """
    fmap.get_root().html.add_child(__import__("folium").Element(control_html))


def write_folium_map(studio_gis: pd.DataFrame, location_catalog: pd.DataFrame) -> None:
    try:
        import folium
        from folium import FeatureGroup, LayerControl
        from folium.plugins import Fullscreen, MiniMap, MousePosition
    except ImportError:
        return

    valid = studio_gis[studio_gis["latitude"].notna() & studio_gis["longitude"].notna()].copy()
    location_valid = location_catalog[
        location_catalog["latitude"].notna() & location_catalog["longitude"].notna()
    ].copy()
    if valid.empty:
        return

    center_frame = location_valid if not location_valid.empty else valid
    center = [float(center_frame["latitude"].mean()), float(center_frame["longitude"].mean())]
    fmap = folium.Map(location=center, zoom_start=14, tiles="CartoDB positron", control_scale=True)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", show=False).add_to(fmap)
    try:
        Fullscreen(position="topleft", title="전체 화면", title_cancel="전체 화면 닫기").add_to(fmap)
        MiniMap(toggle_display=True, position="bottomleft").add_to(fmap)
        MousePosition(position="bottomright", separator=" / ", prefix="좌표").add_to(fmap)
    except Exception:
        pass

    add_map_chrome(
        fmap,
        title="장소별 Hype 지도",
        subtitle="원 크기는 순예약 규모, 색은 리뷰 Hype 신호입니다. 회색은 위치는 있으나 예약/리뷰 지표가 없는 장소입니다.",
        legend_html="""
          <h2>읽는 법</h2>
          <div class="yw-row"><span class="yw-dot" style="background:#c2410c"></span><span>리뷰 Hype 높음</span></div>
          <div class="yw-row"><span class="yw-dot" style="background:#15803d"></span><span>리뷰 Hype 중간 이상</span></div>
          <div class="yw-row"><span class="yw-dot" style="background:#2563eb"></span><span>리뷰 Hype 보통</span></div>
          <div class="yw-row"><span class="yw-dot" style="background:#6b7280"></span><span>위치만 확인</span></div>
          <div class="yw-note">큰 원은 예약 반응이 큰 장소입니다. 순위표가 아니라 장소별 반응 프로필로 읽습니다.</div>
        """,
    )

    location_only_layer = FeatureGroup(name="위치만 있는 장소", show=True)
    hype_layer = FeatureGroup(name="Hype/예약 반응", show=True)
    center_layer = FeatureGroup(name="예약 가중 활동 중심", show=True)

    metric_keys = set(valid["normalized_studio_key"].dropna().astype(str))
    for _, row in location_valid.iterrows():
        normalized_key = str(row.get("normalized_studio_key") or "")
        if normalized_key in metric_keys:
            continue
        popup = folium.Popup(
            f"""
            <div class="yw-popup">
              <h3>{html.escape(str(row.get('display_name') or normalized_key))}</h3>
              <table>
                <tr><td>주소</td><td>{html.escape(str(row.get('address') or ''))}</td></tr>
                <tr><td>상태</td><td>위치 카탈로그만 있음</td></tr>
                <tr><td>수동 확인</td><td>{'필요' if truthy(row.get('needs_manual_verification')) else '완료'}</td></tr>
                <tr><td>비고</td><td>{html.escape(str(row.get('notes') or ''))}</td></tr>
              </table>
            </div>
            """,
            max_width=340,
        )
        folium.CircleMarker(
            location=[float(row["latitude"]), float(row["longitude"])],
            radius=6,
            color="#6b7280",
            weight=1.5,
            fill=True,
            fill_opacity=0.45,
            popup=popup,
            tooltip=f"{row.get('display_name') or normalized_key} (location only)",
        ).add_to(location_only_layer)

    for _, row in valid.iterrows():
        net = max(float(row.get("net_reservation_count") or 0), 0)
        radius = min(28, 6 + math.sqrt(net) * 1.4)
        popup = folium.Popup(
            f"""
            <div class="yw-popup">
              <h3>{html.escape(str(row.get('display_name') or row.get('normalized_studio_key')))}</h3>
              <table>
                <tr><td>주소</td><td>{html.escape(str(row.get('address') or ''))}</td></tr>
                <tr><td>순예약</td><td>{fmt_metric(row.get('net_reservation_count'), 0)}</td></tr>
                <tr><td>예약/취소</td><td>{fmt_metric(row.get('reservation_count'), 0)} / {fmt_metric(row.get('cancellation_count'), 0)}</td></tr>
                <tr><td>리뷰</td><td>{fmt_metric(row.get('review_count'), 0)}</td></tr>
                <tr><td>예약 Hype</td><td>{fmt_metric(row.get('reservation_hype'), 1)}</td></tr>
                <tr><td>리뷰 Hype</td><td>{fmt_metric(row.get('review_hype'), 1)}</td></tr>
                <tr><td>만족 Hype</td><td>{fmt_metric(row.get('satisfaction_hype'), 1)}</td></tr>
                <tr><td>활동 중심 거리</td><td>{fmt_metric(row.get('distance_from_activity_center_km'), 2)} km</td></tr>
              </table>
            </div>
            """,
            max_width=340,
        )
        folium.CircleMarker(
            location=[float(row["latitude"]), float(row["longitude"])],
            radius=radius,
            color=marker_color(row.get("review_hype")),
            weight=2,
            fill=True,
            fill_opacity=0.68,
            popup=popup,
            tooltip=str(row.get("display_name") or row.get("normalized_studio_key")),
        ).add_to(hype_layer)

    if "activity_center_latitude" in valid.columns and "activity_center_longitude" in valid.columns:
        center_lat = pd.to_numeric(valid["activity_center_latitude"], errors="coerce").dropna()
        center_lon = pd.to_numeric(valid["activity_center_longitude"], errors="coerce").dropna()
        if not center_lat.empty and not center_lon.empty:
            folium.CircleMarker(
                location=[float(center_lat.iloc[0]), float(center_lon.iloc[0])],
                radius=8,
                color="#2f6f4e",
                weight=3,
                fill=True,
                fill_color="#f9a212",
                fill_opacity=0.9,
                popup=folium.Popup(
                    "<div class='yw-popup'><h3>예약 가중 활동 중심</h3><table><tr><td>의미</td><td>순예약 규모를 가중치로 계산한 행사 반응의 중심점입니다.</td></tr></table></div>",
                    max_width=320,
                ),
                tooltip="예약 가중 활동 중심",
            ).add_to(center_layer)

    hype_layer.add_to(fmap)
    location_only_layer.add_to(fmap)
    center_layer.add_to(fmap)
    if not location_valid.empty:
        bounds = [
            [float(location_valid["latitude"].min()), float(location_valid["longitude"].min())],
            [float(location_valid["latitude"].max()), float(location_valid["longitude"].max())],
        ]
        fmap.fit_bounds(bounds, padding=(28, 28))
    LayerControl(collapsed=False).add_to(fmap)

    GIS_MAP_HTML.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(GIS_MAP_HTML))


def markdown_table(frame: pd.DataFrame, columns: list[str], rows: int = 10) -> str:
    subset = frame.head(rows)[columns].fillna("")
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for _, row in subset.iterrows():
        values = [str(row[column]).replace("|", "/") for column in columns]
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *body])


def write_report(studio_gis: pd.DataFrame, class_gis: pd.DataFrame, location_catalog: pd.DataFrame) -> None:
    geocoded = studio_gis["latitude"].notna() & studio_gis["longitude"].notna()
    location_geocoded = location_catalog["latitude"].notna() & location_catalog["longitude"].notna()
    needs_manual = studio_gis["needs_manual_verification"].astype(str).str.lower().eq("true")
    location_needs_manual = location_catalog["needs_manual_verification"].astype(str).str.lower().eq("true")
    top_net = studio_gis.sort_values("net_reservation_count", ascending=False)
    top_review = studio_gis.sort_values("review_count", ascending=False)
    top_distance = studio_gis.sort_values("distance_from_activity_center_km", ascending=False)

    report = f"""# GIS Analysis Report

Generated: {date.today().isoformat()}

## Scope

This first GIS pass connects ON STUDIO reservations/cancellations, Obud review metrics, and venue coordinates.

## Inputs

- Studio location seed/geocoding table: `data/external/studio_locations_public.csv`
- Studio Hype metrics: `data/processed/analysis/public/studio_hype_metrics.csv`
- Class Hype metrics: `data/processed/analysis/public/class_hype_metrics.csv`

## Outputs

- Studio GIS CSV: `data/processed/analysis/public/studio_hype_gis.csv`
- Class GIS CSV: `data/processed/analysis/public/class_hype_gis.csv`
- Event location catalog GIS CSV: `data/processed/analysis/public/event_location_catalog_gis.csv`
- Studio GIS GeoJSON: `data/processed/analysis/public/studio_hype_gis.geojson`
- Event location catalog GeoJSON: `data/processed/analysis/public/event_location_catalog_gis.geojson`
- Interactive map: `reports/analysis/yeonhui_yoga_week_gis_map.html`

## Geocoding Coverage

- Normalized studio/place rows: {len(studio_gis)}
- Rows with coordinates: {int(geocoded.sum())}
- Rows needing manual coordinate verification: {int(needs_manual.sum())}
- Location catalog rows: {len(location_catalog)}
- Location catalog rows with coordinates: {int(location_geocoded.sum())}
- Location catalog rows needing manual coordinate verification: {int(location_needs_manual.sum())}
- Class metric rows joined to GIS locations: {len(class_gis)}

## Spatial Reading

Marker size in the HTML map follows net reservations. Marker color follows review Hype. Gray markers are location-only nodes that currently have no reservation/review metric row. This is not a ranking table; it is a spatial reaction profile.

### High Net Reservation Nodes

{markdown_table(top_net, ["normalized_studio_key", "display_name", "net_reservation_count", "review_count", "reservation_hype", "review_hype", "distance_from_activity_center_km"])}

### High Review Nodes

{markdown_table(top_review, ["normalized_studio_key", "display_name", "net_reservation_count", "review_count", "review_rate_per_reservation", "review_hype", "satisfaction_hype"])}

### Outer Nodes In This Dataset

{markdown_table(top_distance, ["normalized_studio_key", "display_name", "address", "distance_from_activity_center_km", "net_reservation_count", "review_count"])}

## Limits

- Coordinates are generated from ON STUDIO class-description addresses, then geocoded through ArcGIS World Geocoding Service.
- `needs_manual_verification=true` rows should be checked against a primary map source before external publication.
- This pass maps venue/studio locations, not participant home locations. It therefore describes the event network footprint, not attendee catchment areas.
"""
    GIS_REPORT_MD.write_text(report, encoding="utf-8")


def main() -> None:
    locations = pd.read_csv(LOCATION_PATH)
    studio_metrics = pd.read_csv(STUDIO_HYPE_METRICS_PUBLIC)
    class_metrics = pd.read_csv(CLASS_HYPE_METRICS_PUBLIC)

    location_catalog = build_location_catalog_gis(locations)
    studio_gis = build_normalized_studio_metrics(studio_metrics, locations)
    studio_gis = add_spatial_summary(studio_gis)
    class_gis = build_class_gis(class_metrics, locations)

    ANALYSIS_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    location_catalog.to_csv(EVENT_LOCATION_CATALOG_GIS_CSV, index=False, encoding="utf-8-sig")
    studio_gis.to_csv(STUDIO_GIS_CSV, index=False, encoding="utf-8-sig")
    class_gis.to_csv(CLASS_GIS_CSV, index=False, encoding="utf-8-sig")
    write_geojson(studio_gis)
    frame_to_geojson(location_catalog, EVENT_LOCATION_CATALOG_GIS_GEOJSON)
    write_folium_map(studio_gis, location_catalog)
    write_report(studio_gis, class_gis, location_catalog)

    print(f"Wrote {EVENT_LOCATION_CATALOG_GIS_CSV}")
    print(f"Wrote {STUDIO_GIS_CSV}")
    print(f"Wrote {CLASS_GIS_CSV}")
    print(f"Wrote {STUDIO_GIS_GEOJSON}")
    print(f"Wrote {EVENT_LOCATION_CATALOG_GIS_GEOJSON}")
    print(f"Wrote {GIS_MAP_HTML}")
    print(f"Wrote {GIS_REPORT_MD}")


if __name__ == "__main__":
    main()
