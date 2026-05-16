from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from review_processing_utils import (
    ANALYSIS_PUBLIC_DIR,
    CLASS_HYPE_METRICS_PUBLIC,
    ONSTUDIO_CANCELLATIONS_PUBLIC,
    ONSTUDIO_CLASSES_PUBLIC,
    ONSTUDIO_RESERVATIONS_PUBLIC,
    canonical_class_key,
    compact_spaces,
    normalize_for_join,
    safe_int,
    studio_key_from_class_title,
    write_csv,
)


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_PRIVATE_DIR = ROOT / "data" / "processed" / "analysis" / "private"

CLASS_HYPE_GIS_CSV = ANALYSIS_PUBLIC_DIR / "class_hype_gis.csv"
LOCATION_NODES_CSV = ANALYSIS_PUBLIC_DIR / "location_nodes.csv"
LOCATION_DISTANCE_MATRIX_CSV = ANALYSIS_PUBLIC_DIR / "location_distance_matrix.csv"
CLASS_LOCATION_EVIDENCE_CSV = ANALYSIS_PUBLIC_DIR / "class_location_evidence_public.csv"
CLASS_SCHEDULE_GIS_CSV = ANALYSIS_PUBLIC_DIR / "class_schedule_gis.csv"
TRANSITION_FEASIBILITY_PUBLIC_CSV = ANALYSIS_PUBLIC_DIR / "transition_feasibility_public.csv"
LOCATION_TRANSITION_FEASIBILITY_PUBLIC_CSV = ANALYSIS_PUBLIC_DIR / "location_transition_feasibility_public.csv"
PARTICIPANT_ITINERARY_PRIVATE_CSV = ANALYSIS_PRIVATE_DIR / "participant_itinerary_gis_private.csv"
PARTICIPANT_TRANSITIONS_PRIVATE_CSV = ANALYSIS_PRIVATE_DIR / "participant_transition_gis_private.csv"

TIMEZONE = ZoneInfo("Asia/Seoul")
EVENT_YEAR = 2026
TRANSFER_BUFFER_MINUTES = 10
CLASS_DATETIME_RE = re.compile(
    r"(?P<month>\d{1,2})\.(?P<day>\d{1,2})\s*\((?P<weekday>[^)]+)\)\s*"
    r"(?P<start_hour>\d{1,2}):(?P<start_minute>\d{2})-(?P<end_hour>\d{1,2}):(?P<end_minute>\d{2})"
)
LOCATION_MARKERS = ["집합 장소", "집결 장소", "📍 장소", "장소:", "장소"]
LOCATION_SECTION_END_MARKERS = ["⏰", "🧘", "🚗", "❗", "준비물", "입장", "주차", "안내"]


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def base_title_if_available(title: str, known_titles: set[str]) -> str:
    match = re.search(r"\s+\([^)]{1,40}\)$", title)
    if not match:
        return title
    candidate = title[: match.start()].strip()
    return candidate if candidate in known_titles else title


def load_known_class_titles() -> set[str]:
    titles: set[str] = set()
    classes = pd.read_csv(ONSTUDIO_CLASSES_PUBLIC, dtype=str, keep_default_na=False)
    titles.update(item.strip() for item in classes["class_name"] if str(item).strip())
    for path in [ONSTUDIO_RESERVATIONS_PUBLIC, ONSTUDIO_CANCELLATIONS_PUBLIC]:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        titles.update(item.strip() for item in frame["class_info_text"] if str(item).strip())
    return titles


