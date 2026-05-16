from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

from review_processing_utils import (
    OBUD_EXTRACTED_PRIVATE,
    ONSTUDIO_CANCELLATIONS_PUBLIC,
    ONSTUDIO_CLASSES_PUBLIC,
    ONSTUDIO_RESERVATIONS_PUBLIC,
    REPORT_OBUD_DIR,
    canonical_class_key,
    canonical_bracket_display_label,
    canonical_class_title_display,
    extract_bracket_label,
    normalize_studio_key,
    normalize_for_join,
    normalize_text,
    strip_bracket_label,
    studio_key_from_class_title,
    write_csv,
    write_text,
)


AUTO_APPROVE_THRESHOLD = 90.0
MATCH_OUTPUT_COLUMNS = [
    "class_title_match_query",
    "class_title_matched",
    "class_title_base",
    "class_match_score",
    "class_match_method",
    "class_match_needs_review",
    "class_match_source",
    "class_key",
    "class_base_key",
    "studio_key",
    "needs_review",
]

QUERY_REPLACEMENTS = [
    (r"Big\s*Blue\s*Yoga", "빅블루요가"),
    (r"Alignment\s+of\s+the\s+Backbend", "후굴의 정렬"),
    (r"Mytri", "마이트리"),
    (r"Maitri", "마이트리"),
    (r"Yeonhee\s+Special", "연희스페셜"),
    (r"Yeonhui\s+Special", "연희스페셜"),
    (r"All\s+Levels?\s+Vinyasa", "올레벨 빈야사"),
    (r"Reading\s+and\s+Yoga", "독서와 요가"),
    (r"Vision\s+Stroll\s+Collaboration", "비전스트롤 콜라보"),
    (r"Rooftop\s+Yoga", "옥상요가"),
    (r"Coffee\s+and\s+Yoga", "커피와 요가"),
    (r"Ashtanga\s+Full\s+Primary", "아쉬탕가 풀프라이머리"),
    (r"연희정음\s+랜드마크", "연희정음|랜드마크"),
    (r"시이연희스페셜", "시이작|연희스페셜"),
    (r"역동적명상", "역동적 명상"),
]


@dataclass(frozen=True)
class ClassReference:
    class_title_standard: str
    class_title_base: str
    class_source: str
    class_key: str
    class_base_key: str
    match_text: str
    body_key: str
    bracket_label: str
    studio_key: str
    source_priority: int


def apply_query_aliases(value: object) -> str:
    text = str(value)
    for pattern, replacement in QUERY_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def base_title_if_available(title: str, known_titles: set[str]) -> str:
    match = re.search(r"\s+\([^)]{1,40}\)$", title)
    if not match:
        return title
    candidate = title[: match.start()].strip()
    return candidate if candidate in known_titles else title


def load_references() -> list[ClassReference]:
    rows: list[dict[str, str]] = []

    classes = pd.read_csv(ONSTUDIO_CLASSES_PUBLIC, dtype=str, keep_default_na=False)
    for title in classes["class_name"].dropna().astype(str):
        if title.strip():
            rows.append({"class_title_standard": title.strip(), "class_source": "onstudio_classes"})

    for path, source in [
        (ONSTUDIO_RESERVATIONS_PUBLIC, "onstudio_reservations"),
        (ONSTUDIO_CANCELLATIONS_PUBLIC, "onstudio_cancellations"),
    ]:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        for title in frame["class_info_text"].dropna().astype(str):
            if title.strip():
                rows.append({"class_title_standard": title.strip(), "class_source": source})

    reference_frame = pd.DataFrame(rows).drop_duplicates("class_title_standard")
    reference_frame["class_title_standard"] = reference_frame["class_title_standard"].map(
        canonical_class_title_display
    )
    reference_frame = reference_frame.drop_duplicates("class_title_standard")
    known_titles = set(reference_frame["class_title_standard"])
    source_priority = {
        "onstudio_classes": 0,
        "onstudio_reservations": 1,
        "onstudio_cancellations": 2,
    }

    references: list[ClassReference] = []
    for _, row in reference_frame.iterrows():
        title = canonical_class_title_display(row["class_title_standard"])
        base_title = canonical_class_title_display(base_title_if_available(title, known_titles))
        references.append(
            ClassReference(
                class_title_standard=title,
                class_title_base=base_title,
                class_source=row["class_source"],
                class_key=canonical_class_key(title),
                class_base_key=canonical_class_key(base_title),
                match_text=normalize_text(title),
                body_key=normalize_for_join(strip_bracket_label(base_title)),
                bracket_label=canonical_bracket_display_label(extract_bracket_label(base_title)),
                studio_key=studio_key_from_class_title(base_title),
                source_priority=source_priority.get(row["class_source"], 9),
            )
        )
    return references


