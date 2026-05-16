from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_BODY = ROOT / "data" / "raw" / "external_web" / "naver_blog_bodies_raw.csv"
BODY_FEATURES_INTERNAL = (
    ROOT / "data" / "interim" / "external_web" / "naver_blog_body_features_internal.csv"
)
INTERIM_OUTPUT = ROOT / "data" / "interim" / "external_web" / "naver_blog_body_deep_features_internal.csv"
PUBLIC_DIR = ROOT / "data" / "processed" / "analysis" / "public"
PUBLIC_FEATURES = PUBLIC_DIR / "yeonhui_yoga_week_naver_blog_body_deep_features_public.csv"
PUBLIC_POST_TYPE_SUMMARY = PUBLIC_DIR / "yeonhui_yoga_week_naver_blog_body_post_type_summary.csv"
PUBLIC_QUALITY_SUMMARY = PUBLIC_DIR / "yeonhui_yoga_week_naver_blog_body_quality_summary.csv"
REPORT_PATH = ROOT / "reports" / "external_web" / "naver_blog_body_deep_feature_report.md"

EVENT_CANONICAL = "연희요가위크"

EXPERIENCE_KEYWORDS = [
    "후기",
    "다녀",
    "갔다",
    "갔",
    "참여",
    "체험",
    "들었",
    "수련",
    "느꼈",
    "마셨",
    "만났",
    "걸었",
    "도착",
    "끝나고",
    "기록",
    "나는",
    "제가",
    "내가",
    "나의",
    "우리",
]

DETAIL_KEYWORDS = [
    "수업",
    "클래스",
    "선생님",
    "강사",
    "호흡",
    "명상",
    "차담",
    "매트",
    "공간",
    "장소",
    "몸",
    "마음",
    "움직임",
    "동작",
    "아사나",
    "싱잉볼",
    "대화",
    "사람들",
    "분위기",
    "프로그램",
]

REFLECTION_KEYWORDS = [
    "생각",
    "느꼈",
    "기억",
    "인상",
    "의미",
    "여운",
    "나에게",
    "스스로",
    "돌아보",
    "마음",
    "몸",
    "회복",
    "이완",
]

POSITIVE_AFFECT_KEYWORDS = [
    "좋았",
    "좋은",
    "좋다",
    "행복",
    "감동",
    "여운",
    "따뜻",
    "편안",
    "즐거",
    "재밌",
    "재미",
    "만족",
    "추천",
    "힐링",
    "회복",
    "감사",
    "사랑",
    "특별",
    "인상",
    "소중",
    "든든",
    "선물",
    "아름",
    "훌륭",
    "최고",
    "평온",
    "차분",
    "깊",
    "충만",
    "고요",
    "안정",
]

NEGATIVE_AFFECT_KEYWORDS = [
    "아쉬",
    "불편",
    "힘들",
    "실망",
    "별로",
    "부족",
    "어려웠",
    "어렵",
    "피곤",
    "아팠",
    "걱정",
    "복잡",
    "늦",
    "불안",
    "혼잡",
    "비싸",
    "아깝",
]

PROMO_KEYWORDS = [
    "모집",
    "신청",
    "예약",
    "티켓",
    "프로그램",
    "안내",
    "공지",
    "오픈",
    "진행합니다",
    "참여자 모집",
    "링크",
    "문의",
    "가격",
    "일정",
    "장소 안내",
    "선착순",
    "할인",
]

MIXED_TOPIC_KEYWORDS = [
    "맛집",
    "카페",
    "브런치",
    "커피",
    "데이트",
    "여행",
    "일상",
    "쇼핑",
    "패션",
    "룩",
    "코디",
    "제품",
    "협찬",
    "광고",
    "전시",
    "공연",
    "책",
    "독서",
    "육아",
    "주말",
    "산책",
    "숙소",
    "호텔",
    "식당",
    "디저트",
]


def normalize_for_match(value: object) -> str:
    return re.sub(r"\s+", "", str(value).lower())


def count_keywords(text: str, keywords: list[str]) -> int:
    normalized = normalize_for_match(text)
    return sum(normalized.count(normalize_for_match(keyword)) for keyword in keywords)


