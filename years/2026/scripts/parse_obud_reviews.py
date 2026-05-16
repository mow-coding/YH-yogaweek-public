from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from review_processing_utils import (
    OBUD_EXTRACTED_PRIVATE,
    OBUD_OCR_RAW,
    REPORT_OBUD_DIR,
    compact_spaces,
    ticket_count,
    write_csv,
    write_text,
)


HEADER_RE = re.compile(
    r"^(?P<masked_reviewer>\S+님)\s+"
    r"(?P<review_date>\d{4}\.\d{2}\.\d{2})\s*[\.\-]?\s*"
    r"(?P<visit_count>\d+)\s*번째\s*방문"
)
RATING_OVERALL_RE = re.compile(r"★\s*(?P<rating>[0-5](?:\.\d+)?)\s*수업")
RATING_CLASS_RE = re.compile(r"수업\s*★?\s*(?P<rating>[0-5](?:\.\d+)?)")
RATING_ATMOSPHERE_RE = re.compile(r"분위기\s*★?\s*(?P<rating>[0-5](?:\.\d+)?)")
RATING_FACILITY_RE = re.compile(r"편의시설\s*★?\s*(?P<rating>[0-5](?:\.\d+)?)")
TICKET_RE = re.compile(r"연희요가위크\s*(?P<ticket>(?:1|4|8|10|20)\s*회권)")


def clean_line(line: object) -> str:
    return compact_spaces(str(line).replace("\u200b", ""))