def parse_class_datetime(value: object) -> dict[str, object]:
    text = compact_spaces(value)
    match = CLASS_DATETIME_RE.search(text)
    if not match:
        return {
            "class_date": "",
            "weekday_text": "",
            "start_datetime": pd.NaT,
            "end_datetime": pd.NaT,
            "start_datetime_iso": "",
            "end_datetime_iso": "",
            "start_hour": "",
            "duration_minutes": "",
            "schedule_parse_status": "unparsed",
            "schedule_needs_review": True,
        }

    parts = {key: match.group(key) for key in match.groupdict()}
    start = datetime(
        EVENT_YEAR,
        int(parts["month"]),
        int(parts["day"]),
        int(parts["start_hour"]),
        int(parts["start_minute"]),
        tzinfo=TIMEZONE,
    )
    end = datetime(
        EVENT_YEAR,
        int(parts["month"]),
        int(parts["day"]),
        int(parts["end_hour"]),
        int(parts["end_minute"]),
        tzinfo=TIMEZONE,
    )
    if end <= start:
        end += timedelta(days=1)
    duration = int((end - start).total_seconds() / 60)
    return {
        "class_date": start.date().isoformat(),
        "weekday_text": parts["weekday"],
        "start_datetime": start,
        "end_datetime": end,
        "start_datetime_iso": start.isoformat(timespec="minutes"),
        "end_datetime_iso": end.isoformat(timespec="minutes"),
        "start_hour": start.hour,
        "duration_minutes": duration,
        "schedule_parse_status": "parsed",
        "schedule_needs_review": duration <= 0,
    }


def enrich_booking_rows(frame: pd.DataFrame, source_kind: str, known_titles: set[str]) -> pd.DataFrame:
    output = frame.copy()
    output["source_kind"] = source_kind
    output["class_title_standard"] = output["class_info_text"].map(compact_spaces)
    output["class_title_base"] = output["class_title_standard"].map(
        lambda title: base_title_if_available(title, known_titles)
    )
    output["class_base_key"] = output["class_title_base"].map(canonical_class_key)
    output["source_studio_key"] = output["class_title_base"].map(studio_key_from_class_title)
    output["people_count"] = output["people_count_text"].map(safe_int).fillna(1).astype(int)

    parsed = output["class_datetime_text"].map(parse_class_datetime).apply(pd.Series)
    output = pd.concat([output, parsed], axis=1)
    output["class_session_key"] = [
        f"{class_key}_{start.strftime('%Y%m%dT%H%M')}" if pd.notna(start) else f"{class_key}_unparsed"
        for class_key, start in zip(output["class_base_key"], output["start_datetime"], strict=False)
    ]
    return output


def load_class_metrics() -> pd.DataFrame:
    metrics = pd.read_csv(CLASS_HYPE_GIS_CSV, dtype=str, keep_default_na=False)
    if "studio_key_x" in metrics.columns:
        metrics["metric_studio_key"] = metrics["studio_key_x"]
    elif "studio_key" in metrics.columns:
        metrics["metric_studio_key"] = metrics["studio_key"]
    else:
        metrics["metric_studio_key"] = ""

    columns = [
        "class_base_key",
        "metric_studio_key",
        "normalized_studio_key",
        "display_name",
        "address",
        "latitude",
        "longitude",
        "needs_manual_verification",
        "reservation_count",
        "cancellation_count",
        "net_reservation_count",
        "review_count",
        "reservation_hype",
        "review_hype",
        "satisfaction_hype",
        "operations_stability",
    ]
    return metrics[[column for column in columns if column in metrics.columns]].drop_duplicates("class_base_key")


def normalize_location_match_text(value: object) -> str:
    text = normalize_for_join(value)
    for token in ["특별시", "광역시", "서울시"]:
        text = text.replace(token, "")
    return text


def compact_location_section(value: object) -> str:
    text = re.sub(r"\s+", " ", "" if value is None else str(value).replace("\n", " ")).strip()
    if not text:
        return ""
    marker_positions = [text.find(marker) for marker in LOCATION_MARKERS if text.find(marker) >= 0]
    if not marker_positions:
        return ""
    start = min(marker_positions)
    end = len(text)
    for marker in LOCATION_SECTION_END_MARKERS:
        position = text.find(marker, start + 1)
        if position >= 0:
            end = min(end, position)
    return text[start:end].strip(" \t\r\n-:：")


def movement_type_from_text(class_title: str, evidence: str) -> str:
    combined = f"{class_title} {evidence}"
    if any(keyword in combined for keyword in ["러닝", "트레킹", "산책"]):
        return "mobile_outdoor"
    if any(keyword in combined for keyword in ["랜드마크", "커뮤니티허브", "옥상", "루프탑"]):
        return "special_venue"
    if any(keyword in combined for keyword in ["야외", "궁동산", "궁둥산"]):
        return "outdoor_static"
    return "studio_or_indoor"