def clamp(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return int(max(minimum, min(maximum, round(value))))


def length_score(chars: int) -> int:
    if chars >= 1800:
        return 35
    if chars >= 1000:
        return 28
    if chars >= 600:
        return 20
    if chars >= 300:
        return 12
    if chars > 0:
        return 5
    return 0


def split_terms(value: object) -> list[str]:
    return [term for term in str(value).split(";") if term.strip()]


def relevance_level(row: dict[str, object]) -> str:
    event_count = int(row["body_event_keyword_count"])
    title_event_count = int(row["title_event_keyword_count"])
    score = int(row["body_relevance_score"])
    if event_count >= 2 and score >= 70:
        return "confirmed_body_strong"
    if event_count >= 1 and score >= 55:
        return "confirmed_body_basic"
    if event_count >= 1:
        return "confirmed_body_weak"
    if title_event_count >= 1:
        return "needs_review_title_only"
    return "needs_review_no_body_event_keyword"


def depth_label(score: int) -> str:
    if score >= 70:
        return "high_depth"
    if score >= 45:
        return "medium_depth"
    if score >= 25:
        return "low_depth"
    return "thin_reference"


def sentiment_tone(positive_count: int, negative_count: int, emotional_score: int) -> str:
    if negative_count >= 3 and negative_count >= positive_count:
        return "negative_or_disappointed"
    if positive_count >= 10 or emotional_score >= 65:
        return "very_positive"
    if positive_count >= 3:
        return "positive"
    if positive_count > 0 and negative_count > 0:
        return "mixed"
    return "neutral_or_unclear"


def topic_mixing_risk(mixed_count: int, event_count: int, chars: int) -> str:
    if mixed_count >= 5 and event_count <= 2:
        return "high"
    if mixed_count >= 3 and event_count <= 1:
        return "medium"
    if mixed_count >= 2 and event_count == 0 and chars >= 600:
        return "medium"
    return "low"


def interpret_post_type(row: dict[str, object]) -> str:
    if not bool(row["body_event_keyword_present"]):
        return "title_only_or_extraction_gap"
    if str(row["topic_mixing_risk"]) == "high" and int(row["body_event_keyword_count"]) <= 2:
        return "mixed_context_event_mention"
    if int(row["promo_keyword_count"]) >= 4 and int(row["experience_keyword_count"]) <= 2:
        return "official_or_promotional_notice"
    if int(row["experience_depth_score"]) >= 70 and int(row["emotional_intensity_score"]) >= 55:
        return "immersive_participant_review"
    if int(row["experience_depth_score"]) >= 45 and int(row["experience_keyword_count"]) >= 3:
        return "participant_experience_review"
    if int(row["space_or_detail_keyword_count"]) >= 8:
        return "space_or_program_overview"
    return "event_reference_or_light_review"


def build_deep_features(raw: pd.DataFrame, base_features: pd.DataFrame) -> pd.DataFrame:
    base_by_id = base_features.set_index("mention_id").to_dict("index") if not base_features.empty else {}
    rows: list[dict[str, object]] = []

    for _, raw_row in raw.iterrows():
        mention_id = str(raw_row.get("mention_id", ""))
        title = str(raw_row.get("title", ""))
        body = str(raw_row.get("body_text", ""))
        chars = int(str(raw_row.get("body_text_chars", "0") or "0"))
        base = base_by_id.get(mention_id, {})

        event_count = normalize_for_match(body).count(EVENT_CANONICAL)
        title_event_count = normalize_for_match(title).count(EVENT_CANONICAL)
        experience_count = count_keywords(body, EXPERIENCE_KEYWORDS)
        detail_count = count_keywords(body, DETAIL_KEYWORDS)
        reflection_count = count_keywords(body, REFLECTION_KEYWORDS)
        positive_count = count_keywords(body, POSITIVE_AFFECT_KEYWORDS)
        negative_count = count_keywords(body, NEGATIVE_AFFECT_KEYWORDS)
        promo_count = count_keywords(body, PROMO_KEYWORDS)
        mixed_count = count_keywords(body, MIXED_TOPIC_KEYWORDS)
        exclamation_count = body.count("!")
        studio_terms = split_terms(base.get("body_matched_studio_terms", ""))

        body_event_present = event_count > 0
        relevance_score = 0
        relevance_score += 45 if body_event_present else 0
        relevance_score += min(event_count, 6) * 5
        relevance_score += 15 if title_event_count else 0
        relevance_score += min(len(studio_terms), 4) * 4
        relevance_score += 10 if chars >= 600 else 0
        relevance_score += min(experience_count, 5) * 2
        if mixed_count >= 5 and event_count <= 1:
            relevance_score -= 15
        if not body_event_present:
            relevance_score = min(relevance_score, 45)

        experience_depth = (
            length_score(chars)
            + min(experience_count * 4, 25)
            + min(detail_count * 2, 20)
            + min(reflection_count * 3, 15)
            + min(len(studio_terms) * 3, 10)
        )
        emotional_score = (
            min(positive_count * 4, 45)
            + min(negative_count * 3, 20)
            + min(reflection_count * 2, 20)
            + min(exclamation_count * 3, 15)
        )

        row = {
            "mention_id": mention_id,
            "title": title,
            "published_at": raw_row.get("published_at", ""),
            "body_text_chars": chars,
            "body_event_keyword_count": event_count,
            "title_event_keyword_count": title_event_count,
            "body_event_keyword_present": body_event_present,
            "body_relevance_score": clamp(relevance_score),
            "body_matched_studio_terms": base.get("body_matched_studio_terms", ""),
            "primary_body_theme": base.get("primary_body_theme", "unclear"),
            "experience_keyword_count": experience_count,
            "space_or_detail_keyword_count": detail_count,
            "reflection_keyword_count": reflection_count,
            "positive_affect_keyword_count": positive_count,
            "negative_affect_keyword_count": negative_count,
            "promo_keyword_count": promo_count,
            "mixed_topic_keyword_count": mixed_count,
            "experience_depth_score": clamp(experience_depth),
            "emotional_intensity_score": clamp(emotional_score),
            "topic_mixing_risk": topic_mixing_risk(mixed_count, event_count, chars),
        }
        row["body_relevance_level"] = relevance_level(row)
        row["experience_depth_label"] = depth_label(int(row["experience_depth_score"]))
        row["sentiment_tone"] = sentiment_tone(
            int(row["positive_affect_keyword_count"]),
            int(row["negative_affect_keyword_count"]),
            int(row["emotional_intensity_score"]),
        )
        row["interpretive_post_type"] = interpret_post_type(row)
        row["manual_review_recommended"] = (
            str(row["body_relevance_level"]).startswith("needs_review")
            or str(row["topic_mixing_risk"]) == "high"
            or str(row["interpretive_post_type"]) == "mixed_context_event_mention"
        )
        rows.append(row)

    return pd.DataFrame(rows)


def bool_sum(series: pd.Series) -> int:
    return int(series.astype(str).str.lower().eq("true").sum())


def build_post_type_summary(features: pd.DataFrame) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    return (
        features.groupby("interpretive_post_type", dropna=False)
        .agg(
            mention_count=("mention_id", "count"),
            average_relevance_score=("body_relevance_score", "mean"),
            average_depth_score=("experience_depth_score", "mean"),
            average_emotional_intensity_score=("emotional_intensity_score", "mean"),
            manual_review_recommended_count=("manual_review_recommended", bool_sum),
        )
        .round(2)
        .reset_index()
        .sort_values(["mention_count", "interpretive_post_type"], ascending=[False, True])
    )


def build_quality_summary(features: pd.DataFrame) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    grouped = (
        features.groupby(
            ["body_relevance_level", "experience_depth_label", "sentiment_tone"],
            dropna=False,
        )
        .agg(
            mention_count=("mention_id", "count"),
            manual_review_recommended_count=("manual_review_recommended", bool_sum),
            average_body_text_chars=("body_text_chars", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values(["mention_count", "body_relevance_level"], ascending=[False, True])
    )
    return grouped


def public_feature_columns(features: pd.DataFrame) -> pd.DataFrame:
    public_columns = [
        "mention_id",
        "published_at",
        "body_text_chars",
        "body_event_keyword_count",
        "body_relevance_score",
        "body_relevance_level",
        "experience_depth_score",
        "experience_depth_label",
        "emotional_intensity_score",
        "sentiment_tone",
        "topic_mixing_risk",
        "interpretive_post_type",
        "primary_body_theme",
        "body_matched_studio_terms",
        "manual_review_recommended",
    ]
    return features[public_columns].copy()


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(lines)


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def write_report(features: pd.DataFrame, post_type_summary: pd.DataFrame, quality_summary: pd.DataFrame) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    total = len(features)
    strong_or_basic = int(
        features["body_relevance_level"].isin(["confirmed_body_strong", "confirmed_body_basic"]).sum()
    )
    manual_review = bool_sum(features["manual_review_recommended"])
    high_depth = int(features["experience_depth_label"].eq("high_depth").sum())
    positive_or_more = int(features["sentiment_tone"].isin(["positive", "very_positive"]).sum())

    report = f"""# Naver Blog Body Deep Feature Report

Generated: {generated_at}

## Purpose

Use full Naver Blog body text to judge whether each confirmed post is a real 2026 Yeonhui Yoga Week mention,
how deeply the author wrote about the experience, and whether the post looks like a thin or mixed-context mention.

## Inputs

- Raw body CSV: `{RAW_BODY.relative_to(ROOT)}`
- Basic body features: `{BODY_FEATURES_INTERNAL.relative_to(ROOT)}`

## Outputs

- Internal deep features: `{INTERIM_OUTPUT.relative_to(ROOT)}`
- Public deep features without source URL/body text: `{PUBLIC_FEATURES.relative_to(ROOT)}`
- Public post type summary: `{PUBLIC_POST_TYPE_SUMMARY.relative_to(ROOT)}`
- Public quality summary: `{PUBLIC_QUALITY_SUMMARY.relative_to(ROOT)}`

## Result

- Body rows analyzed: {total}
- Strong/basic body-confirmed rows: {strong_or_basic}
- High-depth participant/context rows: {high_depth}
- Positive or very positive tone rows: {positive_or_more}
- Manual review recommended rows: {manual_review}

## Post Type Summary

{markdown_table(post_type_summary)}

## Quality Summary

{markdown_table(quality_summary.head(20))}

## Interpretation Notes

These scores are transparent rule-based proxies. They are intended for filtering, triage, and comparison,
not as a final human sentiment judgment. Raw body text is kept out of public outputs.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    if not RAW_BODY.exists():
        raise FileNotFoundError(f"Missing raw body CSV: {RAW_BODY}")
    if not BODY_FEATURES_INTERNAL.exists():
        raise FileNotFoundError(f"Missing body features CSV: {BODY_FEATURES_INTERNAL}")

    raw = pd.read_csv(RAW_BODY, dtype=str, keep_default_na=False)
    base_features = pd.read_csv(BODY_FEATURES_INTERNAL, dtype=str, keep_default_na=False)
    features = build_deep_features(raw, base_features)
    post_type_summary = build_post_type_summary(features)
    quality_summary = build_quality_summary(features)

    write_csv(features, INTERIM_OUTPUT)
    write_csv(public_feature_columns(features), PUBLIC_FEATURES)
    write_csv(post_type_summary, PUBLIC_POST_TYPE_SUMMARY)
    write_csv(quality_summary, PUBLIC_QUALITY_SUMMARY)
    write_report(features, post_type_summary, quality_summary)

    print(f"Wrote {INTERIM_OUTPUT}")
    print(f"Wrote {PUBLIC_FEATURES}")
    print(f"Wrote {PUBLIC_POST_TYPE_SUMMARY}")
    print(f"Wrote {PUBLIC_QUALITY_SUMMARY}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Body rows analyzed: {len(features)}")
    if not features.empty:
        print(
            "Manual review recommended rows: "
            f"{bool_sum(features['manual_review_recommended'])}"
        )


if __name__ == "__main__":
    main()
