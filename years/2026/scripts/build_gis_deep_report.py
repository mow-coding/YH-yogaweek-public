from __future__ import annotations

import html
import json
import math
import re
from datetime import date
from pathlib import Path

import pandas as pd

from review_processing_utils import ANALYSIS_PUBLIC_DIR, OBUD_DEIDENTIFIED_PUBLIC, REPORT_ANALYSIS_DIR, write_csv, write_text


LOCATION_NODES_CSV = ANALYSIS_PUBLIC_DIR / "location_nodes.csv"
LOCATION_DISTANCE_MATRIX_CSV = ANALYSIS_PUBLIC_DIR / "location_distance_matrix.csv"
CLASS_SCHEDULE_GIS_CSV = ANALYSIS_PUBLIC_DIR / "class_schedule_gis.csv"
TRANSITION_FEASIBILITY_PUBLIC_CSV = ANALYSIS_PUBLIC_DIR / "transition_feasibility_public.csv"
LOCATION_TRANSITION_FEASIBILITY_PUBLIC_CSV = ANALYSIS_PUBLIC_DIR / "location_transition_feasibility_public.csv"
LOCATION_MOBILITY_ROLE_METRICS_CSV = ANALYSIS_PUBLIC_DIR / "location_mobility_role_metrics.csv"

GIS_DEEP_REPORT_MD = REPORT_ANALYSIS_DIR / "gis_deep_analysis_report.md"
TRANSITION_MAP_HTML = REPORT_ANALYSIS_DIR / "yeonhui_yoga_week_transition_map.html"
TIME_SLIDER_MAP_HTML = REPORT_ANALYSIS_DIR / "yeonhui_yoga_week_time_slider_map.html"
SPACE_TIME_CUBE_HTML = REPORT_ANALYSIS_DIR / "yeonhui_yoga_week_space_time_cube.html"


STATUS_COLORS = {
    "comfortable": "#15803d",
    "tight": "#d97706",
    "difficult": "#dc2626",
    "overlap": "#7c3aed",
    "unknown": "#6b7280",
}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing input: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def markdown_table(frame: pd.DataFrame, columns: list[str], rows: int = 10) -> str:
    if frame.empty:
        return "_No rows._"
    subset = frame.head(rows)[columns].fillna("")
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for _, row in subset.iterrows():
        body.append("| " + " | ".join(str(row[column]).replace("|", "/") for column in columns) + " |")
    return "\n".join([header, separator, *body])


def fmt_metric(value: object, digits: int = 1) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "-"
    if float(numeric).is_integer():
        return f"{int(numeric):,}"
    return f"{float(numeric):,.{digits}f}"


def public_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"010[-\s]?\d{4}[-\s]?\d{4}", "PHONE_MASKED", text)
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "EMAIL_MASKED", text)
    return text.strip()


def popup_paragraph(value: object) -> str:
    text = public_text(value)
    escaped = html.escape(text)
    return escaped.replace("\n", "<br>")


def build_review_lookup(reviews: pd.DataFrame) -> dict[str, list[dict[str, str]]]:
    if reviews.empty or "class_base_key" not in reviews.columns:
        return {}
    frame = reviews.copy()
    frame["review_capture_order_sort"] = pd.to_numeric(frame.get("review_capture_order", ""), errors="coerce").fillna(9999)
    frame = frame.sort_values(["class_base_key", "review_capture_order_sort"])
    lookup: dict[str, list[dict[str, str]]] = {}
    for _, row in frame.iterrows():
        key = str(row.get("class_base_key") or "").strip()
        text = public_text(row.get("review_text"))
        if not key or not text:
            continue
        lookup.setdefault(key, []).append(
            {
                "review_id": public_text(row.get("review_id")),
                "date": public_text(row.get("review_date_iso")),
                "overall_rating": fmt_metric(row.get("overall_rating"), 1),
                "visit_count": fmt_metric(row.get("visit_count"), 0),
                "text": text,
            }
        )
    return lookup


def render_session_review_list(reviews: list[dict[str, str]]) -> str:
    if not reviews:
        return (
            '<p class="yw-review-empty">'
            "이 수업명에 연결된 공개 리뷰 본문은 아직 없습니다."
            "</p>"
        )
    items = []
    for review in reviews:
        meta_bits = []
        if review.get("date"):
            meta_bits.append(html.escape(review["date"]))
        if review.get("overall_rating") != "-":
            meta_bits.append(f"평점 {html.escape(review['overall_rating'])}")
        if review.get("visit_count") != "-":
            meta_bits.append(f"{html.escape(review['visit_count'])}번째 방문")
        meta = " · ".join(meta_bits)
        items.append(
            '<article class="yw-review-item">'
            f'<div class="yw-review-meta">{meta}</div>'
            f'<p>{popup_paragraph(review.get("text"))}</p>'
            "</article>"
        )
    return '<div class="yw-review-list">' + "".join(items) + "</div>"


def build_session_popup_html(row: dict[str, object], reviews: list[dict[str, str]], display_name: str) -> str:
    active_reservations = row.get("active_reservation_rows")
    review_hype = row.get("review_hype")
    review_count = row.get("review_count")
    class_title = public_text(row.get("class_title_base"))
    date_label = public_text(row.get("date_label"))
    return f"""
      <div class="yw-popup yw-session-popup">
        <h3>{html.escape(class_title)}</h3>
        <p class="yw-popup-subtitle">{html.escape(date_label)} · {html.escape(display_name)}</p>
        <table>
          <tr><td>이 회차 예약</td><td>{fmt_metric(active_reservations, 0)}건</td></tr>
          <tr><td>리뷰 Hype</td><td>{fmt_metric(review_hype, 1)}</td></tr>
          <tr><td>수업명 리뷰</td><td>{fmt_metric(review_count, 0)}건</td></tr>
        </table>
        <h4>이 수업명에 연결된 공개 리뷰 본문</h4>
        {render_session_review_list(reviews)}
        <p class="yw-popup-note">리뷰는 개인 식별자를 제거한 공개용 본문입니다. 같은 수업명이 여러 회차로 열린 경우, 리뷰는 회차가 아니라 수업명 기준으로 연결됩니다.</p>
      </div>
    """


