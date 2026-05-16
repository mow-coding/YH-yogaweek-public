from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_INPUT_DIR = ROOT / "data" / "processed" / "onstudio" / "private"
PUBLIC_OUTPUT_DIR = ROOT / "data" / "processed" / "onstudio" / "public"
REPORT_DIR = ROOT / "reports" / "onstudio"

INPUT_FILES = [
    "onstudio_reservation_2026_yeonhui_yoga_week.csv",
    "onstudio_cancel_2026_yeonhui_yoga_week.csv",
]

OUTPUT_FILES = {
    "onstudio_reservation_2026_yeonhui_yoga_week.csv": "onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv",
    "onstudio_cancel_2026_yeonhui_yoga_week.csv": "onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv",
}

PHONE_RE = re.compile(r"\d{2,3}-\d{3,4}-\d{4}")
PARTICIPANT_ID_RE = re.compile(r"participant_(\d{4})")
PARTICIPANT_ID_PREFIX = "participant_"
PHONE_MASK = "PHONE_MASKED"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def participant_key(row: dict[str, str]) -> str:
    phone = row.get("phone", "").strip()
    name = row.get("reserver_name", "").strip()
    return f"{phone}\t{name}"


def record_key(row: dict[str, str]) -> str:
    return "\t".join(
        [
            row.get("source_dataset", ""),
            row.get("source_file", ""),
            row.get("source_row_index", ""),
            row.get("request_datetime_text", ""),
            row.get("class_datetime_text", ""),
            row.get("class_info_text", ""),
        ]
    )


def existing_deidentified_rows() -> dict[str, dict[str, str]]:
    rows_by_record_key: dict[str, dict[str, str]] = {}
    for input_file in INPUT_FILES:
        output_path = PUBLIC_OUTPUT_DIR / OUTPUT_FILES[input_file]
        if not output_path.exists():
            continue

        _, rows = read_csv(output_path)
        for row in rows:
            participant_id = row.get("reserver_name", "")
            if PARTICIPANT_ID_RE.fullmatch(participant_id):
                rows_by_record_key[record_key(row)] = row

    return rows_by_record_key


