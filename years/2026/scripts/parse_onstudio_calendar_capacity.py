from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = (
    ROOT
    / "data"
    / "raw"
    / "onstudio"
    / "calendar_capacity"
    / "onstudio_calendar_capacity_2026_yeonhui_yoga_week_2026-05-16.txt"
)
OUTPUT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "analysis"
    / "public"
    / "onstudio_calendar_capacity_reference.csv"
)

DAY_SUFFIX = chr(0xC77C)  # Korean "일"
DAY_RE = re.compile(rf"^(\d{{1,2}}){DAY_SUFFIX}$")
COUNT_RE = re.compile(r"^(\d+)\|(\d+)$")
CLASS_RE = re.compile(
    r"^(?P<start>\d{1,2}:\d{2})-(?P<end>\d{1,2}:\d{2})\s+"
    r"\[(?P<location>[^\]]+)\]\s*(?P<title>.+)$"
)
TEACHER_RE = re.compile(r"\((?P<teacher>[^()]*)\)\s*$")


@dataclass(frozen=True)
class CalendarCapacityRow:
    source_file: str
    source_line: int
    class_date: str
    day_number: int
    start_time: str
    end_time: str
    location_text: str
    class_title_text: str
    class_title_without_teacher: str
    teacher_text: str
    reserved_count: int
    capacity: int
    fill_rate: float | None
    raw_entry: str
    raw_count_text: str
    needs_review: bool


def normalize_spaces(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split())


def split_title_and_teacher(title: str) -> tuple[str, str]:
    title = normalize_spaces(title)
    match = TEACHER_RE.search(title)
    if not match:
        return title, ""

    teacher = normalize_spaces(match.group("teacher"))
    title_without_teacher = normalize_spaces(title[: match.start()])
    return title_without_teacher, teacher


def collect_raw_events(lines: list[str]) -> list[dict[str, object]]:
    current_day: int | None = None
    raw_events: list[dict[str, object]] = []

    for index, raw_line in enumerate(lines):
        line = normalize_spaces(raw_line)
        if not line:
            continue

        day_match = DAY_RE.fullmatch(line)
        if day_match:
            current_day = int(day_match.group(1))
            continue

        class_match = CLASS_RE.fullmatch(line)
        if not class_match or current_day is None:
            continue

        if index + 1 >= len(lines):
            continue

        count_text = normalize_spaces(lines[index + 1])
        count_match = COUNT_RE.fullmatch(count_text)
        if not count_match:
            continue

        raw_events.append(
            {
                "source_line": index + 1,
                "day_number": current_day,
                "start_time": class_match.group("start").zfill(5),
                "end_time": class_match.group("end").zfill(5),
                "location_text": normalize_spaces(class_match.group("location")),
                "class_title_text": normalize_spaces(class_match.group("title")),
                "reserved_count": int(count_match.group(1)),
                "capacity": int(count_match.group(2)),
                "raw_entry": line,
                "raw_count_text": count_text,
            }
        )

    return raw_events


def assign_2026_dates(raw_events: list[dict[str, object]]) -> list[CalendarCapacityRow]:
    rows: list[CalendarCapacityRow] = []
    current_month = 4
    previous_day: int | None = None

    for event in raw_events:
        day_number = int(event["day_number"])
        if previous_day is not None and day_number < previous_day:
            current_month += 1
        previous_day = day_number

        capacity = int(event["capacity"])
        reserved_count = int(event["reserved_count"])
        fill_rate = round(reserved_count / capacity, 4) if capacity > 0 else None
        title_without_teacher, teacher_text = split_title_and_teacher(
            str(event["class_title_text"])
        )

        needs_review = (
            current_month not in {4, 5}
            or capacity <= 0
            or reserved_count < 0
            or reserved_count > capacity
        )

        rows.append(
            CalendarCapacityRow(
                source_file=INPUT_PATH.name,
                source_line=int(event["source_line"]),
                class_date=f"2026-{current_month:02d}-{day_number:02d}",
                day_number=day_number,
                start_time=str(event["start_time"]),
                end_time=str(event["end_time"]),
                location_text=str(event["location_text"]),
                class_title_text=str(event["class_title_text"]),
                class_title_without_teacher=title_without_teacher,
                teacher_text=teacher_text,
                reserved_count=reserved_count,
                capacity=capacity,
                fill_rate=fill_rate,
                raw_entry=str(event["raw_entry"]),
                raw_count_text=str(event["raw_count_text"]),
                needs_review=needs_review,
            )
        )

    return rows


def write_rows(rows: list[CalendarCapacityRow]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_PATH}")

    lines = INPUT_PATH.read_text(encoding="utf-8").splitlines()
    raw_events = collect_raw_events(lines)
    if not raw_events:
        raise RuntimeError("No calendar capacity rows were parsed.")

    rows = assign_2026_dates(raw_events)
    write_rows(rows)

    needs_review = sum(row.needs_review for row in rows)
    print(f"Wrote {OUTPUT_PATH}")
    print(f"rows={len(rows)}")
    print(f"needs_review={needs_review}")


if __name__ == "__main__":
    main()