def location_candidate_texts(row: pd.Series) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for label, column in [
        ("location_key", "location_key"),
        ("display_name", "display_name"),
        ("address", "address"),
    ]:
        value = str(row.get(column) or "").strip()
        if value:
            values.append((label, value))

    address = str(row.get("address") or "")
    address_without_seoul = re.sub(r"서울(특별시|시)?\s*(서대문구|마포구)\s*", "", address).strip()
    if address_without_seoul:
        values.append(("address_without_city", address_without_seoul))

    geocoded = str(row.get("geocoded_address") or "").strip()
    if geocoded and geocoded != address:
        values.append(("geocoded_address", geocoded))
    return values


def match_location_from_evidence(evidence: str, source_key: str, location_nodes: pd.DataFrame) -> dict[str, object]:
    evidence_norm = normalize_location_match_text(evidence)
    if not evidence_norm:
        return {
            "actual_location_key": source_key,
            "location_evidence_status": "no_location_section",
            "location_evidence_match_type": "fallback_source_studio",
            "location_match_score_hint": "",
        }

    best: dict[str, object] | None = None
    for _, node in location_nodes.iterrows():
        location_key = str(node.get("location_key") or "")
        for candidate_type, candidate in location_candidate_texts(node):
            candidate_norm = normalize_location_match_text(candidate)
            if len(candidate_norm) < 3:
                continue
            if candidate_norm in evidence_norm or evidence_norm in candidate_norm:
                if candidate_type in {"address", "address_without_city", "geocoded_address"}:
                    score = 100
                elif candidate_type in {"display_name", "location_key"}:
                    score = 85
                else:
                    score = 70
                if best is None or score > int(best["location_match_score_hint"]):
                    best = {
                        "actual_location_key": location_key,
                        "location_evidence_status": "matched_from_class_detail",
                        "location_evidence_match_type": candidate_type,
                        "location_match_score_hint": score,
                    }

    if best:
        return best
    return {
        "actual_location_key": source_key,
        "location_evidence_status": "unmatched_location_section",
        "location_evidence_match_type": "fallback_source_studio",
        "location_match_score_hint": "",
    }


def build_class_location_evidence(
    location_nodes: pd.DataFrame,
    active_class_base_keys: set[str] | None = None,
) -> pd.DataFrame:
    classes = pd.read_csv(ONSTUDIO_CLASSES_PUBLIC, dtype=str, keep_default_na=False)
    rows: list[dict[str, object]] = []
    for _, row in classes.iterrows():
        class_title = compact_spaces(row.get("class_name"))
        if not class_title:
            continue
        class_base_key = canonical_class_key(class_title)
        if active_class_base_keys is not None and class_base_key not in active_class_base_keys:
            continue
        source_studio_key = studio_key_from_class_title(class_title)
        evidence = compact_location_section(row.get("description_raw"))
        movement_type = movement_type_from_text(class_title, evidence)
        match = match_location_from_evidence(evidence, source_studio_key, location_nodes)
        rows.append(
            {
                "class_base_key": class_base_key,
                "class_title_base": class_title,
                "organizer_studio_key": source_studio_key,
                "actual_location_key": match["actual_location_key"],
                "movement_type": movement_type,
                "location_evidence_text": evidence,
                "location_evidence_status": match["location_evidence_status"],
                "location_evidence_match_type": match["location_evidence_match_type"],
                "location_match_score_hint": match["location_match_score_hint"],
            }
        )

    evidence = pd.DataFrame(rows)
    if evidence.empty:
        return evidence

    priority = {
        "matched_from_class_detail": 0,
        "unmatched_location_section": 1,
        "no_location_section": 2,
    }
    evidence["_status_rank"] = evidence["location_evidence_status"].map(priority).fillna(9)
    evidence["_evidence_length"] = evidence["location_evidence_text"].astype(str).str.len()
    evidence = evidence.sort_values(
        ["class_base_key", "_status_rank", "_evidence_length"],
        ascending=[True, True, False],
    )
    evidence = evidence.drop_duplicates("class_base_key").drop(columns=["_status_rank", "_evidence_length"])
    return evidence.reset_index(drop=True)


