from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

ONSTUDIO_PUBLIC_DIR = ROOT / "data" / "processed" / "onstudio" / "public"
ONSTUDIO_PRIVATE_DIR = ROOT / "data" / "processed" / "onstudio" / "private"
OBUD_INTERIM_DIR = ROOT / "data" / "interim" / "obud_reviews"
OBUD_PRIVATE_DIR = ROOT / "data" / "processed" / "obud_reviews" / "private"
OBUD_PUBLIC_DIR = ROOT / "data" / "processed" / "obud_reviews" / "public"
ANALYSIS_PUBLIC_DIR = ROOT / "data" / "processed" / "analysis" / "public"
REPORT_ANALYSIS_DIR = ROOT / "reports" / "analysis"
REPORT_OBUD_DIR = ROOT / "reports" / "obud_reviews"
REFERENCE_DIR = ROOT / "references"

ONSTUDIO_CLASSES_PUBLIC = ONSTUDIO_PUBLIC_DIR / "onstudio_classes_2026_yeonhui_yoga_week.csv"
ONSTUDIO_RESERVATIONS_PUBLIC = (
    ONSTUDIO_PUBLIC_DIR / "onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv"
)
ONSTUDIO_CANCELLATIONS_PUBLIC = (
    ONSTUDIO_PUBLIC_DIR / "onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv"
)
ONSTUDIO_RESERVATIONS_PRIVATE = ONSTUDIO_PRIVATE_DIR / "onstudio_reservation_2026_yeonhui_yoga_week.csv"
ONSTUDIO_CANCELLATIONS_PRIVATE = ONSTUDIO_PRIVATE_DIR / "onstudio_cancel_2026_yeonhui_yoga_week.csv"

OBUD_OCR_RAW = OBUD_INTERIM_DIR / "google_vision_ocr_raw.csv"
OBUD_EXTRACTED_PRIVATE = OBUD_PRIVATE_DIR / "obud_reviews_extracted_private.csv"
OBUD_AI_CHECKED_PRIVATE = OBUD_PRIVATE_DIR / "obud_reviews_ai_checked_private.csv"
OBUD_REVIEWER_MATCH_PRIVATE = OBUD_PRIVATE_DIR / "review_reviewer_match_private.csv"
OBUD_DEIDENTIFIED_PUBLIC = OBUD_PUBLIC_DIR / "obud_reviews_deidentified.csv"

CLASS_HYPE_METRICS_PUBLIC = ANALYSIS_PUBLIC_DIR / "class_hype_metrics.csv"
STUDIO_HYPE_METRICS_PUBLIC = ANALYSIS_PUBLIC_DIR / "studio_hype_metrics.csv"


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def compact_spaces(value: object) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def normalize_text(value: object) -> str:
    text = str(value).lower() if value is not None else ""
    chars: list[str] = []
    previous_space = False
    for char in text:
        if char.isalnum():
            chars.append(char)
            previous_space = False
        elif not previous_space:
            chars.append(" ")
            previous_space = True
    return "".join(chars).strip()


def normalize_for_join(value: object) -> str:
    return normalize_text(value).replace(" ", "")


def safe_int(value: object) -> int | None:
    text = compact_spaces(value)
    if not text:
        return None
    match = re.search(r"-?\d+", text.replace(",", ""))
    return int(match.group(0)) if match else None


def safe_float(value: object) -> float | None:
    text = compact_spaces(value)
    if not text:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    return float(match.group(0)) if match else None


def ticket_count(value: object) -> int | None:
    text = str(value)
    match = re.search(r"(1|4|8|10|20)\s*회권", text)
    return int(match.group(1)) if match else None


def booking_method_group(value: object) -> str:
    text = str(value)
    if "1회권" in text:
        return "one_time"
    if "패스" in text:
        return "pass"
    return "unknown"


def extract_bracket_label(class_title: object) -> str:
    match = re.search(r"\[([^\]]+)\]", str(class_title))
    return compact_spaces(match.group(1)) if match else ""


def strip_bracket_label(class_title: object) -> str:
    return compact_spaces(re.sub(r"^\[[^\]]+\]\s*", "", str(class_title)))


NAME_CANONICALIZATION_REGISTRY = [
    {
        "entity_type": "studio",
        "raw_value": "대저택 프라이빗",
        "canonical_key": "대저택프라이빗",
        "display_name": "대저택프라이빗",
        "notes": "띄어쓰기 차이로 같은 요가원이 갈라지지 않도록 통합",
    },
    {
        "entity_type": "studio",
        "raw_value": "대저택프라이빗",
        "canonical_key": "대저택프라이빗",
        "display_name": "대저택프라이빗",
        "notes": "표준 표기",
    },
    {
        "entity_type": "studio",
        "raw_value": "숨 명상센터",
        "canonical_key": "숨명상센터",
        "display_name": "숨명상센터",
        "notes": "띄어쓰기 차이로 같은 요가원이 갈라지지 않도록 통합",
    },
    {
        "entity_type": "studio",
        "raw_value": "숨명상센터",
        "canonical_key": "숨명상센터",
        "display_name": "숨명상센터",
        "notes": "표준 표기",
    },
    {
        "entity_type": "studio",
        "raw_value": "비전스트롤",
        "canonical_key": "비전스트롤 콜라보",
        "display_name": "비전스트롤 콜라보",
        "notes": "행사 표기상 협업 수업 장소는 비전스트롤 콜라보로 통합",
    },
    {
        "entity_type": "studio",
        "raw_value": "비전스트롤 콜라보",
        "canonical_key": "비전스트롤 콜라보",
        "display_name": "비전스트롤 콜라보",
        "notes": "표준 표기",
    },
    {
        "entity_type": "studio",
        "raw_value": "시작",
        "canonical_key": "시이작",
        "display_name": "시이작",
        "notes": "OCR이 시이작을 시작으로 읽는 경우 보정",
    },
    {
        "entity_type": "class_bracket",
        "raw_value": "연희정음 랜드마크",
        "canonical_key": "연희정음|랜드마크",
        "display_name": "연희정음|랜드마크",
        "notes": "오붓 OCR에서 구분자 |가 공백으로 읽히는 경우 보정",
    },
    {
        "entity_type": "class_bracket",
        "raw_value": "연남장 커뮤니티허브",
        "canonical_key": "연남장|커뮤니티허브",
        "display_name": "연남장|커뮤니티허브",
        "notes": "오붓 OCR에서 구분자 |가 공백으로 읽히는 경우 보정",
    },
]

