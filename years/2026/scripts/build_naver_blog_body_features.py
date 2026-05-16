from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_BODY = ROOT / "data" / "raw" / "external_web" / "naver_blog_bodies_raw.csv"
ANALYSIS_PUBLIC_DIR = ROOT / "data" / "processed" / "analysis" / "public"
INTERIM_EXTERNAL_DIR = ROOT / "data" / "interim" / "external_web"
REPORT_EXTERNAL_DIR = ROOT / "reports" / "external_web"
EXTERNAL_DIR = ROOT / "data" / "external"

BODY_FEATURES_INTERNAL = INTERIM_EXTERNAL_DIR / "naver_blog_body_features_internal.csv"
BODY_THEME_SUMMARY_PUBLIC = ANALYSIS_PUBLIC_DIR / "yeonhui_yoga_week_naver_blog_body_theme_summary.csv"
BODY_STUDIO_SUMMARY_PUBLIC = ANALYSIS_PUBLIC_DIR / "yeonhui_yoga_week_naver_blog_body_studio_summary.csv"
REPORT_PATH = REPORT_EXTERNAL_DIR / "naver_blog_body_feature_report.md"

EVENT_CANONICAL = "연희요가위크"
STUDIO_TERM_ALIASES = {
    "빅블루": "빅블루요가",
    "숨 명상센터": "숨명상센터",
    "대저택 프라이빗": "대저택프라이빗",
    "비전스트롤": "비전스트롤 콜라보",
}

THEME_KEYWORDS = {
    "participant_review": ["후기", "다녀", "참여", "체험", "수련", "갔다", "들었다", "느꼈"],
    "official_or_studio_promo": ["모집", "예약", "티켓", "신청", "안내", "공지", "오픈", "진행합니다"],
    "class_experience": ["수업", "클래스", "선생님", "강사", "매트", "동작", "호흡"],
    "space_experience": ["공간", "장소", "연남장", "연희정음", "카페", "분위기", "루프탑", "옥상"],
    "community_or_social": ["차담", "커뮤니티", "소통", "함께", "사람들", "대화"],
    "wellness_recovery": ["명상", "회복", "이완", "휴식", "마음", "몸", "힐링"],
    "visual_or_lifestyle": ["사진", "룩", "구디백", "브이로그", "코디", "언박싱"],
}


def compact_spaces(value: object) -> str:
    return " ".join(("" if value is None else str(value)).split())


def normalize_for_match(value: object) -> str:
    return re.sub(r"\s+", "", str(value).lower())


def load_studio_terms() -> list[str]:
    terms: set[str] = set()
    for path, columns in [
        (ANALYSIS_PUBLIC_DIR / "studio_hype_metrics.csv", ["studio_key"]),
        (EXTERNAL_DIR / "studio_locations_public.csv", ["studio_key", "normalized_studio_key", "display_name"]),
    ]:
        if not path.exists():
            continue
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        for column in columns:
            if column in frame.columns:
                terms.update(compact_spaces(value) for value in frame[column] if compact_spaces(value))

    terms.update(
        {
            "빅블루",
            "빅블루요가",
            "마인드플로우",
            "마이트리",
            "시이작",
            "연희정음",
            "연남장",
            "너울너울",
            "무릉",
            "숨명상센터",
            "숨 명상센터",
            "바운드하우스",
            "대저택프라이빗",
            "대저택 프라이빗",
            "비전스트롤",
            "파츄코파라다이스",
            "궁동산",
            "궁둥산",
        }
    )
    return sorted(terms, key=lambda item: (-len(item), item))


def matched_terms(text: str, terms: list[str]) -> str:
    normalized = normalize_for_match(text)
    matches: list[str] = []
    for term in terms:
        if normalize_for_match(term) not in normalized:
            continue
        matches.append(STUDIO_TERM_ALIASES.get(term, term))
    return ";".join(dict.fromkeys(matches))


def keyword_count(text: str, keywords: list[str]) -> int:
    normalized = normalize_for_match(text)
    return sum(normalized.count(normalize_for_match(keyword)) for keyword in keywords)


def theme_flags(text: str) -> dict[str, object]:
    flags: dict[str, object] = {}
    for theme, keywords in THEME_KEYWORDS.items():
        count = keyword_count(text, keywords)
        flags[f"{theme}_keyword_count"] = count
        flags[f"{theme}_flag"] = count > 0
    return flags


def classify_primary_theme(row: pd.Series) -> str:
    scores = {
        theme: int(row.get(f"{theme}_keyword_count", 0) or 0)
        for theme in THEME_KEYWORDS
    }
    if not scores or max(scores.values()) == 0:
        return "unclear"
    priority = [
        "participant_review",
        "class_experience",
        "space_experience",
        "wellness_recovery",
        "community_or_social",
        "visual_or_lifestyle",
        "official_or_studio_promo",
    ]
    return max(priority, key=lambda theme: (scores.get(theme, 0), -priority.index(theme)))


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    studio_terms = load_studio_terms()
    rows: list[dict[str, object]] = []
    for _, row in raw.iterrows():
        body = str(row.get("body_text", ""))
        title = str(row.get("title", ""))
        combined = f"{title}\n{body}"
        event_count = normalize_for_match(body).count(EVENT_CANONICAL)
        feature = {
            "mention_id": row.get("mention_id", ""),
            "title": title,
            "source_public_name": row.get("source_public_name", ""),
            "published_at": row.get("published_at", ""),
            "body_fetch_status": row.get("body_fetch_status", ""),
            "body_text_chars": row.get("body_text_chars", ""),
            "body_text_lines": row.get("body_text_lines", ""),
            "body_event_keyword_count": event_count,
            "body_event_keyword_present": event_count > 0,
            "body_matched_studio_terms": matched_terms(combined, studio_terms),
            "body_noise_risk": not (event_count > 0),
        }
        feature.update(theme_flags(body))
        rows.append(feature)

    features = pd.DataFrame(rows)
    if features.empty:
        return features
    features["primary_body_theme"] = features.apply(classify_primary_theme, axis=1)
    return features