def parse_rating(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group("rating") if match else ""


def extract_class_title(lines: list[str]) -> tuple[str, str, int | None]:
    for index, line in enumerate(lines):
        if "수업 [" in line:
            bracket_index = line.find("[")
            class_title = clean_line(line[bracket_index:])
            return class_title, class_title, index

        if line == "수업" and index + 1 < len(lines):
            next_line = clean_line(lines[index + 1])
            if next_line:
                return next_line, next_line, index + 1

    for index, line in enumerate(lines):
        if line.startswith("[") and "]" in line:
            return line, line, index

    return "", "", None


def extract_ticket(text: str) -> tuple[str, str]:
    match = TICKET_RE.search(text)
    if not match:
        return "", ""
    ticket = clean_line(match.group("ticket"))
    return f"연희요가위크 {ticket}", str(ticket_count(ticket) or "")


def is_non_review_line(line: str, header_line: str, class_title: str) -> bool:
    if not line:
        return True
    if line == header_line:
        return True
    if line == "수업":
        return True
    if line == class_title:
        return True
    if "★" in line and ("분위기" in line or "편의시설" in line or "수업" in line):
        return True
    if TICKET_RE.search(line):
        return True
    return False


def extract_review_text(lines: list[str], class_line_index: int | None, class_title: str) -> str:
    if class_line_index is None:
        candidates = lines[1:]
    else:
        candidates = lines[class_line_index + 1 :]

    header_line = lines[0] if lines else ""
    review_lines: list[str] = []
    for line in candidates:
        if TICKET_RE.search(line):
            break
        if is_non_review_line(line, header_line, class_title):
            continue
        review_lines.append(line)

    return "\n".join(review_lines).strip()


def parse_row(row: pd.Series) -> dict[str, object]:
    text = str(row.get("ocr_text", ""))
    lines = [clean_line(line) for line in text.splitlines() if clean_line(line)]
    joined = " ".join(lines)

    header = HEADER_RE.search(lines[0]) if lines else None
    class_title, class_title_raw, class_line_index = extract_class_title(lines)
    ticket_type, ticket_count_text = extract_ticket(text)
    review_text = extract_review_text(lines, class_line_index, class_title)

    warnings: list[str] = []
    if not header:
        warnings.append("missing_header")
    if not parse_rating(RATING_OVERALL_RE, joined):
        warnings.append("missing_overall_rating")
    if not parse_rating(RATING_CLASS_RE, joined):
        warnings.append("missing_class_rating")
    if not parse_rating(RATING_ATMOSPHERE_RE, joined):
        warnings.append("missing_atmosphere_rating")
    if not parse_rating(RATING_FACILITY_RE, joined):
        warnings.append("missing_facility_rating")
    if not class_title:
        warnings.append("missing_class_title")
    if not review_text:
        warnings.append("missing_review_text")

    review_date_text = header.group("review_date") if header else ""
    review_date_iso = review_date_text.replace(".", "-") if review_date_text else ""
    capture_order = int(row["review_capture_order"])

    return {
        "review_id": f"review_{capture_order:04d}",
        "review_capture_order": capture_order,
        "source_image": row.get("source_image", ""),
        "ocr_engine": row.get("ocr_engine", ""),
        "ocr_text_path": row.get("ocr_text_path", ""),
        "ocr_text_chars": row.get("ocr_text_chars", ""),
        "masked_reviewer": header.group("masked_reviewer") if header else "",
        "review_date_text": review_date_text,
        "review_date_iso": review_date_iso,
        "visit_count": header.group("visit_count") if header else "",
        "overall_rating": parse_rating(RATING_OVERALL_RE, joined),
        "class_rating": parse_rating(RATING_CLASS_RE, joined),
        "atmosphere_rating": parse_rating(RATING_ATMOSPHERE_RE, joined),
        "facility_rating": parse_rating(RATING_FACILITY_RE, joined),
        "class_title_ocr": class_title,
        "class_title_ocr_raw": class_title_raw,
        "review_text_ocr": review_text,
        "ticket_type_ocr": ticket_type,
        "ticket_count": ticket_count_text,
        "parse_needs_review": bool(warnings),
        "parse_warnings": ";".join(warnings),
        "ocr_text": text,
    }


def main() -> None:
    if not OBUD_OCR_RAW.exists():
        raise FileNotFoundError(f"Missing OCR raw CSV: {OBUD_OCR_RAW}")

    raw = pd.read_csv(OBUD_OCR_RAW, dtype=str, keep_default_na=False)
    parsed = pd.DataFrame([parse_row(row) for _, row in raw.iterrows()])
    write_csv(parsed, OBUD_EXTRACTED_PRIVATE)

    report_path = REPORT_OBUD_DIR / "obud_review_parsing_report.md"
    report = f"""# 오붓 리뷰 OCR 1차 파싱 리포트

## 입력
- 원천 OCR 표: `{OBUD_OCR_RAW.relative_to(Path.cwd())}`
- 입력 행 수: {len(raw)}

## 출력
- private 구조화 표: `{OBUD_EXTRACTED_PRIVATE.relative_to(Path.cwd())}`
- 출력 행 수: {len(parsed)}

## 추출률
- 작성자/날짜/방문회차: {(parsed['masked_reviewer'] != '').sum()} / {len(parsed)}
- 전체 별점: {(parsed['overall_rating'] != '').sum()} / {len(parsed)}
- 수업 별점: {(parsed['class_rating'] != '').sum()} / {len(parsed)}
- 분위기 별점: {(parsed['atmosphere_rating'] != '').sum()} / {len(parsed)}
- 편의시설 별점: {(parsed['facility_rating'] != '').sum()} / {len(parsed)}
- OCR 수업명: {(parsed['class_title_ocr'] != '').sum()} / {len(parsed)}
- 리뷰 본문: {(parsed['review_text_ocr'] != '').sum()} / {len(parsed)}
- 티켓 종류: {(parsed['ticket_type_ocr'] != '').sum()} / {len(parsed)}

## 검수 필요
- `parse_needs_review=true`: {parsed['parse_needs_review'].astype(bool).sum()}건

이 스크립트는 Google Vision OCR 결과 텍스트에서 리뷰 필드를 기계적으로 추출한다.  
개인 식별 가능성이 있는 `masked_reviewer`, 원문 OCR 텍스트는 private 산출물에만 저장한다.
"""
    write_text(report_path, report)

    print(f"Parsed {len(parsed)} review rows")
    print(f"Wrote {OBUD_EXTRACTED_PRIVATE}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