STUDIO_ALIASES = {
    "BigBlueYoga": "빅블루요가",
    "big blue yoga": "빅블루요가",
    "Mytri": "마이트리",
    "Maitri": "마이트리",
    "Yeonhee Special": "연희스페셜",
    "Yeonhui Special": "연희스페셜",
    "Vision Stroll Collaboration": "비전스트롤 콜라보",
    "Rooftop Yoga": "옥상요가",
    **{
        item["raw_value"]: item["canonical_key"]
        for item in NAME_CANONICALIZATION_REGISTRY
        if item["entity_type"] == "studio"
    },
}

CLASS_BRACKET_ALIASES = {
    item["raw_value"]: item["canonical_key"]
    for item in NAME_CANONICALIZATION_REGISTRY
    if item["entity_type"] == "class_bracket"
}

PIPE_STUDIO_ALIASES = {
    "연남장|커뮤니티허브": "연남장",
    "연희정음|랜드마크": "연희정음",
    "데이스타콜라보|연희스페셜": "데이스타콜라보",
    "마이트리|연희스페셜": "마이트리",
    "마인드플로우|연희스페셜": "마인드플로우",
    "빅블루요가|연희스페셜": "빅블루요가",
    "시이작|연희스페셜": "시이작",
    "시이작|어린이날 키즈요가": "시이작",
    "비전스트롤 콜라보|옥상요가": "비전스트롤 콜라보",
}


def _apply_aliases(value: str, aliases: dict[str, str]) -> str:
    output = compact_spaces(value)
    for source, target in aliases.items():
        if output.lower() == source.lower():
            return target
    for source, target in aliases.items():
        if re.search(r"[A-Za-z]", source):
            output = re.sub(re.escape(source), target, output, flags=re.IGNORECASE)
    return output


def canonical_bracket_display_label(value: object) -> str:
    label = compact_spaces(value).replace(" | ", "|").replace(" |", "|").replace("| ", "|")
    label = _apply_aliases(label, CLASS_BRACKET_ALIASES)
    label = _apply_aliases(label, STUDIO_ALIASES)
    return compact_spaces(label).replace(" | ", "|").replace(" |", "|").replace("| ", "|")


def normalize_studio_key(value: object) -> str:
    label = canonical_bracket_display_label(value)
    if label in PIPE_STUDIO_ALIASES:
        return PIPE_STUDIO_ALIASES[label]
    if "|" in label:
        label = label.split("|", 1)[0]
    label = _apply_aliases(compact_spaces(label), STUDIO_ALIASES)
    no_space_label = label.replace(" ", "")
    if no_space_label == "대저택프라이빗":
        return "대저택프라이빗"
    if no_space_label == "숨명상센터":
        return "숨명상센터"
    if no_space_label == "비전스트롤":
        return "비전스트롤 콜라보"
    return compact_spaces(label)


def canonical_class_title_display(class_title: object) -> str:
    raw = compact_spaces(class_title)
    label = extract_bracket_label(raw)
    body = strip_bracket_label(raw)
    if not label:
        return body
    display_label = canonical_bracket_display_label(label)
    if not body:
        return f"[{display_label}]"
    return f"[{display_label}] {body}"


def studio_key_from_class_title(class_title: object) -> str:
    return normalize_studio_key(extract_bracket_label(class_title))


def canonical_class_key(class_title: object) -> str:
    return normalize_for_join(canonical_class_title_display(class_title))


def percentile_0_100(values: Iterable[object]) -> list[float | None]:
    numeric_values = [safe_float(value) for value in values]
    valid = sorted(value for value in numeric_values if value is not None and not math.isnan(value))
    if not valid:
        return [None for _ in numeric_values]
    if len(valid) == 1:
        return [100.0 if value is not None else None for value in numeric_values]
    result: list[float | None] = []
    for value in numeric_values:
        if value is None or math.isnan(value):
            result.append(None)
            continue
        below = sum(1 for item in valid if item < value)
        same = sum(1 for item in valid if item == value)
        result.append(round((below + 0.5 * same) / len(valid) * 100, 2))
    return result


def minmax_0_100(values: Iterable[object]) -> list[float | None]:
    numeric_values = [safe_float(value) for value in values]
    valid = [value for value in numeric_values if value is not None and not math.isnan(value)]
    if not valid:
        return [None for _ in numeric_values]
    minimum = min(valid)
    maximum = max(valid)
    if maximum == minimum:
        return [100.0 if value is not None else None for value in numeric_values]
    return [
        round((value - minimum) / (maximum - minimum) * 100, 2) if value is not None else None
        for value in numeric_values
    ]