def bool_sum(series: pd.Series) -> int:
    return int(series.astype(str).str.lower().eq("true").sum())


def build_theme_summary(features: pd.DataFrame) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    return (
        features.groupby("primary_body_theme", dropna=False)
        .agg(
            mention_count=("mention_id", "count"),
            body_event_keyword_present_count=("body_event_keyword_present", bool_sum),
            average_body_text_chars=("body_text_chars", lambda values: round(pd.to_numeric(values, errors="coerce").mean(), 2)),
        )
        .reset_index()
        .sort_values(["mention_count", "primary_body_theme"], ascending=[False, True])
    )


def explode_studio_terms(features: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in features.iterrows():
        terms = [term for term in str(row.get("body_matched_studio_terms", "")).split(";") if compact_spaces(term)]
        if not terms:
            terms = ["UNMATCHED"]
        for term in terms:
            rows.append(
                {
                    "body_matched_studio_term": term,
                    "mention_id": row.get("mention_id", ""),
                    "primary_body_theme": row.get("primary_body_theme", ""),
                    "body_event_keyword_present": row.get("body_event_keyword_present", False),
                }
            )
    return pd.DataFrame(rows)


def build_studio_summary(features: pd.DataFrame) -> pd.DataFrame:
    exploded = explode_studio_terms(features)
    if exploded.empty:
        return pd.DataFrame()
    return (
        exploded.groupby("body_matched_studio_term", dropna=False)
        .agg(
            mention_count=("mention_id", "nunique"),
            body_event_keyword_present_count=("body_event_keyword_present", bool_sum),
            theme_count=("primary_body_theme", "nunique"),
        )
        .reset_index()
        .sort_values(["mention_count", "body_matched_studio_term"], ascending=[False, True])
    )


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def write_report(features: pd.DataFrame, theme_summary: pd.DataFrame, studio_summary: pd.DataFrame) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    total = len(features)
    body_event_count = bool_sum(features["body_event_keyword_present"]) if not features.empty else 0
    noise_risk = bool_sum(features["body_noise_risk"]) if not features.empty else 0
    theme_lines = "\n".join(
        f"| {row.primary_body_theme} | {row.mention_count} | {row.body_event_keyword_present_count} |"
        for row in theme_summary.itertuples(index=False)
    )
    studio_lines = "\n".join(
        f"| {row.body_matched_studio_term} | {row.mention_count} |"
        for row in studio_summary.head(20).itertuples(index=False)
    )
    report = f"""# Naver Blog Body Feature Report

Generated: {generated_at}

## Purpose

Use fetched Naver Blog body text to improve noise handling and qualitative interpretation.

## Inputs

- Raw body CSV: `{RAW_BODY.relative_to(ROOT)}`

## Outputs

- Internal body features: `{BODY_FEATURES_INTERNAL.relative_to(ROOT)}`
- Public theme summary: `{BODY_THEME_SUMMARY_PUBLIC.relative_to(ROOT)}`
- Public studio/body summary: `{BODY_STUDIO_SUMMARY_PUBLIC.relative_to(ROOT)}`

## Result

- Body rows: {total}
- Body rows containing `연희요가위크`: {body_event_count}
- Body rows flagged as noise risk: {noise_risk}

## Theme Summary

| primary_body_theme | mention_count | body_event_keyword_present_count |
|---|---:|---:|
{theme_lines}

## Body Studio/Place Summary

| body_matched_studio_term | mention_count |
|---|---:|
{studio_lines}

## Noise Handling

Rows where the title/snippet matched but body text does not contain `연희요가위크` are not automatically discarded.
They are flagged as `body_noise_risk=true` because the body extraction may miss image-only text or the event name may appear only in the title.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    if not RAW_BODY.exists():
        raise FileNotFoundError(f"Missing raw body CSV: {RAW_BODY}")
    raw = pd.read_csv(RAW_BODY, dtype=str, keep_default_na=False)
    features = build_features(raw)
    theme_summary = build_theme_summary(features)
    studio_summary = build_studio_summary(features)

    write_csv(features, BODY_FEATURES_INTERNAL)
    write_csv(theme_summary, BODY_THEME_SUMMARY_PUBLIC)
    write_csv(studio_summary, BODY_STUDIO_SUMMARY_PUBLIC)
    write_report(features, theme_summary, studio_summary)

    print(f"Wrote {BODY_FEATURES_INTERNAL}")
    print(f"Wrote {BODY_THEME_SUMMARY_PUBLIC}")
    print(f"Wrote {BODY_STUDIO_SUMMARY_PUBLIC}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Body rows: {len(features)}")
    if not features.empty:
        print(f"Body rows containing event keyword: {bool_sum(features['body_event_keyword_present'])}")
        print(f"Body noise risk rows: {bool_sum(features['body_noise_risk'])}")


if __name__ == "__main__":
    main()
