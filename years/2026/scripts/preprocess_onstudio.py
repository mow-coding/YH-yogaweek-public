from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw" / "onstudio"
PUBLIC_OUTPUT_DIR = ROOT / "data" / "processed" / "onstudio" / "public"
PRIVATE_OUTPUT_DIR = ROOT / "data" / "processed" / "onstudio" / "private"
REPORT_DIR = ROOT / "reports" / "onstudio"

EXPECTED_CLASS_ROWS = 125
EXPECTED_TEACHER_ROWS = 47
EXPECTED_RESERVATION_ROWS = 1611
EXPECTED_CANCEL_ROWS = 1048


PHONE_RE = re.compile(r"^\d{2,3}-\d{3,4}-\d{4}$")
PAGE_RE = re.compile(r"^(\d+)p\.txt$")
TEACHER_DETAIL_RE = re.compile(
    r"^(?P<phone>\d{2,3}-\d{3,4}-\d{4}|-)\t(?P<role>오너|매니저|강사)\t(?P<registered_date>\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.?)\s*$"
)


@dataclass(frozen=True)
class PageFile:
    path: Path
    page: int


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").splitlines()


def page_files(folder: Path) -> list[PageFile]:
    files: list[PageFile] = []
    for path in folder.glob("*.txt"):
        match = PAGE_RE.match(path.name)
        if match:
            files.append(PageFile(path=path, page=int(match.group(1))))
    return sorted(files, key=lambda item: item.page)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_request_cancel_line(line: str) -> tuple[str, str, str]:
    parts = line.split("\t")
    request_text = parts[0] if len(parts) >= 1 else ""
    cancel_text = parts[1] if len(parts) >= 2 else ""
    extra_text = "\t".join(parts[2:]) if len(parts) >= 3 else ""
    return request_text, cancel_text, extra_text


def parse_people_booking_line(line: str) -> tuple[str, str, str]:
    parts = line.split("\t")
    people_text = parts[0] if len(parts) >= 1 else ""
    booking_method_text = parts[1] if len(parts) >= 2 else ""
    extra_text = "\t".join(parts[2:]) if len(parts) >= 3 else ""
    return people_text, booking_method_text, extra_text


def parse_booking_folder(
    folder_name: str,
    status: str,
    source_dataset: str,
) -> tuple[list[dict[str, object]], list[str]]:
    folder = RAW_ROOT / folder_name
    rows: list[dict[str, object]] = []
    warnings: list[str] = []

    for page_file in page_files(folder):
        lines = read_lines(page_file.path)
        row_index = 0

        for index, line in enumerate(lines):
            if not PHONE_RE.match(line.strip()):
                continue

            if index < 4 or index + 1 >= len(lines):
                warnings.append(
                    f"{folder_name}/{page_file.path.name}: line {index + 1} looked like a phone number but did not have the expected surrounding lines."
                )
                continue

            raw_lines = lines[index - 4 : index + 2]
            request_cancel_line = raw_lines[0]
            class_datetime_text = raw_lines[1]
            class_info_text = raw_lines[2]
            reserver_name = raw_lines[3]
            phone = raw_lines[4].strip()
            people_booking_line = raw_lines[5]

            request_text, cancel_text, request_cancel_extra = parse_request_cancel_line(request_cancel_line)
            people_text, booking_method_text, people_booking_extra = parse_people_booking_line(people_booking_line)

            row_index += 1
            rows.append(
                {
                    "source_dataset": source_dataset,
                    "status": status,
                    "status_source": f"folder:{folder_name}",
                    "source_file": page_file.path.name,
                    "source_page": page_file.page,
                    "source_row_index": row_index,
                    "source_line_start": index - 3,
                    "source_line_end": index + 2,
                    "request_datetime_text": request_text,
                    "cancel_datetime_text": cancel_text,
                    "request_cancel_line_extra_text": request_cancel_extra,
                    "request_cancel_line_raw": request_cancel_line,
                    "class_datetime_text": class_datetime_text,
                    "class_info_text": class_info_text,
                    "reserver_name": reserver_name,
                    "phone": phone,
                    "people_count_text": people_text,
                    "booking_method_text": booking_method_text,
                    "people_booking_line_extra_text": people_booking_extra,
                    "people_booking_line_raw": people_booking_line,
                    "raw_record_text": "\n".join(raw_lines),
                }
            )

    return rows, warnings


def is_class_record_start(line: str) -> bool:
    return line.startswith("[") or line.startswith("요가\t")


def parse_class_record(
    page_file: PageFile,
    row_index: int,
    raw_lines: list[str],
    line_start: int,
    line_end: int,
) -> dict[str, object]:
    first_line = raw_lines[0] if raw_lines else ""
    if "\t" in first_line:
        class_name, first_description_part = first_line.split("\t", 1)
    else:
        class_name = first_line
        first_description_part = ""

    description_parts: list[str] = [first_description_part]
    if len(raw_lines) > 1:
        description_parts.extend(raw_lines[1:])

    return {
        "source_dataset": "class",
        "source_file": page_file.path.name,
        "source_page": page_file.page,
        "source_row_index": row_index,
        "source_line_start": line_start,
        "source_line_end": line_end,
        "class_name": class_name,
        "description_raw": "\n".join(description_parts),
        "raw_record_text": "\n".join(raw_lines),
    }