def add_missing_active_location_evidence(
    evidence: pd.DataFrame,
    active_rows: pd.DataFrame,
) -> pd.DataFrame:
    existing = set(evidence["class_base_key"]) if not evidence.empty else set()
    fallback_rows: list[dict[str, object]] = []
    active_unique = active_rows.drop_duplicates("class_base_key")
    for _, row in active_unique.iterrows():
        class_base_key = str(row.get("class_base_key") or "")
        if not class_base_key or class_base_key in existing:
            continue
        source_studio_key = str(row.get("source_studio_key") or "")
        fallback_rows.append(
            {
                "class_base_key": class_base_key,
                "class_title_base": row.get("class_title_base", ""),
                "organizer_studio_key": source_studio_key,
                "actual_location_key": source_studio_key,
                "movement_type": movement_type_from_text(str(row.get("class_title_base") or ""), ""),
                "location_evidence_text": "",
                "location_evidence_status": "fallback_to_title_location",
                "location_evidence_match_type": "fallback_source_studio",
                "location_match_score_hint": "",
            }
        )
    if not fallback_rows:
        return evidence
    return pd.concat([evidence, pd.DataFrame(fallback_rows)], ignore_index=True).sort_values(
        ["class_base_key", "class_title_base"]
    )


def fill_missing_locations(enriched: pd.DataFrame, location_nodes: pd.DataFrame) -> pd.DataFrame:
    output = enriched.copy()
    node_lookup = (
        location_nodes.rename(
            columns={
                "location_key": "fallback_location_key",
                "display_name": "fallback_display_name",
                "address": "fallback_address",
                "latitude": "fallback_latitude",
                "longitude": "fallback_longitude",
                "needs_manual_verification": "fallback_needs_manual_verification",
            }
        )
        .drop_duplicates("fallback_location_key")
        .copy()
    )
    output = output.merge(
        node_lookup[
            [
                "fallback_location_key",
                "fallback_display_name",
                "fallback_address",
                "fallback_latitude",
                "fallback_longitude",
                "fallback_needs_manual_verification",
            ]
        ],
        left_on="source_studio_key",
        right_on="fallback_location_key",
        how="left",
    )
    for target, fallback in [
        ("normalized_studio_key", "fallback_location_key"),
        ("display_name", "fallback_display_name"),
        ("address", "fallback_address"),
        ("latitude", "fallback_latitude"),
        ("longitude", "fallback_longitude"),
        ("needs_manual_verification", "fallback_needs_manual_verification"),
    ]:
        if target not in output.columns:
            output[target] = ""
        output[target] = output[target].where(output[target].astype(str).str.strip().ne(""), output[fallback])
    output["location_match_status"] = output["normalized_studio_key"].fillna("").astype(str).map(
        lambda value: "matched" if value.strip() else "missing_location"
    )
    output["schedule_needs_review"] = output["schedule_needs_review"].astype(bool) | output[
        "location_match_status"
    ].ne("matched")
    fallback_columns = [column for column in output.columns if column.startswith("fallback_")]
    return output.drop(columns=fallback_columns)