GENERIC_CLASS_BODY_KEYS = {"요가", "명상", "수업", "필라테스"}


def specificity_adjusted_score(
    query_body_key: str,
    query_studio_key: str,
    query_bracket_label: str,
    query_class_key: str,
    reference: ClassReference,
) -> tuple[float, str]:
    if query_class_key and query_class_key in {reference.class_key, reference.class_base_key}:
        return 101.0, "exact_full_class_key"

    wratio = fuzz.WRatio(normalize_text(query_body_key), normalize_text(reference.body_key))
    token_score = fuzz.token_set_ratio(normalize_text(query_body_key), normalize_text(reference.body_key))
    full_wratio = fuzz.WRatio(normalize_text(query_body_key), normalize_text(reference.class_title_base))
    score = max(wratio, token_score, full_wratio)
    method = "rapidfuzz_token_set" if token_score >= max(wratio, full_wratio) else "rapidfuzz_wratio"

    if query_body_key and query_body_key == reference.body_key:
        if query_studio_key and reference.studio_key and query_studio_key != reference.studio_key:
            score = min(score, AUTO_APPROVE_THRESHOLD - 1)
            method = "exact_body_key+studio_mismatch_guard"
        elif query_bracket_label and query_bracket_label == reference.bracket_label:
            return 100.5, "exact_body_and_bracket_key"
        else:
            return 100.0, "exact_body_key"

    if query_body_key and reference.body_key and query_body_key in reference.body_key:
        score = max(score, 94.0)
        method = f"{method}+query_contained"
    elif query_body_key and reference.body_key and reference.body_key in query_body_key and len(reference.body_key) >= 5:
        score = max(score, 92.0)
        method = f"{method}+reference_contained"

    if query_studio_key and reference.studio_key and query_studio_key != reference.studio_key:
        score -= 8.0
        method = f"{method}+studio_penalty"

    query_len = max(len(query_body_key), 1)
    reference_len = len(reference.body_key)
    coverage_ratio = reference_len / query_len
    if len(query_body_key) >= 8 and (
        reference.body_key in GENERIC_CLASS_BODY_KEYS or coverage_ratio < 0.45
    ):
        score = min(score, AUTO_APPROVE_THRESHOLD - 1)
        method = f"{method}+short_generic_guard"
    elif len(query_body_key) >= 8 and coverage_ratio < 0.65 and score < 98:
        score = min(score, AUTO_APPROVE_THRESHOLD - 1)
        method = f"{method}+coverage_guard"

    return score, method


def match_one(query: object, references: list[ClassReference]) -> dict[str, object]:
    query_raw = str(query).strip()
    query_alias = canonical_class_title_display(apply_query_aliases(query_raw))
    query_norm = normalize_text(query_alias)
    query_body_key = normalize_for_join(strip_bracket_label(query_alias))
    query_studio_key = studio_key_from_class_title(query_alias)
    query_bracket_label = canonical_bracket_display_label(extract_bracket_label(query_alias))
    query_class_key = canonical_class_key(query_alias)

    if not query_norm:
        return {
            "class_title_match_query": query_alias,
            "class_title_matched": "",
            "class_title_base": "",
            "class_match_score": "",
            "class_match_method": "missing_ocr_class_title",
            "class_match_needs_review": True,
            "class_match_source": "",
            "class_key": "",
            "class_base_key": "",
            "studio_key": "",
        }

    best_ref: ClassReference | None = None
    best_score = -1.0
    best_method = "rapidfuzz_wratio"
    best_tie_breaker: tuple[int, float, int, int] = (-1, -1.0, -1, -99)

    for reference in references:
        score, method = specificity_adjusted_score(
            query_body_key=query_body_key,
            query_studio_key=query_studio_key,
            query_bracket_label=query_bracket_label,
            query_class_key=query_class_key,
            reference=reference,
        )
        if reference.class_title_standard == reference.class_title_base:
            score += 0.01
        coverage_ratio = len(reference.body_key) / max(len(query_body_key), 1)
        bracket_match = 1 if query_bracket_label and query_bracket_label == reference.bracket_label else 0
        tie_breaker = (bracket_match, coverage_ratio, len(reference.body_key), -reference.source_priority)
        if score > best_score or (score == best_score and tie_breaker > best_tie_breaker):
            best_score = score
            best_ref = reference
            best_method = method
            best_tie_breaker = tie_breaker

    if best_ref is None:
        raise RuntimeError("No class references were available.")

    score_for_output = round(min(best_score, 100.0), 2)
    needs_review = score_for_output < AUTO_APPROVE_THRESHOLD
    if query_alias != query_raw and not needs_review:
        best_method = f"{best_method}+query_alias"

    return {
        "class_title_match_query": query_alias,
        "class_title_matched": best_ref.class_title_standard,
        "class_title_base": best_ref.class_title_base,
        "class_match_score": score_for_output,
        "class_match_method": best_method,
        "class_match_needs_review": needs_review,
        "class_match_source": best_ref.class_source,
        "class_key": best_ref.class_key,
        "class_base_key": best_ref.class_base_key,
        "studio_key": normalize_studio_key(best_ref.studio_key),
    }