def parse_classes() -> tuple[list[dict[str, object]], list[str]]:
    folder = RAW_ROOT / "classes"
    rows: list[dict[str, object]] = []
    warnings: list[str] = []

    for page_file in page_files(folder):
        lines = read_lines(page_file.path)
        in_table = False
        current_lines: list[str] = []
        current_line_start = 0
        row_index = 0

        for index, line in enumerate(lines, start=1):
            if not in_table:
                if line == "수업명\t설명\t작업":
                    in_table = True
                continue

            if line.startswith("총 125개"):
                break

            if not current_lines and not is_class_record_start(line):
                continue

            if is_class_record_start(line):
                if current_lines:
                    row_index += 1
                    rows.append(
                        parse_class_record(
                            page_file=page_file,
                            row_index=row_index,
                            raw_lines=current_lines,
                            line_start=current_line_start,
                            line_end=index - 1,
                        )
                    )
                current_lines = [line]
                current_line_start = index
            else:
                current_lines.append(line)

        if current_lines:
            row_index += 1
            rows.append(
                parse_class_record(
                    page_file=page_file,
                    row_index=row_index,
                    raw_lines=current_lines,
                    line_start=current_line_start,
                    line_end=current_line_start + len(current_lines) - 1,
                )
            )

        expected_rows = 5 if page_file.page == 13 else 10
        if row_index != expected_rows:
            warnings.append(
                f"classes/{page_file.path.name}: expected {expected_rows} class rows based on page position, parsed {row_index}."
            )

    return rows, warnings


def parse_teachers() -> tuple[list[dict[str, object]], list[str]]:
    folder = RAW_ROOT / "teachers"
    rows: list[dict[str, object]] = []
    warnings: list[str] = []

    for page_file in page_files(folder):
        lines = read_lines(page_file.path)
        in_table = False
        pending_lines: list[str] = []
        pending_line_start = 0
        row_index = 0

        for index, line in enumerate(lines, start=1):
            if not in_table:
                if line == "등록일":
                    in_table = True
                continue

            if line.startswith("총 47명"):
                break

            if not line:
                continue

            detail_match = TEACHER_DETAIL_RE.match(line)
            if detail_match:
                raw_lines = pending_lines + [line]
                name_candidates = [item for item in pending_lines if item != "앱연동"]
                teacher_name = name_candidates[0] if name_candidates else ""
                app_linked_text = "앱연동" if "앱연동" in pending_lines else ""

                row_index += 1
                rows.append(
                    {
                        "source_dataset": "teacher",
                        "source_file": page_file.path.name,
                        "source_page": page_file.page,
                        "source_row_index": row_index,
                        "source_line_start": pending_line_start or index,
                        "source_line_end": index,
                        "teacher_name": teacher_name,
                        "app_linked_text": app_linked_text,
                        "phone_text": detail_match.group("phone"),
                        "role": detail_match.group("role"),
                        "registered_date_text": detail_match.group("registered_date").strip(),
                        "raw_record_text": "\n".join(raw_lines),
                    }
                )
                pending_lines = []
                pending_line_start = 0
                continue

            if not pending_lines:
                pending_line_start = index
            pending_lines.append(line)

        if pending_lines:
            warnings.append(
                f"teachers/{page_file.path.name}: leftover lines after parsing teacher records: {' | '.join(pending_lines)}"
            )

        expected_rows = 7 if page_file.page == 5 else 10
        if row_index != expected_rows:
            warnings.append(
                f"teachers/{page_file.path.name}: expected {expected_rows} teacher rows based on page position, parsed {row_index}."
            )

    return rows, warnings


def count_page_files(folder_name: str) -> int:
    return len(page_files(RAW_ROOT / folder_name))


def report_section(title: str, lines: Iterable[str]) -> list[str]:
    result = [f"## {title}", ""]
    result.extend(lines)
    result.append("")
    return result