def apply_class_location_evidence(
    enriched: pd.DataFrame,
    class_location_evidence: pd.DataFrame,
    location_nodes: pd.DataFrame,
) -> pd.DataFrame:
    output = enriched.copy()
    output["organizer_studio_key"] = output["source_studio_key"]

    evidence_columns = [
        "class_base_key",
        "actual_location_key",
        "movement_type",
        "location_evidence_text",
        "location_evidence_status",
        "location_evidence_match_type",
        "location_match_score_hint",
    ]
    available_evidence_columns = [
        column for column in evidence_columns if column in class_location_evidence.columns
    ]
    if available_evidence_columns:
        output = output.merge(
            class_location_evidence[available_evidence_columns].drop_duplicates("class_base_key"),
            on="class_base_key",
            how="left",
        )
    else:
        for column in evidence_columns:
            if column != "class_base_key":
                output[column] = ""

    for column in [
        "actual_location_key",
        "movement_type",
        "location_evidence_text",
        "location_evidence_status",
        "location_evidence_match_type",
        "location_match_score_hint",
    ]:
        if column not in output.columns:
            output[column] = ""
        output[column] = output[column].fillna("").astype(object)

    output["actual_location_key"] = output["actual_location_key"].where(
        output["actual_location_key"].astype(str).str.strip().ne(""),
        output["normalized_studio_key"],
    )
    output["movement_type"] = output.apply(
        lambda row: row["movement_type"]
        if str(row["movement_type"]).strip()
        else movement_type_from_text(str(row.get("class_title_base") or ""), str(row.get("location_evidence_text") or "")),
        axis=1,
    )
    output["location_evidence_status"] = output["location_evidence_status"].where(
        output["location_evidence_status"].astype(str).str.strip().ne(""),
        "fallback_to_title_location",
    )
    output["location_evidence_match_type"] = output["location_evidence_match_type"].where(
        output["location_evidence_match_type"].astype(str).str.strip().ne(""),
        "fallback_source_studio",
    )

    actual_nodes = location_nodes.rename(
        columns={
            "location_key": "actual_location_key",
            "display_name": "actual_location_display_name",
            "address": "actual_location_address",
            "latitude": "actual_location_latitude",
            "longitude": "actual_location_longitude",
            "needs_manual_verification": "actual_location_needs_manual_verification",
        }
    )
    output = output.merge(
        actual_nodes[
            [
                "actual_location_key",
                "actual_location_display_name",
                "actual_location_address",
                "actual_location_latitude",
                "actual_location_longitude",
                "actual_location_needs_manual_verification",
            ]
        ].drop_duplicates("actual_location_key"),
        on="actual_location_key",
        how="left",
    )

    for column in [
        "actual_location_display_name",
        "actual_location_address",
        "actual_location_latitude",
        "actual_location_longitude",
        "actual_location_needs_manual_verification",
    ]:
        output[column] = output[column].fillna("")
    has_actual_node = output["actual_location_display_name"].astype(str).str.strip().ne("")
    output["normalized_studio_key"] = output["actual_location_key"].where(has_actual_node, output["normalized_studio_key"])
    output["display_name"] = output["actual_location_display_name"].where(has_actual_node, output["display_name"])
    output["address"] = output["actual_location_address"].where(has_actual_node, output["address"])
    output["latitude"] = output["actual_location_latitude"].where(has_actual_node, output["latitude"])
    output["longitude"] = output["actual_location_longitude"].where(has_actual_node, output["longitude"])
    output["needs_manual_verification"] = output["actual_location_needs_manual_verification"].where(
        has_actual_node,
        output["needs_manual_verification"],
    )
    output["location_from_class_detail"] = output["location_evidence_status"].eq("matched_from_class_detail")
    output["location_match_status"] = output["location_match_status"].where(has_actual_node, "missing_actual_location")
    output["schedule_needs_review"] = (
        output["schedule_needs_review"].astype(bool)
        | output["location_match_status"].ne("matched")
        | output["location_evidence_status"].eq("unmatched_location_section")
        | output["actual_location_key"].astype(str).str.contains("궁둥산|궁동산", regex=True, na=False)
    )
    return output


