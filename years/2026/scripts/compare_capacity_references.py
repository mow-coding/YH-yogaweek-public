from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path
from typing import Callable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ANALYSIS_DIR = ROOT / "data" / "processed" / "analysis" / "public"
CALENDAR_PATH = PUBLIC_ANALYSIS_DIR / "onstudio_calendar_capacity_reference.csv"
DRIVE_PATH = PUBLIC_ANALYSIS_DIR / "google_drive_program_capacity_reference.csv"
OUTPUT_PATH = PUBLIC_ANALYSIS_DIR / "capacity_reference_comparison.csv"
REPORT_PATH = ROOT / "reports" / "onstudio" / "onstudio_calendar_capacity_comparison_report.md"


def load_similarity() -> Callable[[str, str], float]:
    try:
        from rapidfuzz import fuzz

        return lambda left, right: float(fuzz.token_set_ratio(left, right))
    except ImportError:
        from difflib import SequenceMatcher

        return lambda left, right: SequenceMatcher(None, left, right).ratio() * 100.0


similarity_score = load_similarity()


def normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^0-9a-z가-힣]+", " ", text)
    return " ".join(text.split())


def normalize_time(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = str(value).strip()
    match = re.match(r"^(\d{1,2}):(\d{2})", text)
    if not match:
        return text
    return f"{int(match.group(1)):02d}:{match.group(2)}"


def comparison_key(row: pd.Series, title_col: str) -> str:
    return normalize_text(
        " ".join(
            [
                str(row.get("location_text", "")),
                str(row.get(title_col, "")),
                str(row.get("instructor_text", "")),
                str(row.get("teacher_text", "")),
            ]
        )
    )


def best_drive_match(calendar_row: pd.Series, drive_candidates: pd.DataFrame) -> dict[str, object]:
    if drive_candidates.empty:
        return {
            "drive_source_cell": "",
            "drive_location_text": "",
            "drive_class_title_text": "",
            "drive_instructor_text": "",
            "drive_capacity": pd.NA,
            "match_score": 0.0,
            "match_status": "no_drive_candidate_same_time",
            "capacity_difference": pd.NA,
            "needs_review": True,
        }

    calendar_key = comparison_key(calendar_row, "class_title_text")
    candidates: list[tuple[float, pd.Series]] = []
    for _, candidate in drive_candidates.iterrows():
        drive_key = comparison_key(candidate, "class_title_text")
        candidates.append((similarity_score(calendar_key, drive_key), candidate))

    score, drive_row = max(candidates, key=lambda item: item[0])
    calendar_capacity = int(calendar_row["capacity"])
    drive_capacity_value = drive_row.get("capacity", pd.NA)
    drive_capacity = (
        int(drive_capacity_value)
        if not pd.isna(drive_capacity_value)
        else pd.NA
    )

    if score < 70:
        status = "low_confidence_match"
        needs_review = True
    elif pd.isna(drive_capacity):
        status = "matched_drive_capacity_missing"
        needs_review = True
    elif calendar_capacity == drive_capacity:
        status = "matched_same_capacity"
        needs_review = False
    else:
        status = "matched_capacity_mismatch"
        needs_review = True

    capacity_difference = (
        calendar_capacity - drive_capacity
        if not pd.isna(drive_capacity)
        else pd.NA
    )

    return {
        "drive_source_cell": drive_row.get("source_cell", ""),
        "drive_location_text": drive_row.get("location_text", ""),
        "drive_class_title_text": drive_row.get("class_title_text", ""),
        "drive_instructor_text": drive_row.get("instructor_text", ""),
        "drive_capacity": drive_capacity,
        "match_score": round(score, 2),
        "match_status": status,
        "capacity_difference": capacity_difference,
        "needs_review": needs_review,
    }


def markdown_table(df: pd.DataFrame, columns: list[str], limit: int = 12) -> str:
    if df.empty:
        return "_없음_"

    shown = df.loc[:, columns].head(limit).copy()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in shown.iterrows():
        values = [
            str(row.get(column, "")).replace("\n", " ").replace("|", "&#124;")
            for column in columns
        ]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def write_report(calendar: pd.DataFrame, drive: pd.DataFrame, comparison: pd.DataFrame) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    status_counts = comparison["match_status"].value_counts().rename_axis("status").reset_index(name="rows")
    mismatch_rows = comparison[comparison["match_status"] == "matched_capacity_mismatch"].copy()
    review_rows = comparison[comparison["needs_review"]].copy()

    fill_summary = (
        calendar.groupby("class_date", dropna=False)
        .agg(
            classes=("class_date", "size"),
            reserved_total=("reserved_count", "sum"),
            capacity_total=("capacity", "sum"),
        )
        .reset_index()
    )
    fill_summary["fill_rate"] = (
        fill_summary["reserved_total"] / fill_summary["capacity_total"]
    ).round(4)

    content = f"""# ON STUDIO 캘린더 정원표 대조 리포트

작성일: 2026-05-16

## 요약

- ON STUDIO 캘린더 원본: `data/raw/onstudio/calendar_capacity/onstudio_calendar_capacity_2026_yeonhui_yoga_week_2026-05-16.txt`
- ON STUDIO 캘린더 파생표: `data/processed/analysis/public/onstudio_calendar_capacity_reference.csv`
- Google Drive 기획 정원 파생표: `data/processed/analysis/public/google_drive_program_capacity_reference.csv`
- 대조표: `data/processed/analysis/public/capacity_reference_comparison.csv`
- 캘린더 추출 행 수: {len(calendar)}
- Google Drive 정원 후보 행 수: {len(drive)}
- 캘린더 기준 날짜 범위: {calendar['class_date'].min()} ~ {calendar['class_date'].max()}
- 수동 검토 필요 행 수: {int(comparison['needs_review'].sum())}

## 판정 기준

ON STUDIO 캘린더는 플랫폼 화면에서 복사한 `예약수|정원` 형식이므로, 1차 분석에서는 실제 운영 현황에 더 가까운 자료로 본다.
Google Drive 프로그램표는 기획/전달용 문서 성격이 있으므로, 정원 누락이나 변경 이력을 확인하는 대조 자료로 사용한다.

같은 날짜와 시작시간 안에서 장소명, 수업명, 강사명을 정규화한 뒤 fuzzy similarity를 계산했다.
점수 70점 이상은 같은 수업 후보로 보았고, 정원이 다르면 `matched_capacity_mismatch`로 표시했다.

## 대조 상태

{markdown_table(status_counts, ['status', 'rows'], limit=20)}

## 날짜별 캘린더 예약/정원 요약

{markdown_table(fill_summary, ['class_date', 'classes', 'reserved_total', 'capacity_total', 'fill_rate'], limit=30)}

## 정원 불일치 후보

{markdown_table(mismatch_rows, ['calendar_class_date', 'calendar_start_time', 'calendar_location_text', 'calendar_class_title_text', 'calendar_capacity', 'drive_capacity', 'capacity_difference', 'match_score'], limit=20)}

## 수동 검토 후보

{markdown_table(review_rows, ['calendar_class_date', 'calendar_start_time', 'calendar_location_text', 'calendar_class_title_text', 'match_status', 'match_score', 'calendar_capacity', 'drive_capacity'], limit=30)}

## 해석 메모

- ON STUDIO 캘린더 파생표의 `reserved_count`는 최종 결제자 수가 아니라 캘린더 화면에 표시된 예약 점유 수로 해석한다.
- 매출/정산 분석에는 기존 예약/취소 원장과 티켓 가격표를 우선 사용하고, 이 표는 정원 대비 채움률과 운영 포화도를 보는 보조축으로 사용한다.
- Google Drive 표와 다르게 나온 행은 오류라고 단정하지 않는다. 행사 준비 중 정원이나 장소/수업명이 바뀌었을 수 있기 때문이다.
"""

    REPORT_PATH.write_text(content, encoding="utf-8")


def main() -> None:
    if not CALENDAR_PATH.exists():
        raise FileNotFoundError(f"Missing calendar capacity CSV: {CALENDAR_PATH}")
    if not DRIVE_PATH.exists():
        raise FileNotFoundError(f"Missing Google Drive capacity CSV: {DRIVE_PATH}")

    calendar = pd.read_csv(CALENDAR_PATH)
    drive = pd.read_csv(DRIVE_PATH)
    calendar["start_time_normalized"] = calendar["start_time"].map(normalize_time)
    drive["start_time_normalized"] = drive["start_time"].map(normalize_time)

    records: list[dict[str, object]] = []
    for _, calendar_row in calendar.iterrows():
        candidates = drive[
            (drive["class_date"].astype(str) == str(calendar_row["class_date"]))
            & (drive["start_time_normalized"] == calendar_row["start_time_normalized"])
        ]
        match = best_drive_match(calendar_row, candidates)
        records.append(
            {
                "calendar_source_line": calendar_row["source_line"],
                "calendar_class_date": calendar_row["class_date"],
                "calendar_start_time": calendar_row["start_time"],
                "calendar_end_time": calendar_row["end_time"],
                "calendar_location_text": calendar_row["location_text"],
                "calendar_class_title_text": calendar_row["class_title_text"],
                "calendar_teacher_text": calendar_row.get("teacher_text", ""),
                "calendar_reserved_count": calendar_row["reserved_count"],
                "calendar_capacity": calendar_row["capacity"],
                "calendar_fill_rate": calendar_row["fill_rate"],
                **match,
            }
        )

    comparison = pd.DataFrame(records)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    write_report(calendar, drive, comparison)

    print(f"Wrote {OUTPUT_PATH}")
    print(f"Wrote {REPORT_PATH}")
    print(f"calendar_rows={len(calendar)}")
    print(f"drive_rows={len(drive)}")
    print(comparison["match_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