def write_report(
    classes: list[dict[str, object]],
    teachers: list[dict[str, object]],
    reservation_rows: list[dict[str, object]],
    cancel_rows: list[dict[str, object]],
    warnings: list[str],
) -> None:
    report_lines: list[str] = [
        "# ON STUDIO 전처리 리포트",
        "",
        "이 리포트는 분석 결과가 아니라, CSV 전처리 결과가 원본 수집 현황과 맞는지 확인하기 위한 검증 기록이다.",
        "",
    ]

    report_lines.extend(
        report_section(
            "생성 파일",
            [
                "- `data\\processed\\onstudio\\public\\onstudio_classes_2026_yeonhui_yoga_week.csv`",
                "- `data\\processed\\onstudio\\private\\onstudio_teachers_2026_yeonhui_yoga_week.csv`",
                "- `data\\processed\\onstudio\\private\\onstudio_reservation_2026_yeonhui_yoga_week.csv`",
                "- `data\\processed\\onstudio\\private\\onstudio_cancel_2026_yeonhui_yoga_week.csv`",
            ],
        )
    )

    report_lines.extend(
        report_section(
            "건수 검증",
            [
                f"- 수업 정보: {len(classes)}건 / 기대값 {EXPECTED_CLASS_ROWS}건",
                f"- 강사 정보: {len(teachers)}건 / 기대값 {EXPECTED_TEACHER_ROWS}명",
                f"- 예약건 정보: {len(reservation_rows)}건 / 기대값 {EXPECTED_RESERVATION_ROWS}건",
                f"- 취소건 정보: {len(cancel_rows)}건 / 기대값 {EXPECTED_CANCEL_ROWS}건",
                f"- 예약 + 취소 합계: {len(reservation_rows) + len(cancel_rows)}건 / 기대값 {EXPECTED_RESERVATION_ROWS + EXPECTED_CANCEL_ROWS}건",
            ],
        )
    )

    report_lines.extend(
        report_section(
            "원본 페이지 파일 수",
            [
                f"- `classes`: {count_page_files('classes')}개",
                f"- `teachers`: {count_page_files('teachers')}개",
                f"- `reservations`: {count_page_files('reservations')}개",
                f"- `cancellations`: {count_page_files('cancellations')}개",
            ],
        )
    )

    if warnings:
        report_lines.extend(report_section("주의 또는 확인 필요", [f"- {item}" for item in warnings]))
    else:
        report_lines.extend(report_section("주의 또는 확인 필요", ["- 없음"]))

    report_lines.extend(
        report_section(
            "보존 원칙",
            [
                "- 원본 txt 파일은 수정하지 않았다.",
                "- 각 CSV 행에는 `source_file`, `source_page`, `source_line_start`, `source_line_end`를 남겼다.",
                "- 각 CSV 행에는 원본 행 묶음을 담은 `raw_record_text`를 남겼다.",
                "- 예약 상태는 원본 행에서 복사되지 않으므로 폴더명을 기준으로 `status`와 `status_source`를 부여했다.",
            ],
        )
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "onstudio_preprocessing_report.md").write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )


def main() -> None:
    class_rows, class_warnings = parse_classes()
    teacher_rows, teacher_warnings = parse_teachers()
    reservation_rows, reservation_warnings = parse_booking_folder("reservations", "예약", "reservation")
    cancel_rows, cancel_warnings = parse_booking_folder("cancellations", "취소", "cancel")

    class_fields = [
        "source_dataset",
        "source_file",
        "source_page",
        "source_row_index",
        "source_line_start",
        "source_line_end",
        "class_name",
        "description_raw",
        "raw_record_text",
    ]
    teacher_fields = [
        "source_dataset",
        "source_file",
        "source_page",
        "source_row_index",
        "source_line_start",
        "source_line_end",
        "teacher_name",
        "app_linked_text",
        "phone_text",
        "role",
        "registered_date_text",
        "raw_record_text",
    ]
    booking_fields = [
        "source_dataset",
        "status",
        "status_source",
        "source_file",
        "source_page",
        "source_row_index",
        "source_line_start",
        "source_line_end",
        "request_datetime_text",
        "cancel_datetime_text",
        "request_cancel_line_extra_text",
        "request_cancel_line_raw",
        "class_datetime_text",
        "class_info_text",
        "reserver_name",
        "phone",
        "people_count_text",
        "booking_method_text",
        "people_booking_line_extra_text",
        "people_booking_line_raw",
        "raw_record_text",
    ]

    write_csv(
        PUBLIC_OUTPUT_DIR / "onstudio_classes_2026_yeonhui_yoga_week.csv",
        class_rows,
        class_fields,
    )
    write_csv(
        PRIVATE_OUTPUT_DIR / "onstudio_teachers_2026_yeonhui_yoga_week.csv",
        teacher_rows,
        teacher_fields,
    )
    write_csv(
        PRIVATE_OUTPUT_DIR / "onstudio_reservation_2026_yeonhui_yoga_week.csv",
        reservation_rows,
        booking_fields,
    )
    write_csv(
        PRIVATE_OUTPUT_DIR / "onstudio_cancel_2026_yeonhui_yoga_week.csv",
        cancel_rows,
        booking_fields,
    )

    warnings = class_warnings + teacher_warnings + reservation_warnings + cancel_warnings
    write_report(class_rows, teacher_rows, reservation_rows, cancel_rows, warnings)

    print("ON STUDIO preprocessing complete")
    print(f"classes={len(class_rows)}")
    print(f"teachers={len(teacher_rows)}")
    print(f"reservation={len(reservation_rows)}")
    print(f"cancel={len(cancel_rows)}")
    print(f"warnings={len(warnings)}")


if __name__ == "__main__":
    main()
