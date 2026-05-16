from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_XLSX = (
    ROOT
    / "data"
    / "raw"
    / "google_drive_shared"
    / "rightnow_yogi"
    / "files"
    / "program_obud_delivery.xlsx"
)
OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "analysis"
    / "public"
    / "google_drive_program_capacity_reference.csv"
)

DATE_PATTERN = re.compile(r"2026\.\s*(\d{1,2})\.\s*(\d{1,2})")
TIME_PATTERN = re.compile(r"^\s*(\d{1,2}\s*[:;]\s*\d{2})(?:\s*[-~]\s*(\d{1,2}\s*[:;]\s*\d{2}))?")
LOCATION_PATTERN = re.compile(r"\[([^\]]+)\]")
CAPACITY_PATTERNS = [
    re.compile(r"정원\s*[:：\-]?\s*(\d{1,3})\s*명"),
    re.compile(r"\((?:정원\s*)?(\d{1,3})\s*명\)"),
    re.compile(r"(\d{1,3})\s*명\s*한정"),
]


def compact(value: object) -> str:
    return " ".join(("" if value is None else str(value)).replace("\r", "\n").split())


def clean_time(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", "", value).replace(";", ":")


def parse_date_label(label: str) -> str:
    match = DATE_PATTERN.search(label)
    if not match:
        return ""
    month = int(match.group(1))
    day = int(match.group(2))
    return f"2026-{month:02d}-{day:02d}"


def parse_capacity(raw_text: str) -> int | None:
    for pattern in CAPACITY_PATTERNS:
        match = pattern.search(raw_text)
        if match:
            return int(match.group(1))
    return None


def parse_entry(raw_text: str, date_label: str, sheet_name: str, row_idx: int, col_idx: int) -> dict[str, object]:
    lines = [line.strip() for line in str(raw_text).replace("\r", "\n").split("\n") if line.strip()]
    first_line = lines[0] if lines else ""

    time_match = TIME_PATTERN.search(first_line)
    start_time = clean_time(time_match.group(1)) if time_match else ""
    end_time = clean_time(time_match.group(2)) if time_match and time_match.group(2) else ""

    location_match = LOCATION_PATTERN.search(raw_text)
    location_text = compact(location_match.group(1)) if location_match else ""

    body_lines = lines[1:] if time_match else lines
    class_title = ""
    for line in body_lines:
        candidate = re.sub(r"^\[[^\]]+\]\s*", "", line).strip()
        if not candidate:
            continue
        if candidate.startswith("-") or "정원" in candidate:
            continue
        if DATE_PATTERN.search(candidate) or candidate.lower().startswith("week"):
            continue
        class_title = compact(candidate)
        break

    instructor_text = " / ".join(compact(line.lstrip("-")) for line in lines if line.startswith("-"))
    capacity = parse_capacity(raw_text)

    return {
        "source_file": "program_obud_delivery.xlsx",
        "source_sheet": sheet_name,
        "source_cell": f"R{row_idx + 1}C{col_idx + 1}",
        "date_label": compact(date_label),
        "class_date": parse_date_label(date_label),
        "start_time": start_time,
        "end_time": end_time,
        "location_text": location_text,
        "class_title_text": class_title,
        "instructor_text": instructor_text,
        "capacity": capacity if capacity is not None else "",
        "raw_entry": raw_text,
        "needs_review": not (start_time and class_title and capacity is not None),
    }


def should_skip_cell(raw_text: str) -> bool:
    text = compact(raw_text)
    if not text:
        return True
    if text.startswith("연희축제 프로그램") or text.lower().startswith("week"):
        return True
    if DATE_PATTERN.fullmatch(text.replace(" ", "")):
        return True
    return False


def build_capacity_reference() -> pd.DataFrame:
    if not SOURCE_XLSX.exists():
        raise FileNotFoundError(f"Source file not found: {SOURCE_XLSX}")

    workbook = pd.ExcelFile(SOURCE_XLSX)
    sheet_name = workbook.sheet_names[0]
    sheet = pd.read_excel(SOURCE_XLSX, sheet_name=sheet_name, header=None)

    date_by_col: dict[int, str] = {}
    rows: list[dict[str, object]] = []

    for row_idx, row in sheet.iterrows():
        values = row.to_dict()
        date_cells = {
            col_idx: str(value)
            for col_idx, value in values.items()
            if pd.notna(value) and DATE_PATTERN.search(str(value))
        }
        if date_cells:
            date_by_col.update(date_cells)
            continue

        for col_idx, value in values.items():
            if pd.isna(value):
                continue
            raw_text = str(value).strip()
            if should_skip_cell(raw_text):
                continue
            has_program_signal = bool(TIME_PATTERN.search(raw_text)) or parse_capacity(raw_text) is not None
            if not has_program_signal:
                continue
            date_label = date_by_col.get(col_idx, "")
            rows.append(parse_entry(raw_text, date_label, sheet_name, row_idx, col_idx))

    capacity = pd.DataFrame(rows)
    if not capacity.empty:
        capacity = capacity.sort_values(["class_date", "start_time", "source_cell"], na_position="last")
    return capacity


def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    capacity = build_capacity_reference()
    capacity.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"Wrote {len(capacity)} rows to {OUTPUT_CSV}")
    if not capacity.empty:
        missing_capacity = int((capacity["capacity"].astype(str).str.len() == 0).sum())
        needs_review = int(capacity["needs_review"].sum())
        print(f"missing_capacity_rows={missing_capacity}")
        print(f"needs_review_rows={needs_review}")


if __name__ == "__main__":
    main()