def build_class_schedule(enriched_rows: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["class_session_key"]
    aggregations = {
        "class_base_key": "first",
        "class_title_base": "first",
        "class_datetime_text": "first",
        "class_date": "first",
        "weekday_text": "first",
        "start_datetime_iso": "first",
        "end_datetime_iso": "first",
        "start_hour": "first",
        "duration_minutes": "first",
        "schedule_parse_status": "first",
        "schedule_needs_review": "max",
        "organizer_studio_key": "first",
        "actual_location_key": "first",
        "actual_location_display_name": "first",
        "actual_location_address": "first",
        "normalized_studio_key": "first",
        "display_name": "first",
        "address": "first",
        "latitude": "first",
        "longitude": "first",
        "needs_manual_verification": "first",
        "location_match_status": "first",
        "location_from_class_detail": "first",
        "movement_type": "first",
        "location_evidence_text": "first",
        "location_evidence_status": "first",
        "location_evidence_match_type": "first",
        "reservation_count": "first",
        "cancellation_count": "first",
        "net_reservation_count": "first",
        "review_count": "first",
        "reservation_hype": "first",
        "review_hype": "first",
        "satisfaction_hype": "first",
        "operations_stability": "first",
    }
    schedule = enriched_rows.groupby(group_columns, dropna=False).agg(aggregations).reset_index()
    active_counts = (
        enriched_rows[enriched_rows["source_kind"].eq("reservation")]
        .groupby("class_session_key")
        .agg(
            active_reservation_rows=("class_session_key", "size"),
            active_people_count=("people_count", "sum"),
            unique_participant_count=("reserver_name", "nunique"),
        )
        .reset_index()
    )
    cancel_counts = (
        enriched_rows[enriched_rows["source_kind"].eq("cancellation")]
        .groupby("class_session_key")
        .agg(cancellation_rows=("class_session_key", "size"), cancelled_people_count=("people_count", "sum"))
        .reset_index()
    )
    schedule = schedule.merge(active_counts, on="class_session_key", how="left")
    schedule = schedule.merge(cancel_counts, on="class_session_key", how="left")
    for column in ["active_reservation_rows", "active_people_count", "unique_participant_count", "cancellation_rows", "cancelled_people_count"]:
        schedule[column] = pd.to_numeric(schedule[column], errors="coerce").fillna(0).astype(int)
    return schedule.sort_values(["start_datetime_iso", "display_name", "class_title_base"])


def build_participant_itinerary(reservations: pd.DataFrame) -> pd.DataFrame:
    itinerary = reservations.copy()
    itinerary = itinerary.sort_values(["reserver_name", "start_datetime", "end_datetime", "class_title_base"])
    itinerary["itinerary_order"] = itinerary.groupby("reserver_name").cumcount() + 1
    columns = [
        "reserver_name",
        "itinerary_order",
        "class_session_key",
        "class_base_key",
        "class_title_base",
        "class_datetime_text",
        "class_date",
        "start_datetime_iso",
        "end_datetime_iso",
        "organizer_studio_key",
        "actual_location_key",
        "actual_location_display_name",
        "actual_location_address",
        "normalized_studio_key",
        "display_name",
        "latitude",
        "longitude",
        "movement_type",
        "location_from_class_detail",
        "location_evidence_status",
        "booking_method_text",
        "people_count",
        "schedule_parse_status",
        "schedule_needs_review",
        "location_match_status",
    ]
    itinerary = itinerary[[column for column in columns if column in itinerary.columns]]
    return itinerary.rename(columns={"reserver_name": "participant_public_id"})


def feasibility_status(gap_minutes: float | None, travel_minutes: float | None) -> tuple[str, str]:
    if gap_minutes is None or travel_minutes is None:
        return "unknown", "판정 불가"
    if gap_minutes < 0:
        return "overlap", "시간 겹침"
    if gap_minutes >= travel_minutes + TRANSFER_BUFFER_MINUTES:
        return "comfortable", "여유 있음"
    if gap_minutes >= travel_minutes:
        return "tight", "빠듯함"
    return "difficult", "시간표상 어려움"


def build_transitions(itinerary: pd.DataFrame, distance_matrix: pd.DataFrame) -> pd.DataFrame:
    distance_lookup = {
        (str(row["origin_location_key"]), str(row["destination_location_key"])): row
        for _, row in distance_matrix.iterrows()
    }
    rows: list[dict[str, object]] = []
    itinerary = itinerary.copy()
    itinerary["start_datetime"] = pd.to_datetime(itinerary["start_datetime_iso"], errors="coerce")
    itinerary["end_datetime"] = pd.to_datetime(itinerary["end_datetime_iso"], errors="coerce")

    for participant_id, group in itinerary.groupby("participant_public_id", dropna=False):
        group = group.sort_values(["start_datetime", "end_datetime", "class_title_base"])
        if len(group) < 2:
            continue
        records = list(group.to_dict("records"))
        for index in range(len(records) - 1):
            origin = records[index]
            destination = records[index + 1]
            origin_key = str(origin.get("actual_location_key") or origin.get("normalized_studio_key") or "")
            destination_key = str(
                destination.get("actual_location_key") or destination.get("normalized_studio_key") or ""
            )
            distance_row = distance_lookup.get((origin_key, destination_key))
            travel_minutes = (
                float(distance_row["walk_minutes"]) if distance_row is not None and str(distance_row["walk_minutes"]) else None
            )
            if pd.notna(origin.get("end_datetime")) and pd.notna(destination.get("start_datetime")):
                gap_minutes = round(
                    (destination["start_datetime"] - origin["end_datetime"]).total_seconds() / 60,
                    2,
                )
            else:
                gap_minutes = None
            status, label = feasibility_status(gap_minutes, travel_minutes)
            origin_class_date = str(origin.get("class_date") or "")
            destination_class_date = str(destination.get("class_date") or "")
            same_class_date = bool(origin_class_date and origin_class_date == destination_class_date)
            if not origin_class_date or not destination_class_date:
                transition_scope = "unknown_date"
            elif same_class_date:
                transition_scope = "same_day"
            else:
                transition_scope = "cross_day"
            rows.append(
                {
                    "participant_public_id": participant_id,
                    "transition_order": index + 1,
                    "origin_session_key": origin.get("class_session_key", ""),
                    "origin_class_base_key": origin.get("class_base_key", ""),
                    "origin_class_title_base": origin.get("class_title_base", ""),
                    "origin_class_date": origin_class_date,
                    "origin_start_datetime_iso": origin.get("start_datetime_iso", ""),
                    "origin_end_datetime_iso": origin.get("end_datetime_iso", ""),
                    "origin_location_key": origin_key,
                    "origin_display_name": origin.get("actual_location_display_name")
                    or origin.get("display_name", ""),
                    "destination_session_key": destination.get("class_session_key", ""),
                    "destination_class_base_key": destination.get("class_base_key", ""),
                    "destination_class_title_base": destination.get("class_title_base", ""),
                    "destination_class_date": destination_class_date,
                    "destination_start_datetime_iso": destination.get("start_datetime_iso", ""),
                    "destination_end_datetime_iso": destination.get("end_datetime_iso", ""),
                    "destination_location_key": destination_key,
                    "destination_display_name": destination.get("actual_location_display_name")
                    or destination.get("display_name", ""),
                    "gap_minutes": gap_minutes,
                    "walk_minutes": travel_minutes,
                    "walk_distance_m": float(distance_row["walk_distance_m"]) if distance_row is not None else None,
                    "walk_method": distance_row["walk_method"] if distance_row is not None else "",
                    "transfer_buffer_minutes": TRANSFER_BUFFER_MINUTES,
                    "feasibility_status": status,
                    "feasibility_label": label,
                    "same_location": origin_key == destination_key,
                    "same_class_date": same_class_date,
                    "transition_scope": transition_scope,
                }
            )
    return pd.DataFrame(rows)


def aggregate_transitions(transitions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if transitions.empty:
        return pd.DataFrame(), pd.DataFrame()

    transitions = transitions[transitions["transition_scope"].eq("same_day")].copy()
    if transitions.empty:
        return pd.DataFrame(), pd.DataFrame()

    class_group_columns = [
        "origin_session_key",
        "origin_class_base_key",
        "origin_class_title_base",
        "origin_start_datetime_iso",
        "origin_location_key",
        "origin_display_name",
        "destination_session_key",
        "destination_class_base_key",
        "destination_class_title_base",
        "destination_start_datetime_iso",
        "destination_location_key",
        "destination_display_name",
        "feasibility_status",
        "feasibility_label",
        "walk_method",
        "same_location",
    ]
    location_group_columns = [
        "origin_location_key",
        "origin_display_name",
        "destination_location_key",
        "destination_display_name",
        "feasibility_status",
        "feasibility_label",
        "walk_method",
        "same_location",
    ]

    def aggregate(group_columns: list[str]) -> pd.DataFrame:
        frame = (
            transitions.groupby(group_columns, dropna=False)
            .agg(
                transition_count=("participant_public_id", "size"),
                avg_gap_minutes=("gap_minutes", "mean"),
                min_gap_minutes=("gap_minutes", "min"),
                max_gap_minutes=("gap_minutes", "max"),
                avg_walk_minutes=("walk_minutes", "mean"),
                avg_walk_distance_m=("walk_distance_m", "mean"),
            )
            .reset_index()
        )
        for column in [
            "avg_gap_minutes",
            "min_gap_minutes",
            "max_gap_minutes",
            "avg_walk_minutes",
            "avg_walk_distance_m",
        ]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").round(2)
        return frame.sort_values("transition_count", ascending=False)

    return aggregate(class_group_columns), aggregate(location_group_columns)


def main() -> None:
    required = [CLASS_HYPE_GIS_CSV, LOCATION_NODES_CSV, LOCATION_DISTANCE_MATRIX_CSV]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(f"Missing input: {path}")

    known_titles = load_known_class_titles()
    reservations = pd.read_csv(ONSTUDIO_RESERVATIONS_PUBLIC, dtype=str, keep_default_na=False)
    cancellations = pd.read_csv(ONSTUDIO_CANCELLATIONS_PUBLIC, dtype=str, keep_default_na=False)
    location_nodes = pd.read_csv(LOCATION_NODES_CSV, dtype=str, keep_default_na=False)
    distance_matrix = pd.read_csv(LOCATION_DISTANCE_MATRIX_CSV, dtype=str, keep_default_na=False)
    class_metrics = load_class_metrics()

    reservation_rows = enrich_booking_rows(reservations, "reservation", known_titles)
    cancellation_rows = enrich_booking_rows(cancellations, "cancellation", known_titles)
    active_class_base_keys = set(reservation_rows["class_base_key"]) | set(cancellation_rows["class_base_key"])
    class_location_evidence = build_class_location_evidence(location_nodes, active_class_base_keys)
    class_location_evidence = add_missing_active_location_evidence(
        class_location_evidence,
        pd.concat([reservation_rows, cancellation_rows], ignore_index=True),
    )
    enriched = pd.concat([reservation_rows, cancellation_rows], ignore_index=True)
    enriched = enriched.merge(class_metrics, on="class_base_key", how="left")
    enriched = fill_missing_locations(enriched, location_nodes)
    enriched = apply_class_location_evidence(enriched, class_location_evidence, location_nodes)

    class_schedule = build_class_schedule(enriched)
    participant_itinerary = build_participant_itinerary(enriched[enriched["source_kind"].eq("reservation")])
    participant_transitions = build_transitions(participant_itinerary, distance_matrix)
    transition_public, location_transition_public = aggregate_transitions(participant_transitions)

    write_csv(class_location_evidence, CLASS_LOCATION_EVIDENCE_CSV)
    write_csv(class_schedule, CLASS_SCHEDULE_GIS_CSV)
    write_csv(transition_public, TRANSITION_FEASIBILITY_PUBLIC_CSV)
    write_csv(location_transition_public, LOCATION_TRANSITION_FEASIBILITY_PUBLIC_CSV)
    write_csv(participant_itinerary, PARTICIPANT_ITINERARY_PRIVATE_CSV)
    write_csv(participant_transitions, PARTICIPANT_TRANSITIONS_PRIVATE_CSV)

    print(f"Wrote {CLASS_LOCATION_EVIDENCE_CSV}")
    print(f"Wrote {CLASS_SCHEDULE_GIS_CSV}")
    print(f"Wrote {TRANSITION_FEASIBILITY_PUBLIC_CSV}")
    print(f"Wrote {LOCATION_TRANSITION_FEASIBILITY_PUBLIC_CSV}")
    print(f"Wrote {PARTICIPANT_ITINERARY_PRIVATE_CSV}")
    print(f"Wrote {PARTICIPANT_TRANSITIONS_PRIVATE_CSV}")
    print(f"Class schedule rows: {len(class_schedule)}")
    print(f"Private itinerary rows: {len(participant_itinerary)}")
    print(f"Private transition rows: {len(participant_transitions)}")


if __name__ == "__main__":
    main()