def add_folium_panel(fmap: object, *, title: str, subtitle: str, legend_html: str) -> None:
    panel_html = f"""
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
        background: rgba(255, 253, 248, 0.96) !important;
      }}
      .leaflet-popup-content-wrapper {{
        border-radius: 8px;
        box-shadow: 0 18px 34px rgba(42, 24, 16, 0.20);
      }}
      .yw-panel {{
        position: fixed;
        z-index: 9999;
        background: rgba(255, 253, 248, 0.95);
        border: 1px solid rgba(229, 220, 200, 0.92);
        border-radius: 8px;
        box-shadow: 0 18px 38px rgba(42, 24, 16, 0.18);
        color: #2a1810;
        backdrop-filter: blur(10px);
      }}
      .yw-title-panel {{
        top: 16px;
        left: 56px;
        width: min(430px, calc(100% - 96px));
        padding: 16px 18px 15px;
        border-top: 4px solid #f9a212;
      }}
      .yw-title-panel h1 {{
        margin: 2px 0 7px;
        font-size: 20px;
        font-weight: 800;
        line-height: 1.3;
        letter-spacing: 0;
        word-break: keep-all;
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
      .yw-row span:last-child {{
        word-break: keep-all;
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
        width: 24px;
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
        min-width: 250px;
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
    fmap.get_root().html.add_child(__import__("folium").Element(panel_html))


def weighted_mean(frame: pd.DataFrame, value_column: str, weight_column: str = "transition_count") -> float | None:
    if frame.empty:
        return None
    values = pd.to_numeric(frame[value_column], errors="coerce")
    weights = pd.to_numeric(frame[weight_column], errors="coerce").fillna(0)
    valid = values.notna() & weights.gt(0)
    if not valid.any():
        return None
    return float((values[valid] * weights[valid]).sum() / weights[valid].sum())


def build_location_mobility_metrics(nodes: pd.DataFrame, location_transitions: pd.DataFrame) -> pd.DataFrame:
    transitions = location_transitions.copy()
    if transitions.empty:
        transitions = pd.DataFrame(
            columns=[
                "origin_location_key",
                "destination_location_key",
                "feasibility_status",
                "transition_count",
                "avg_gap_minutes",
                "avg_walk_minutes",
            ]
        )
    for column in ["transition_count", "avg_gap_minutes", "avg_walk_minutes", "avg_walk_distance_m"]:
        if column in transitions.columns:
            transitions[column] = pd.to_numeric(transitions[column], errors="coerce")

    rows: list[dict[str, object]] = []
    for _, node in nodes.iterrows():
        key = str(node.get("location_key") or "")
        outgoing = transitions[transitions["origin_location_key"].astype(str).eq(key)]
        incoming = transitions[transitions["destination_location_key"].astype(str).eq(key)]
        same = transitions[
            transitions["origin_location_key"].astype(str).eq(key)
            & transitions["destination_location_key"].astype(str).eq(key)
        ]
        related = transitions[
            transitions["origin_location_key"].astype(str).eq(key)
            | transitions["destination_location_key"].astype(str).eq(key)
        ]
        outgoing_count = pd.to_numeric(outgoing.get("transition_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
        incoming_count = pd.to_numeric(incoming.get("transition_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
        same_count = pd.to_numeric(same.get("transition_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
        cross_outgoing = pd.to_numeric(
            outgoing[outgoing["origin_location_key"].ne(outgoing["destination_location_key"])].get("transition_count", pd.Series(dtype=float)),
            errors="coerce",
        ).fillna(0).sum()
        cross_incoming = pd.to_numeric(
            incoming[incoming["origin_location_key"].ne(incoming["destination_location_key"])].get("transition_count", pd.Series(dtype=float)),
            errors="coerce",
        ).fillna(0).sum()
        status_counts = {
            status: pd.to_numeric(
                related[related["feasibility_status"].astype(str).eq(status)].get("transition_count", pd.Series(dtype=float)),
                errors="coerce",
            )
            .fillna(0)
            .sum()
            for status in STATUS_COLORS
        }
        transfer_hub_score = float(cross_outgoing + cross_incoming + same_count * 0.5)
        total_related = max(float(outgoing_count + incoming_count - same_count), 0.0)
        comfortable_share = (
            round(float(status_counts.get("comfortable", 0)) / total_related, 4) if total_related else None
        )
        rows.append(
            {
                "location_key": key,
                "display_name": node.get("display_name", ""),
                "latitude": node.get("latitude", ""),
                "longitude": node.get("longitude", ""),
                "outgoing_transition_count": int(outgoing_count),
                "incoming_transition_count": int(incoming_count),
                "same_location_transition_count": int(same_count),
                "cross_location_outgoing_count": int(cross_outgoing),
                "cross_location_incoming_count": int(cross_incoming),
                "comfortable_transition_count": int(status_counts.get("comfortable", 0)),
                "tight_transition_count": int(status_counts.get("tight", 0)),
                "difficult_transition_count": int(status_counts.get("difficult", 0)),
                "overlap_transition_count": int(status_counts.get("overlap", 0)),
                "unknown_transition_count": int(status_counts.get("unknown", 0)),
                "comfortable_transition_share": comfortable_share,
                "avg_related_gap_minutes": None if weighted_mean(related, "avg_gap_minutes") is None else round(weighted_mean(related, "avg_gap_minutes"), 2),
                "avg_related_walk_minutes": None if weighted_mean(related, "avg_walk_minutes") is None else round(weighted_mean(related, "avg_walk_minutes"), 2),
                "transfer_hub_score": round(transfer_hub_score, 2),
                "mobility_role_note": "같은 날 복수 예약 흐름에서 해당 장소가 연결점으로 등장한 정도입니다. 실제 GPS 이동 기록이 아니라 예약 시간표 기반 후보입니다.",
            }
        )
    return pd.DataFrame(rows).sort_values("transfer_hub_score", ascending=False)


def write_transition_map(
    nodes: pd.DataFrame,
    location_transitions: pd.DataFrame,
    mobility_metrics: pd.DataFrame,
) -> bool:
    try:
        import folium
        from folium import FeatureGroup, LayerControl
        from folium.plugins import Fullscreen, MiniMap, MousePosition
    except ImportError:
        return False

    nodes = nodes.copy()
    nodes["latitude"] = pd.to_numeric(nodes["latitude"], errors="coerce")
    nodes["longitude"] = pd.to_numeric(nodes["longitude"], errors="coerce")
    valid_nodes = nodes[nodes["latitude"].notna() & nodes["longitude"].notna()]
    if valid_nodes.empty:
        return False

    node_lookup = valid_nodes.set_index("location_key").to_dict("index")
    mobility_lookup = mobility_metrics.set_index("location_key").to_dict("index") if not mobility_metrics.empty else {}
    center = [float(valid_nodes["latitude"].mean()), float(valid_nodes["longitude"].mean())]
    fmap = folium.Map(location=center, zoom_start=14, tiles="CartoDB positron", control_scale=True)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", show=False).add_to(fmap)
    try:
        Fullscreen(position="topleft", title="전체 화면", title_cancel="전체 화면 닫기").add_to(fmap)
        MiniMap(toggle_display=True, position="bottomleft").add_to(fmap)
        MousePosition(position="bottomright", separator=" / ", prefix="좌표").add_to(fmap)
    except Exception:
        pass

    add_folium_panel(
        fmap,
        title="동선 가능성 지도",
        subtitle="같은 날 여러 수업을 예약한 흐름을 장소 쌍 단위로 집계했습니다. 선은 실제 GPS가 아니라 시간표상 가능한 이동 후보입니다.",
        legend_html="""
          <h2>읽는 법</h2>
          <div class="yw-row"><span class="yw-line" style="border-color:#15803d"></span><span>여유 있음</span></div>
          <div class="yw-row"><span class="yw-line" style="border-color:#d97706"></span><span>빠듯함</span></div>
          <div class="yw-row"><span class="yw-line" style="border-color:#dc2626"></span><span>시간표상 어려움</span></div>
          <div class="yw-row"><span class="yw-line" style="border-color:#7c3aed"></span><span>시간 겹침</span></div>
          <div class="yw-row"><span class="yw-dot" style="background:#f9a212"></span><span>원이 클수록 이동 허브성 큼</span></div>
          <div class="yw-note">두꺼운 선은 같은 장소 쌍이 더 자주 등장했다는 뜻입니다.</div>
        """,
    )

    node_layer = FeatureGroup(name="장소별 이동 허브성", show=True)
    comfortable_layer = FeatureGroup(name="여유 있음", show=True)
    tight_layer = FeatureGroup(name="빠듯함", show=True)
    difficult_layer = FeatureGroup(name="시간표상 어려움/겹침", show=True)

    for _, node in valid_nodes.iterrows():
        mobility = mobility_lookup.get(str(node.get("location_key") or ""), {})
        hub_score = pd.to_numeric(pd.Series([mobility.get("transfer_hub_score")]), errors="coerce").iloc[0]
        radius = 6 if pd.isna(hub_score) else min(24, 6 + math.sqrt(max(float(hub_score), 0)) * 1.7)
        popup = folium.Popup(
            f"""
            <div class="yw-popup">
              <h3>{html.escape(str(node.get('display_name') or node.get('location_key')))}</h3>
              <table>
                <tr><td>주소</td><td>{html.escape(str(node.get('address') or ''))}</td></tr>
                <tr><td>이동 허브성</td><td>{fmt_metric(mobility.get('transfer_hub_score'), 1)}</td></tr>
                <tr><td>들어오는 흐름</td><td>{fmt_metric(mobility.get('incoming_transition_count'), 0)}</td></tr>
                <tr><td>나가는 흐름</td><td>{fmt_metric(mobility.get('outgoing_transition_count'), 0)}</td></tr>
                <tr><td>장소 내 연속 수강</td><td>{fmt_metric(mobility.get('same_location_transition_count'), 0)}</td></tr>
                <tr><td>평균 여유</td><td>{fmt_metric(mobility.get('avg_related_gap_minutes'), 1)}분</td></tr>
                <tr><td>평균 도보</td><td>{fmt_metric(mobility.get('avg_related_walk_minutes'), 1)}분</td></tr>
              </table>
            </div>
            """,
            max_width=340,
        )
        folium.CircleMarker(
            location=[float(node["latitude"]), float(node["longitude"])],
            radius=radius,
            color="#2a1810",
            weight=2,
            fill=True,
            fill_color="#f9a212",
            fill_opacity=0.78,
            popup=popup,
            tooltip=str(node.get("display_name") or node.get("location_key")),
        ).add_to(node_layer)

    if not location_transitions.empty:
        frame = location_transitions.copy()
        frame["transition_count"] = pd.to_numeric(frame["transition_count"], errors="coerce").fillna(0)
        frame = frame[frame["transition_count"].gt(0)]
        frame = frame[frame["origin_location_key"].ne(frame["destination_location_key"])]
        frame = frame.sort_values("transition_count", ascending=False).head(80)
        for _, row in frame.iterrows():
            origin = node_lookup.get(str(row["origin_location_key"]))
            destination = node_lookup.get(str(row["destination_location_key"]))
            if not origin or not destination:
                continue
            status = str(row.get("feasibility_status") or "unknown")
            color = STATUS_COLORS.get(status, "gray")
            weight = min(8, 1 + float(row["transition_count"]) ** 0.5)
            dash_array = None
            target_layer = comfortable_layer
            if status == "tight":
                dash_array = "8, 7"
                target_layer = tight_layer
            elif status in {"difficult", "overlap"}:
                dash_array = "3, 7"
                target_layer = difficult_layer
            popup = folium.Popup(
                f"""
                <div class="yw-popup">
                  <h3>{html.escape(str(row.get('origin_display_name')))} → {html.escape(str(row.get('destination_display_name')))}</h3>
                  <table>
                    <tr><td>이동 후보</td><td>{fmt_metric(row.get('transition_count'), 0)}건</td></tr>
                    <tr><td>판정</td><td>{html.escape(str(row.get('feasibility_label') or status))}</td></tr>
                    <tr><td>평균 이동 여유</td><td>{fmt_metric(row.get('avg_gap_minutes'), 1)}분</td></tr>
                    <tr><td>최소/최대 여유</td><td>{fmt_metric(row.get('min_gap_minutes'), 1)} / {fmt_metric(row.get('max_gap_minutes'), 1)}분</td></tr>
                    <tr><td>평균 도보 시간</td><td>{fmt_metric(row.get('avg_walk_minutes'), 1)}분</td></tr>
                    <tr><td>도보거리 산정</td><td>{html.escape(str(row.get('walk_method') or ''))}</td></tr>
                  </table>
                </div>
                """,
                max_width=360,
            )
            folium.PolyLine(
                locations=[
                    [float(origin["latitude"]), float(origin["longitude"])],
                    [float(destination["latitude"]), float(destination["longitude"])],
                ],
                color=color,
                weight=weight,
                opacity=0.72,
                dash_array=dash_array,
                popup=popup,
                tooltip=f"{row.get('origin_display_name')} -> {row.get('destination_display_name')}",
            ).add_to(target_layer)

    node_layer.add_to(fmap)
    comfortable_layer.add_to(fmap)
    tight_layer.add_to(fmap)
    difficult_layer.add_to(fmap)
    bounds = [
        [float(valid_nodes["latitude"].min()), float(valid_nodes["longitude"].min())],
        [float(valid_nodes["latitude"].max()), float(valid_nodes["longitude"].max())],
    ]
    fmap.fit_bounds(bounds, padding=(28, 28))
    LayerControl(collapsed=False).add_to(fmap)

    TRANSITION_MAP_HTML.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(TRANSITION_MAP_HTML))
    return True


def review_hype_color(value: float) -> str:
    if pd.isna(value):
        return "#6b7280"
    if value >= 75:
        return "#c2410c"
    if value >= 55:
        return "#15803d"
    if value >= 35:
        return "#2563eb"
    return "#6b7280"


def write_time_slider_map(class_schedule: pd.DataFrame) -> bool:
    try:
        import folium
        from folium.plugins import Fullscreen, MiniMap, MousePosition, TimestampedGeoJson
    except ImportError:
        return False

    frame = class_schedule.copy()
    frame["latitude"] = pd.to_numeric(frame["latitude"], errors="coerce")
    frame["longitude"] = pd.to_numeric(frame["longitude"], errors="coerce")
    frame["start_datetime"] = pd.to_datetime(frame["start_datetime_iso"], errors="coerce")
    frame["active_reservation_rows"] = pd.to_numeric(frame["active_reservation_rows"], errors="coerce").fillna(0)
    frame["review_hype"] = pd.to_numeric(frame["review_hype"], errors="coerce")
    frame = frame[frame["latitude"].notna() & frame["longitude"].notna() & frame["start_datetime"].notna()]
    if frame.empty:
        return False

    center = [float(frame["latitude"].mean()), float(frame["longitude"].mean())]
    fmap = folium.Map(location=center, zoom_start=14, tiles="CartoDB positron", control_scale=True)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", show=False).add_to(fmap)
    try:
        Fullscreen(position="topleft", title="전체 화면", title_cancel="전체 화면 닫기").add_to(fmap)
        MiniMap(toggle_display=True, position="bottomleft").add_to(fmap)
        MousePosition(position="bottomright", separator=" / ", prefix="좌표").add_to(fmap)
    except Exception:
        pass

    intro = """
    <div class="yw-panel yw-title-panel">
      <div class="yw-eyebrow">2026 연희 요가 위크 GIS</div>
      <h1>시간 흐름 지도</h1>
      <p>하단 슬라이더를 움직이면 행사 기간 동안 어느 장소에서 수업이 열렸는지 순서대로 나타납니다.</p>
    </div>
    <div class="yw-panel yw-legend-panel">
      <h2>읽는 법</h2>
      <div class="yw-row"><span class="yw-dot" style="background:#c2410c"></span><span>리뷰 Hype 높음</span></div>
      <div class="yw-row"><span class="yw-dot" style="background:#15803d"></span><span>리뷰 Hype 중간 이상</span></div>
      <div class="yw-row"><span class="yw-dot" style="background:#2563eb"></span><span>리뷰 Hype 보통</span></div>
      <div class="yw-row"><span class="yw-dot" style="background:#6b7280"></span><span>낮음/정보 부족</span></div>
      <div class="yw-note">원 크기는 예약 규모입니다. 시간-공간 큐브보다 먼저 보면 전체 흐름을 읽기 쉽습니다.</div>
    </div>
    <style>
      .leaflet-container {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #fffaf0;
      }
      .leaflet-control-layers,
      .leaflet-bar a,
      .leaflet-control-scale-line {
        border-color: rgba(42, 24, 16, 0.14) !important;
        box-shadow: 0 8px 22px rgba(42, 24, 16, 0.12) !important;
      }
      .leaflet-control-layers { border-radius: 8px; color: #2a1810; }
      .leaflet-popup-content-wrapper {
        border-radius: 8px;
        box-shadow: 0 18px 34px rgba(42, 24, 16, 0.20);
      }
      .yw-panel {
        position: fixed;
        z-index: 9999;
        background: rgba(255, 253, 248, 0.92);
        border: 1px solid rgba(229, 220, 200, 0.92);
        border-radius: 8px;
        box-shadow: 0 18px 38px rgba(42, 24, 16, 0.18);
        color: #2a1810;
        backdrop-filter: blur(10px);
      }
      .yw-title-panel {
        top: 16px;
        left: 56px;
        width: min(420px, calc(100% - 96px));
        padding: 15px 17px 14px;
      }
      .yw-title-panel h1 {
        margin: 2px 0 7px;
        font-size: 19px;
        font-weight: 800;
        line-height: 1.3;
        letter-spacing: 0;
      }
      .yw-title-panel p {
        margin: 0;
        color: #64584e;
        font-size: 13px;
        line-height: 1.48;
      }
      .yw-eyebrow {
        font-size: 11px;
        letter-spacing: 0;
        color: #9a5a00;
        font-weight: 700;
      }
      .yw-legend-panel {
        right: 18px;
        bottom: 74px;
        width: min(320px, calc(100% - 36px));
        padding: 13px 15px;
        font-size: 12px;
        line-height: 1.45;
      }
      .yw-legend-panel h2 { margin: 0 0 8px; font-size: 13px; }
      .yw-row { display: flex; align-items: center; gap: 8px; margin: 6px 0; }
      .yw-dot {
        width: 11px;
        height: 11px;
        border-radius: 50%;
        display: inline-block;
        border: 1px solid rgba(42, 24, 16, 0.25);
        flex: 0 0 auto;
      }
      .yw-note { margin-top: 8px; color: #6f645a; }
      @media (max-width: 720px) {
        .yw-title-panel { top: 10px; left: 44px; width: calc(100% - 58px); padding: 11px 12px; }
        .yw-legend-panel { right: 10px; bottom: 66px; padding: 10px 12px; }
      }
    </style>
    """
    fmap.get_root().html.add_child(folium.Element(intro))

    features = []
    for _, row in frame.sort_values("start_datetime").iterrows():
        reservations = float(row["active_reservation_rows"])
        review_hype = float(row["review_hype"]) if pd.notna(row["review_hype"]) else float("nan")
        radius = max(5, min(18, 4 + reservations * 0.35))
        color = review_hype_color(review_hype)
        display_name = html.escape(str(row.get("display_name") or row.get("location_key") or ""))
        class_title = html.escape(str(row.get("class_title_base") or ""))
        start_label = html.escape(str(row.get("start_datetime_iso") or ""))
        popup = (
            f"<b>{display_name}</b><br>"
            f"{class_title}<br>"
            f"시작: {start_label}<br>"
            f"예약: {int(reservations)}<br>"
            f"리뷰 Hype: {'' if pd.isna(review_hype) else round(review_hype, 2)}"
        )
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["longitude"]), float(row["latitude"])],
                },
                "properties": {
                    "time": row["start_datetime"].isoformat(),
                    "popup": popup,
                    "tooltip": f"{display_name} / {class_title}",
                    "icon": "circle",
                    "iconstyle": {
                        "fillColor": color,
                        "fillOpacity": 0.78,
                        "stroke": True,
                        "color": "#111827",
                        "weight": 1,
                        "radius": radius,
                    },
                    "style": {
                        "color": color,
                    },
                },
            }
        )

    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="PT1H",
        add_last_point=False,
        auto_play=False,
        loop=False,
        loop_button=True,
        max_speed=2,
        date_options="YYYY-MM-DD HH:mm",
        time_slider_drag_update=True,
        duration="PT2H",
    ).add_to(fmap)
    bounds = [
        [float(frame["latitude"].min()), float(frame["longitude"].min())],
        [float(frame["latitude"].max()), float(frame["longitude"].max())],
    ]
    fmap.fit_bounds(bounds, padding=(28, 28))

    TIME_SLIDER_MAP_HTML.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(TIME_SLIDER_MAP_HTML))
    return True


def write_space_time_cube(class_schedule: pd.DataFrame, reviews: pd.DataFrame) -> bool:
    try:
        import folium
        from folium import FeatureGroup, LayerControl
        from folium.plugins import Fullscreen, MiniMap, MousePosition
    except ImportError:
        return False

    frame = class_schedule.copy()
    frame["latitude"] = pd.to_numeric(frame["latitude"], errors="coerce")
    frame["longitude"] = pd.to_numeric(frame["longitude"], errors="coerce")
    frame["start_datetime"] = pd.to_datetime(frame["start_datetime_iso"], errors="coerce")
    frame["active_reservation_rows"] = pd.to_numeric(frame["active_reservation_rows"], errors="coerce").fillna(0)
    frame["review_hype"] = pd.to_numeric(frame["review_hype"], errors="coerce")
    frame = frame[frame["latitude"].notna() & frame["longitude"].notna() & frame["start_datetime"].notna()]
    if frame.empty:
        return False

    min_time = frame["start_datetime"].min()
    max_time = frame["start_datetime"].max()
    total_seconds = max((max_time - min_time).total_seconds(), 1)
    frame["time_fraction"] = (frame["start_datetime"] - min_time).dt.total_seconds() / total_seconds
    frame["date_label"] = frame["start_datetime"].dt.strftime("%m/%d %H:%M")

    center = [float(frame["latitude"].mean()), float(frame["longitude"].mean())]
    fmap = folium.Map(location=center, zoom_start=14, tiles="CartoDB positron", control_scale=True)
    map_name = fmap.get_name()
    review_lookup = build_review_lookup(reviews)
    session_popup_data: dict[str, dict[str, object]] = {}
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", show=False).add_to(fmap)
    try:
        Fullscreen(position="topleft", title="전체 화면", title_cancel="전체 화면 닫기").add_to(fmap)
        MiniMap(toggle_display=True, position="bottomleft").add_to(fmap)
        MousePosition(position="bottomright", separator=" / ", prefix="좌표").add_to(fmap)
    except Exception:
        pass

    panel_html = f"""
    <div class="yw-panel yw-title-panel">
      <div class="yw-eyebrow">2026 연희 요가 위크 GIS</div>
      <h1>지도 위 시간-공간 큐브</h1>
      <p>장소의 실제 위치 위에 시간축을 세웠습니다. 아래쪽은 {min_time.strftime('%m/%d %H:%M')}, 위쪽은 {max_time.strftime('%m/%d %H:%M')}입니다.</p>
    </div>
    <div class="yw-panel yw-legend-panel">
      <h2>읽는 법</h2>
      <div class="yw-row"><span class="yw-dot" style="background:#c2410c"></span><span>리뷰 Hype 높음</span></div>
      <div class="yw-row"><span class="yw-dot" style="background:#15803d"></span><span>리뷰 Hype 중간 이상</span></div>
      <div class="yw-row"><span class="yw-dot" style="background:#2563eb"></span><span>리뷰 Hype 보통</span></div>
      <div class="yw-row"><span class="yw-dot" style="background:#6b7280"></span><span>낮음/정보 부족</span></div>
      <div class="yw-axis-demo"><span>위: 행사 후반</span><i></i><span>아래: 행사 초반</span></div>
      <div class="yw-time-control">
        <label for="yw-cube-time-slider">시간 필터</label>
        <input id="yw-cube-time-slider" type="range" min="0" max="100" step="1" value="100">
        <div class="yw-time-control-meta">
          <span id="yw-cube-time-label">전체 기간 보기</span>
          <span id="yw-cube-visible-count"></span>
        </div>
      </div>
      <div class="yw-note">세로 막대 하나가 한 장소입니다. 막대 위의 점 하나는 수업 1개이고, 점이 클수록 예약 규모가 큽니다.</div>
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
        background: rgba(255, 253, 248, 0.96) !important;
      }}
      .leaflet-popup-content-wrapper {{
        border-radius: 8px;
        box-shadow: 0 18px 34px rgba(42, 24, 16, 0.20);
      }}
      .yw-panel {{
        position: fixed;
        z-index: 9999;
        background: rgba(255, 253, 248, 0.95);
        border: 1px solid rgba(229, 220, 200, 0.92);
        border-radius: 8px;
        box-shadow: 0 18px 38px rgba(42, 24, 16, 0.18);
        color: #2a1810;
        backdrop-filter: blur(10px);
      }}
      .yw-title-panel {{
        top: 16px;
        left: 56px;
        width: min(440px, calc(100% - 96px));
        padding: 16px 18px 15px;
        border-top: 4px solid #f9a212;
      }}
      .yw-title-panel h1 {{
        margin: 2px 0 7px;
        font-size: 20px;
        font-weight: 800;
        line-height: 1.3;
        letter-spacing: 0;
        word-break: keep-all;
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
      .yw-row span:last-child {{
        word-break: keep-all;
      }}
      .yw-dot {{
        width: 11px;
        height: 11px;
        border-radius: 50%;
        display: inline-block;
        border: 1px solid rgba(42, 24, 16, 0.25);
        flex: 0 0 auto;
      }}
      .yw-note {{
        margin-top: 8px;
        color: #6f645a;
      }}
      .yw-axis-demo {{
        display: grid;
        grid-template-columns: 84px 12px 1fr;
        gap: 8px;
        align-items: center;
        margin-top: 10px;
        color: #6f645a;
      }}
      .yw-axis-demo i {{
        width: 3px;
        height: 44px;
        display: block;
        border-radius: 999px;
        background: linear-gradient(#2a1810, #f9a212);
      }}
      .yw-time-control {{
        margin-top: 12px;
        padding: 12px 0 0;
        border-top: 1px solid rgba(229, 220, 200, 0.9);
      }}
      .yw-time-control label {{
        display: block;
        margin-bottom: 6px;
        color: #2a1810;
        font-weight: 700;
      }}
      .yw-time-control input[type="range"] {{
        width: 100%;
        accent-color: #f9a212;
        cursor: pointer;
      }}
      .yw-time-control-meta {{
        display: flex;
        justify-content: space-between;
        gap: 8px;
        margin-top: 4px;
        color: #6f645a;
        font-size: 11px;
      }}
      .yw-tower-icon {{
        background: transparent;
        border: 0;
      }}
      .yw-time-tower {{
        position: relative;
        width: 126px;
        height: 310px;
        pointer-events: none;
        transform: translateY(-4px);
      }}
      .yw-time-tower .tower-glow {{
        position: absolute;
        left: 34px;
        bottom: 30px;
        width: 58px;
        height: 242px;
        border-radius: 999px;
        background: linear-gradient(180deg, rgba(249, 162, 18, 0.22), rgba(47, 111, 78, 0.12));
        box-shadow: 0 16px 30px rgba(42,24,16,0.20);
      }}
      .yw-time-tower .tower-axis {{
        position: absolute;
        left: 61px;
        bottom: 34px;
        width: 8px;
        height: 238px;
        border-radius: 999px;
        background: linear-gradient(180deg, rgba(42,24,16,0.96), rgba(249,162,18,0.96));
        box-shadow: 0 8px 20px rgba(42,24,16,0.30);
      }}
      .yw-time-tower .tower-axis::before,
      .yw-time-tower .tower-axis::after {{
        content: "";
        position: absolute;
        left: -18px;
        width: 44px;
        border-top: 2px dashed rgba(42,24,16,0.36);
      }}
      .yw-time-tower .tower-axis::before {{ top: 60px; }}
      .yw-time-tower .tower-axis::after {{ top: 119px; }}
      .yw-time-tower .tower-dot {{
        position: absolute;
        border-radius: 50%;
        padding: 0;
        appearance: none;
        cursor: pointer;
        display: block;
        transform: translate(-50%, 50%);
        border: 2px solid rgba(255, 253, 248, 0.96);
        outline: 1px solid rgba(42,24,16,0.55);
        box-shadow: 0 3px 10px rgba(42,24,16,0.34);
        pointer-events: auto;
        transition: opacity 160ms ease, filter 160ms ease, transform 160ms ease;
      }}
      .yw-time-tower .tower-dot:hover {{
        transform: translate(-50%, 50%) scale(1.12);
        z-index: 3;
      }}
      .yw-time-tower .tower-dot.is-future {{
        opacity: 0.12;
        filter: grayscale(1);
        pointer-events: none;
        transform: translate(-50%, 50%) scale(0.72);
      }}
      .yw-time-tower .tower-label {{
        position: absolute;
        left: 50%;
        bottom: 0;
        transform: translateX(-50%);
        max-width: 118px;
        padding: 3px 8px;
        border-radius: 999px;
        background: rgba(255,253,248,0.98);
        border: 1px solid rgba(42,24,16,0.28);
        color: #2a1810;
        font-size: 12px;
        font-weight: 700;
        line-height: 1.25;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        box-shadow: 0 5px 14px rgba(42,24,16,0.18);
      }}
      .yw-popup {{
        min-width: 270px;
        max-width: 420px;
        color: #2a1810;
      }}
      .yw-popup h3 {{
        margin: 0 0 7px;
        font-size: 15px;
      }}
      .yw-popup h4 {{
        margin: 12px 0 7px;
        font-size: 13px;
      }}
      .yw-popup-subtitle {{
        margin: -3px 0 8px;
        color: #75685c;
        font-size: 12px;
        line-height: 1.45;
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
      .yw-review-list {{
        display: grid;
        gap: 8px;
        max-height: 230px;
        overflow-y: auto;
        padding-right: 4px;
      }}
      .yw-review-item {{
        padding: 8px 9px;
        border: 1px solid #efe6d4;
        border-radius: 8px;
        background: #fffaf0;
      }}
      .yw-review-item p {{
        margin: 4px 0 0;
        color: #2a1810;
        font-size: 12px;
        line-height: 1.55;
        word-break: keep-all;
        overflow-wrap: break-word;
      }}
      .yw-review-meta,
      .yw-popup-note,
      .yw-review-empty {{
        color: #75685c;
        font-size: 11px;
        line-height: 1.45;
      }}
      .yw-popup-note {{
        margin: 9px 0 0;
      }}
      .yw-review-empty {{
        margin: 0;
        padding: 8px 9px;
        border: 1px dashed #dacdb5;
        border-radius: 8px;
        background: #fffdf8;
      }}
      @media (max-width: 720px) {{
        .yw-time-tower {{
          transform: scale(0.72) translateY(32px);
          transform-origin: bottom center;
        }}
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
    <script>
      (function () {{
        var mapName = {json.dumps(map_name)};
        function cubeMap() {{
          return window[mapName] || null;
        }}
        function bindDotPopups(dots) {{
          dots.forEach(function (dot) {{
            if (dot.getAttribute("data-popup-bound") === "1") {{
              return;
            }}
            dot.setAttribute("data-popup-bound", "1");
            dot.addEventListener("click", function (event) {{
              if (window.L && L.DomEvent) {{
                L.DomEvent.stopPropagation(event);
              }} else if (event) {{
                event.stopPropagation();
              }}
              if (event) {{
                event.preventDefault();
              }}
              var popupId = dot.getAttribute("data-popup-id");
              var popupData = window.YW_CUBE_SESSION_POPUPS && window.YW_CUBE_SESSION_POPUPS[popupId];
              var map = cubeMap();
              if (!popupData || !map || !window.L) {{
                return;
              }}
              L.popup({{ maxWidth: 460, className: "yw-session-popup-shell" }})
                .setLatLng(popupData.latlng)
                .setContent(popupData.html)
                .openOn(map);
            }});
          }});
        }}
        function initCubeSlider(retry) {{
          var slider = document.getElementById("yw-cube-time-slider");
          var label = document.getElementById("yw-cube-time-label");
          var count = document.getElementById("yw-cube-visible-count");
          var dots = Array.prototype.slice.call(document.querySelectorAll(".tower-dot"));
          if (!slider || dots.length === 0) {{
            if ((retry || 0) < 30) {{
              window.setTimeout(function () {{ initCubeSlider((retry || 0) + 1); }}, 250);
            }}
            return;
          }}
          bindDotPopups(dots);
          function update() {{
            var threshold = Number(slider.value) / 100;
            var visible = 0;
            var currentLabel = "";
            var currentFraction = -1;
            dots.forEach(function (dot) {{
              var fraction = Number(dot.getAttribute("data-fraction") || "0");
              var show = fraction <= threshold + 0.000001;
              dot.classList.toggle("is-future", !show);
              if (show) {{
                visible += 1;
                if (fraction >= currentFraction) {{
                  currentFraction = fraction;
                  currentLabel = dot.getAttribute("data-label") || currentLabel;
                }}
              }}
            }});
            if (label) {{
              label.textContent = currentLabel ? currentLabel + "까지 보기" : "첫 수업 전";
            }}
            if (count) {{
              count.textContent = visible + "/" + dots.length + "개 수업";
            }}
          }}
          slider.addEventListener("input", update);
          update();
        }}
        if (document.readyState === "loading") {{
          document.addEventListener("DOMContentLoaded", function () {{ initCubeSlider(0); }});
        }} else {{
          initCubeSlider(0);
        }}
      }})();
    </script>
    """
    fmap.get_root().html.add_child(folium.Element(panel_html))

    tower_layer = FeatureGroup(name="시간-공간 타워", show=True)
    base_layer = FeatureGroup(name="장소 기준점", show=True)

    def session_popup_rows(group: pd.DataFrame) -> str:
        top_sessions = group.sort_values("active_reservation_rows", ascending=False).head(6)
        rows = []
        for _, item in top_sessions.iterrows():
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(item.get('date_label') or ''))}</td>"
                f"<td>{html.escape(str(item.get('class_title_base') or ''))}</td>"
                f"<td>{fmt_metric(item.get('active_reservation_rows'), 0)}</td>"
                "</tr>"
            )
        return "".join(rows)

    for location_key, group in frame.sort_values("start_datetime").groupby("normalized_studio_key", dropna=False):
        first = group.iloc[0]
        display_name = str(first.get("display_name") or location_key)
        dots = []
        for index, row in enumerate(group.to_dict("records")):
            fraction = max(0, min(1, float(row["time_fraction"])))
            bottom = 34 + fraction * 238
            reservations = float(row.get("active_reservation_rows") or 0)
            size = max(10, min(28, 8 + math.sqrt(max(reservations, 0)) * 3.1))
            review_hype = pd.to_numeric(pd.Series([row.get("review_hype")]), errors="coerce").iloc[0]
            color = review_hype_color(float(review_hype)) if pd.notna(review_hype) else "#6b7280"
            left = 64 + ((index % 7) - 3) * 10
            session_id = f"session_{len(session_popup_data) + 1:04d}"
            class_reviews = review_lookup.get(str(row.get("class_base_key") or "").strip(), [])
            session_popup_data[session_id] = {
                "latlng": [float(row["latitude"]), float(row["longitude"])],
                "html": build_session_popup_html(row, class_reviews, display_name),
            }
            title = (
                f"{display_name} / {row.get('date_label')} / "
                f"{row.get('class_title_base')} / 예약 {int(reservations)} / "
                f"리뷰 Hype {fmt_metric(review_hype, 1)}"
            )
            dots.append(
                f'<button type="button" class="tower-dot" title="{html.escape(title, quote=True)}" '
                f'aria-label="{html.escape(title, quote=True)}" data-popup-id="{html.escape(session_id, quote=True)}" '
                f'data-fraction="{fraction:.6f}" data-label="{html.escape(str(row.get("date_label") or ""), quote=True)}" '
                f'style="left:{left}px; bottom:{bottom:.1f}px; width:{size:.1f}px; height:{size:.1f}px; background:{color};"></button>'
            )

        tower_html = (
            '<div class="yw-time-tower">'
            '<div class="tower-glow"></div>'
            '<div class="tower-axis"></div>'
            + "".join(dots)
            + f'<div class="tower-label">{html.escape(display_name)}</div>'
            "</div>"
        )
        popup_html = f"""
            <div class="yw-popup">
              <h3>{html.escape(display_name)}</h3>
              <table>
                <tr><td>수업 세션</td><td>{fmt_metric(len(group), 0)}개</td></tr>
                <tr><td>예약 합계</td><td>{fmt_metric(group['active_reservation_rows'].sum(), 0)}건</td></tr>
                <tr><td>첫 수업</td><td>{html.escape(str(group['date_label'].iloc[0]))}</td></tr>
                <tr><td>마지막 수업</td><td>{html.escape(str(group['date_label'].iloc[-1]))}</td></tr>
              </table>
              <p style="margin:10px 0 6px; color:#75685c;">예약 규모가 큰 수업</p>
              <table>
                <tr><td>시간</td><td>수업</td><td>예약</td></tr>
                {session_popup_rows(group)}
              </table>
            </div>
            """
        lat = float(first["latitude"])
        lon = float(first["longitude"])
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=tower_html,
                icon_size=(126, 310),
                icon_anchor=(63, 300),
                class_name="yw-tower-icon",
            ),
            tooltip=f"{display_name} 시간-공간 타워",
            popup=folium.Popup(popup_html, max_width=430),
        ).add_to(tower_layer)
        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            color="#2a1810",
            weight=2,
            fill=True,
            fill_color="#f9a212",
            fill_opacity=0.84,
            tooltip=display_name,
            popup=folium.Popup(popup_html, max_width=430),
        ).add_to(base_layer)

    popup_data_json = json.dumps(session_popup_data, ensure_ascii=False)
    fmap.get_root().html.add_child(
        folium.Element(f"<script>window.YW_CUBE_SESSION_POPUPS = {popup_data_json};</script>")
    )

    tower_layer.add_to(fmap)
    base_layer.add_to(fmap)
    bounds = [
        [float(frame["latitude"].min()), float(frame["longitude"].min())],
        [float(frame["latitude"].max()), float(frame["longitude"].max())],
    ]
    fmap.fit_bounds(bounds, padding=(38, 38))
    LayerControl(collapsed=False).add_to(fmap)

    SPACE_TIME_CUBE_HTML.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(SPACE_TIME_CUBE_HTML))
    return True


def write_report(
    nodes: pd.DataFrame,
    distance_matrix: pd.DataFrame,
    class_schedule: pd.DataFrame,
    transition_public: pd.DataFrame,
    location_transitions: pd.DataFrame,
    mobility_metrics: pd.DataFrame,
    transition_map_written: bool,
    time_slider_map_written: bool,
    cube_written: bool,
) -> None:
    non_self = distance_matrix[distance_matrix["is_same_location"].astype(str).str.lower().ne("true")].copy()
    non_self["walk_distance_m"] = pd.to_numeric(non_self["walk_distance_m"], errors="coerce")
    nearest = non_self.sort_values("walk_distance_m").head(8)
    farthest = non_self.sort_values("walk_distance_m", ascending=False).head(8)

    schedule_needs_review = class_schedule["schedule_needs_review"].astype(str).str.lower().eq("true").sum()
    parsed_count = class_schedule["schedule_parse_status"].eq("parsed").sum()
    if transition_public.empty:
        status_counts = pd.DataFrame(columns=["feasibility_status", "transition_count"])
        top_class_pairs = pd.DataFrame()
    else:
        status_counts = (
            transition_public.groupby(["feasibility_status", "feasibility_label"], dropna=False)["transition_count"]
            .apply(lambda series: pd.to_numeric(series, errors="coerce").fillna(0).sum())
            .reset_index()
            .sort_values("transition_count", ascending=False)
        )
        top_class_pairs = transition_public.copy()
        top_class_pairs["transition_count"] = pd.to_numeric(top_class_pairs["transition_count"], errors="coerce")
        top_class_pairs = top_class_pairs.sort_values("transition_count", ascending=False)

    top_location_pairs = location_transitions.copy()
    if not top_location_pairs.empty:
        top_location_pairs["transition_count"] = pd.to_numeric(top_location_pairs["transition_count"], errors="coerce")
        top_location_pairs = top_location_pairs.sort_values("transition_count", ascending=False)
    top_mobility_roles = mobility_metrics.copy()
    if not top_mobility_roles.empty:
        top_mobility_roles["transfer_hub_score"] = pd.to_numeric(top_mobility_roles["transfer_hub_score"], errors="coerce")
        top_mobility_roles = top_mobility_roles.sort_values("transfer_hub_score", ascending=False)

    report = f"""# GIS Deep Analysis Report

Generated: {date.today().isoformat()}

## Scope

This report extends the first GIS pass from static venue points into distance, schedule, and movement-feasibility analysis.
It does not use participant home addresses or real GPS traces. Movement means same-day possible transitions inferred from de-identified reservations and class times.

## Outputs

- Location nodes: `data/processed/analysis/public/location_nodes.csv`
- Distance matrix: `data/processed/analysis/public/location_distance_matrix.csv`
- Class schedule GIS: `data/processed/analysis/public/class_schedule_gis.csv`
- Public same-day transition feasibility: `data/processed/analysis/public/transition_feasibility_public.csv`
- Public same-day location transition feasibility: `data/processed/analysis/public/location_transition_feasibility_public.csv`
- Public location mobility role metrics: `data/processed/analysis/public/location_mobility_role_metrics.csv`
- Private participant itinerary: `data/processed/analysis/private/participant_itinerary_gis_private.csv`
- Time slider map: `reports/analysis/yeonhui_yoga_week_time_slider_map.html`
- Transition map: `reports/analysis/yeonhui_yoga_week_transition_map.html`
- Map-based space-time cube: `reports/analysis/yeonhui_yoga_week_space_time_cube.html`

## Data Summary

- Location nodes: {len(nodes)}
- Distance matrix rows: {len(distance_matrix)}
- Class schedule rows: {len(class_schedule)}
- Parsed class schedule rows: {int(parsed_count)}
- Class schedule rows needing review: {int(schedule_needs_review)}
- Public same-day class/session transition rows: {len(transition_public)}
- Public same-day location transition rows: {len(location_transitions)}
- Public location mobility role rows: {len(mobility_metrics)}
- Time slider map generated: {time_slider_map_written}
- Transition map generated: {transition_map_written}
- Map-based space-time cube generated: {cube_written}

## Feasibility Status Counts

{markdown_table(status_counts, ["feasibility_status", "feasibility_label", "transition_count"], rows=10)}

## Nearest Venue Pairs

{markdown_table(nearest, ["origin_display_name", "destination_display_name", "walk_distance_m", "walk_minutes", "walk_method"], rows=8)}

## Farthest Venue Pairs

{markdown_table(farthest, ["origin_display_name", "destination_display_name", "walk_distance_m", "walk_minutes", "walk_method"], rows=8)}

## Busiest Location Transition Candidates

{markdown_table(top_location_pairs, ["origin_display_name", "destination_display_name", "feasibility_label", "transition_count", "avg_gap_minutes", "avg_walk_minutes"], rows=12)}

## Location Mobility Roles

This table helps read which places behave like local movement hubs in the reservation timetable. It is not a ranking of venue quality. It counts how often a place appears in adjacent same-day booking flows.

{markdown_table(top_mobility_roles, ["display_name", "transfer_hub_score", "incoming_transition_count", "outgoing_transition_count", "same_location_transition_count", "comfortable_transition_count", "tight_transition_count"], rows=12)}

## Busiest Class Transition Candidates

{markdown_table(top_class_pairs, ["origin_class_title_base", "destination_class_title_base", "feasibility_label", "transition_count", "avg_gap_minutes", "avg_walk_minutes"], rows=12)}

## Interpretation Notes

- `comfortable` means the class gap is at least estimated walk time plus 10 minutes.
- `tight` means walking may be possible, but there is less than 10 minutes of buffer.
- `difficult` means the estimated walk time is longer than the available gap.
- `overlap` means the next class starts before the previous class ends.
- Public transition tables aggregate same-day adjacent reservations only, so multi-day reservation sequences do not distort movement interpretation.
- This is an operational planning layer for next-year scheduling, not a disclosure of individual participant movement.
- The space-time cube is now rendered on top of a Leaflet map. Venue position remains the x/y map coordinate, and each vertical tower uses height as the time axis.
"""
    write_text(GIS_DEEP_REPORT_MD, report)


def main() -> None:
    nodes = read_csv(LOCATION_NODES_CSV)
    distance_matrix = read_csv(LOCATION_DISTANCE_MATRIX_CSV)
    class_schedule = read_csv(CLASS_SCHEDULE_GIS_CSV)
    reviews = read_csv(OBUD_DEIDENTIFIED_PUBLIC)
    transition_public = read_csv(TRANSITION_FEASIBILITY_PUBLIC_CSV)
    location_transitions = read_csv(LOCATION_TRANSITION_FEASIBILITY_PUBLIC_CSV)
    mobility_metrics = build_location_mobility_metrics(nodes, location_transitions)
    write_csv(mobility_metrics, LOCATION_MOBILITY_ROLE_METRICS_CSV)

    transition_map_written = write_transition_map(nodes, location_transitions, mobility_metrics)
    time_slider_map_written = write_time_slider_map(class_schedule)
    cube_written = write_space_time_cube(class_schedule, reviews)
    write_report(
        nodes,
        distance_matrix,
        class_schedule,
        transition_public,
        location_transitions,
        mobility_metrics,
        transition_map_written,
        time_slider_map_written,
        cube_written,
    )

    print(f"Wrote {LOCATION_MOBILITY_ROLE_METRICS_CSV}")
    print(f"Wrote {GIS_DEEP_REPORT_MD}")
    if transition_map_written:
        print(f"Wrote {TRANSITION_MAP_HTML}")
    if time_slider_map_written:
        print(f"Wrote {TIME_SLIDER_MAP_HTML}")
    if cube_written:
        print(f"Wrote {SPACE_TIME_CUBE_HTML}")


if __name__ == "__main__":
    main()