def main() -> None:
    if not OBUD_EXTRACTED_PRIVATE.exists():
        raise FileNotFoundError(
            f"Missing parsed review table. Run scripts/parse_obud_reviews.py first: {OBUD_EXTRACTED_PRIVATE}"
        )

    reviews = pd.read_csv(OBUD_EXTRACTED_PRIVATE, dtype=str, keep_default_na=False)
    reviews = reviews.drop(columns=[column for column in MATCH_OUTPUT_COLUMNS if column in reviews.columns])
    references = load_references()
    matched_rows = [match_one(row.get("class_title_ocr", ""), references) for _, row in reviews.iterrows()]
    matched = pd.concat([reviews, pd.DataFrame(matched_rows)], axis=1)

    combined_needs_review = (
        matched["parse_needs_review"].astype(str).str.lower().eq("true")
        | matched["class_match_needs_review"].astype(str).str.lower().eq("true")
    )
    matched["needs_review"] = combined_needs_review

    write_csv(matched, OBUD_EXTRACTED_PRIVATE)

    low_matches = matched[matched["class_match_needs_review"].astype(str).str.lower().eq("true")]
    report_path = REPORT_OBUD_DIR / "obud_review_class_matching_report.md"
    examples = "\n".join(
        f"- {row.review_id}: OCR `{row.class_title_ocr}` -> `{row.class_title_matched}` "
        f"(score {row.class_match_score})"
        for row in low_matches.head(20).itertuples()
    )
    if not examples:
        examples = "- 90점 미만 자동 매칭 없음"

    report = f"""# 오붓 리뷰 수업명 매칭 리포트

## 입력
- 리뷰 파싱 private 표: `{OBUD_EXTRACTED_PRIVATE.relative_to(Path.cwd())}`
- ON STUDIO 수업 카탈로그: `{ONSTUDIO_CLASSES_PUBLIC.relative_to(Path.cwd())}`
- ON STUDIO 예약/취소 수업명: `{ONSTUDIO_RESERVATIONS_PUBLIC.relative_to(Path.cwd())}`, `{ONSTUDIO_CANCELLATIONS_PUBLIC.relative_to(Path.cwd())}`

## 방식
- Google Vision OCR에서 추출된 `class_title_ocr`을 ON STUDIO 표준 수업명 후보와 비교했다.
- 영어 OCR 표기와 일부 OCR 흔들림은 `QUERY_REPLACEMENTS` 규칙으로 먼저 보정했다.
- 이후 `RapidFuzz`의 WRatio/token set 유사도를 사용했다.
- 자동 승인 기준: {AUTO_APPROVE_THRESHOLD:.0f}점 이상.

## 결과
- 전체 리뷰: {len(matched)}건
- 자동 승인 수업명 매칭: {(~matched['class_match_needs_review'].astype(str).str.lower().eq('true')).sum()}건
- 수업명 검수 필요: {len(low_matches)}건

## 90점 미만 또는 수업명 누락 예시
{examples}
"""
    write_text(report_path, report)

    print(f"Matched {len(matched)} review class titles")
    print(f"Class matches needing review: {len(low_matches)}")
    print(f"Wrote {OBUD_EXTRACTED_PRIVATE}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