def build_participant_ids(rows_by_file: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    ids: dict[str, str] = {}
    existing_rows = existing_deidentified_rows()
    max_existing_number = 0

    for existing_row in existing_rows.values():
        match = PARTICIPANT_ID_RE.fullmatch(existing_row.get("reserver_name", ""))
        if match:
            max_existing_number = max(max_existing_number, int(match.group(1)))

    for input_file in INPUT_FILES:
        for row in rows_by_file[input_file]:
            existing_row = existing_rows.get(record_key(row))
            if not existing_row:
                continue

            existing_participant_id = existing_row.get("reserver_name", "")
            if PARTICIPANT_ID_RE.fullmatch(existing_participant_id):
                ids.setdefault(participant_key(row), existing_participant_id)

    next_number = max_existing_number + 1
    for input_file in INPUT_FILES:
        for row in rows_by_file[input_file]:
            key = participant_key(row)
            if key not in ids:
                ids[key] = f"{PARTICIPANT_ID_PREFIX}{next_number:04d}"
                next_number += 1
    return ids


def deidentify_raw_record_text(row: dict[str, str], participant_id: str) -> str:
    raw_record_text = row.get("raw_record_text", "")
    original_name = row.get("reserver_name", "")
    original_phone = row.get("phone", "")
    raw_lines = raw_record_text.splitlines()

    if len(raw_lines) >= 5:
        # 예약/취소 원본 묶음은 이름과 전화번호가 각각 4번째, 5번째 줄에 있다.
        raw_lines[3] = participant_id
        raw_lines[4] = PHONE_MASK
        return "\n".join(raw_lines)

    masked_text = raw_record_text
    if original_name:
        masked_text = masked_text.replace(original_name, participant_id)
    if original_phone:
        masked_text = masked_text.replace(original_phone, PHONE_MASK)
    masked_text = PHONE_RE.sub(PHONE_MASK, masked_text)
    return masked_text


def deidentify_rows(
    rows: list[dict[str, str]],
    participant_ids: dict[str, str],
) -> list[dict[str, str]]:
    deidentified: list[dict[str, str]] = []
    for row in rows:
        new_row = dict(row)
        participant_id = participant_ids[participant_key(row)]
        new_row["reserver_name"] = participant_id
        new_row["phone"] = PHONE_MASK
        new_row["raw_record_text"] = deidentify_raw_record_text(row, participant_id)
        deidentified.append(new_row)
    return deidentified


def validate_output(path: Path, expected_rows: int) -> dict[str, int | str]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    full_text = path.read_text(encoding="utf-8-sig")
    participant_id_bad_rows = sum(
        1 for row in rows if not re.fullmatch(r"participant_\d{4}", row.get("reserver_name", ""))
    )
    phone_column_bad_rows = sum(1 for row in rows if row.get("phone") != PHONE_MASK)
    raw_record_phone_matches = len(PHONE_RE.findall(full_text))

    return {
        "file": path.name,
        "rows": len(rows),
        "expected_rows": expected_rows,
        "participant_id_bad_rows": participant_id_bad_rows,
        "phone_column_bad_rows": phone_column_bad_rows,
        "remaining_phone_pattern_matches": raw_record_phone_matches,
    }


def write_report(validation_rows: list[dict[str, int | str]], unique_participant_count: int) -> None:
    lines = [
        "# ON STUDIO 예약/취소 비식별 사본 생성 리포트",
        "",
        "이 리포트는 예약/취소 CSV의 개인정보 비식별 사본 생성 결과를 기록한다.",
        "",
        "## 처리 원칙",
        "",
        "- 원본 CSV 파일은 수정하지 않았다.",
        "- 예약/취소 비식별 사본은 원본과 같은 21개 컬럼 구조를 유지한다.",
        "- `reserver_name`에는 실제 이름 대신 `participant_0001` 형식의 비식별 ID를 넣었다.",
        "- `phone`에는 실제 전화번호 대신 `PHONE_MASKED`를 넣었다.",
        "- `raw_record_text` 안의 고객 이름과 전화번호도 같은 방식으로 교체했다.",
        "- 비식별 ID는 예약/취소 두 파일 전체에서 같은 `전화번호 + 이름` 조합에 같은 값이 부여되도록 만들었다.",
        "- 기존 비식별 사본이 있으면 기존 participant ID를 최대한 유지하고, 새 고객에게만 다음 번호를 부여했다.",
        "- 원본 개인정보와 비식별 ID를 연결하는 별도 매핑 파일은 만들지 않았다.",
        "",
        "## 생성 파일",
        "",
        "- `data\\processed\\onstudio\\public\\onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv`",
        "- `data\\processed\\onstudio\\public\\onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv`",
        "",
        "## 검증 결과",
        "",
        f"- 고유 비식별 참여자 ID 수: {unique_participant_count}",
    ]

    for row in validation_rows:
        lines.extend(
            [
                f"- `{row['file']}`",
                f"  - 행 수: {row['rows']} / 기대값 {row['expected_rows']}",
                f"  - `reserver_name`이 participant ID 형식이 아닌 행: {row['participant_id_bad_rows']}",
                f"  - `phone`이 `PHONE_MASKED`가 아닌 행: {row['phone_column_bad_rows']}",
                f"  - 파일 전체 전화번호 패턴 잔존 횟수: {row['remaining_phone_pattern_matches']}",
            ]
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "onstudio_reservation_cancel_deidentification_report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    fieldnames_by_file: dict[str, list[str]] = {}
    rows_by_file: dict[str, list[dict[str, str]]] = {}
    for input_file in INPUT_FILES:
        fieldnames, rows = read_csv(PRIVATE_INPUT_DIR / input_file)
        fieldnames_by_file[input_file] = fieldnames
        rows_by_file[input_file] = rows

    participant_ids = build_participant_ids(rows_by_file)

    validation_rows: list[dict[str, int | str]] = []
    for input_file in INPUT_FILES:
        output_file = OUTPUT_FILES[input_file]
        deidentified_rows = deidentify_rows(rows_by_file[input_file], participant_ids)
        output_path = PUBLIC_OUTPUT_DIR / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_csv(output_path, fieldnames_by_file[input_file], deidentified_rows)
        validation_rows.append(validate_output(output_path, expected_rows=len(rows_by_file[input_file])))

    write_report(validation_rows, unique_participant_count=len(participant_ids))

    print("Reservation/cancel deidentification complete")
    print(f"unique_participants={len(participant_ids)}")
    for row in validation_rows:
        print(
            f"{row['file']}: rows={row['rows']}, remaining_phone_pattern_matches={row['remaining_phone_pattern_matches']}"
        )


if __name__ == "__main__":
    main()
