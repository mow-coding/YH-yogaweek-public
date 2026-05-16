from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INTERIM_EXTERNAL_DIR = ROOT / "data" / "interim" / "external_web"
ANALYSIS_PUBLIC_DIR = ROOT / "data" / "processed" / "analysis" / "public"
REPORT_EXTERNAL_DIR = ROOT / "reports" / "external_web"

REVIEW_QUEUE = INTERIM_EXTERNAL_DIR / "viral_mentions_review_queue.csv"
CHECKED_INTERNAL = INTERIM_EXTERNAL_DIR / "yeonhui_yoga_week_mentions_checked.csv"
CONFIRMED_INTERNAL = INTERIM_EXTERNAL_DIR / "yeonhui_yoga_week_mentions_confirmed_internal.csv"
PUBLIC_CONFIRMED = ANALYSIS_PUBLIC_DIR / "yeonhui_yoga_week_viral_mentions_public.csv"
PUBLIC_PLATFORM_SUMMARY = ANALYSIS_PUBLIC_DIR / "yeonhui_yoga_week_viral_platform_summary.csv"
PUBLIC_STUDIO_SUMMARY = ANALYSIS_PUBLIC_DIR / "yeonhui_yoga_week_viral_studio_summary.csv"
REPORT_PATH = REPORT_EXTERNAL_DIR / "yeonhui_yoga_week_mention_filter_report.md"

PLANNING_START_DATE = pd.Timestamp("2026-02-01")
EVENT_NAME_CANONICAL = "연희요가위크"
STUDIO_TERM_ALIASES = {
    "빅블루": "빅블루요가",
    "숨 명상센터": "숨명상센터",
    "대저택 프라이빗": "대저택프라이빗",
    "비전스트롤": "비전스트롤 콜라보",
}


def compact_spaces(value: object) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def normalize_for_match(value: object) -> str:
    return re.sub(r"\s+", "", str(value).lower())


def parse_date(value: object) -> pd.Timestamp | None:
    text = compact_spaces(value)
    if not text:
        return None
    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(parsed):
        parsed = pd.to_datetime(text[:10], errors="coerce")
    if pd.isna(parsed):
        return None
    timestamp = pd.Timestamp(parsed)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert(None)
    return timestamp.normalize()


def direct_event_keyword_flags(title: object, description: object) -> tuple[bool, bool, bool]:
    normalized_title = normalize_for_match(title)
    normalized_description = normalize_for_match(description)
    title_has = EVENT_NAME_CANONICAL in normalized_title
    description_has = EVENT_NAME_CANONICAL in normalized_description
    return title_has or description_has, title_has, description_has


def classify_row(row: pd.Series) -> dict[str, object]:
    published_date = parse_date(row.get("published_at", ""))
    event_keyword, title_has_keyword, description_has_keyword = direct_event_keyword_flags(
        row.get("title", ""),
        row.get("description", ""),
    )

    if published_date is None:
        date_status = "missing_or_unparseable"
        date_ok = False
    elif published_date < PLANNING_START_DATE:
        date_status = "before_2026_02_01"
        date_ok = False
    else:
        date_status = "on_or_after_2026_02_01"
        date_ok = True

    if event_keyword and date_ok:
        classification = "confirmed_2026_yeonhui_yoga_week"
        needs_manual_review = False
    elif event_keyword and not date_ok:
        classification = "event_keyword_but_date_not_valid"
        needs_manual_review = True
    else:
        classification = "not_confirmed_no_direct_event_keyword"
        needs_manual_review = True

    if title_has_keyword and description_has_keyword and date_ok:
        confidence_score = 100
    elif title_has_keyword and date_ok:
        confidence_score = 95
    elif description_has_keyword and date_ok:
        confidence_score = 90
    else:
        confidence_score = 0

    evidence_parts = []
    if title_has_keyword:
        evidence_parts.append("title")
    if description_has_keyword:
        evidence_parts.append("description")

    return {
        "published_date": published_date.date().isoformat() if published_date is not None else "",
        "date_status": date_status,
        "direct_event_keyword": event_keyword,
        "event_keyword_in_title": title_has_keyword,
        "event_keyword_in_description": description_has_keyword,
        "confirmed_event_mention": classification == "confirmed_2026_yeonhui_yoga_week",
        "mention_classification": classification,
        "event_confidence_score": confidence_score,
        "needs_manual_review_after_filter": needs_manual_review,
        "confirmation_evidence_fields": ";".join(evidence_parts),
        "filter_rule": "title_or_description_contains_연희요가위크_and_published_date_on_or_after_2026-02-01",
    }


def build_checked_frame(queue: pd.DataFrame) -> pd.DataFrame:
    checks = pd.DataFrame([classify_row(row) for _, row in queue.iterrows()])
    checked = pd.concat([queue.reset_index(drop=True), checks], axis=1)
    checked = checked.sort_values(
        ["confirmed_event_mention", "event_confidence_score", "published_date", "platform"],
        ascending=[False, False, False, True],
    )
    return checked


def build_public_confirmed(confirmed: pd.DataFrame) -> pd.DataFrame:
    source_keys = (
        confirmed["platform"].fillna("")
        + "|"
        + confirmed["source_public_name"].fillna("")
        + "|"
        + confirmed["source_public_id"].fillna("")
        + "|"
        + confirmed["source_profile_url"].fillna("")
    )
    source_map = {
        key: f"external_source_{index:04d}"
        for index, key in enumerate(sorted(set(source_keys)), start=1)
    }

    output = pd.DataFrame(
        {
            "mention_public_id": [f"viral_mention_{index:04d}" for index in range(1, len(confirmed) + 1)],
            "platform": confirmed["platform"],
            "published_date": confirmed["published_date"],
            "title": confirmed["title"],
            "description": confirmed["description"],
            "source_public_anonymous_id": source_keys.map(source_map),
            "search_queries": confirmed["search_queries"],
            "query_count": confirmed["query_count"],
            "best_query_rank": confirmed["best_query_rank"],
            "matched_studio_terms": confirmed["matched_studio_terms"],
            "view_count": confirmed["view_count"],
            "like_count": confirmed["like_count"],
            "comment_count": confirmed["comment_count"],
            "channel_subscriber_count": confirmed["channel_subscriber_count"],
            "event_confidence_score": confirmed["event_confidence_score"],
            "confirmation_evidence_fields": confirmed["confirmation_evidence_fields"],
            "source_url_internal_only": "yes",
            "source_identity_handling": "source name, source id, profile url, and exact url retained only in raw/interim files",
        }
    )
    return output


def numeric_sum(series: pd.Series) -> int:
    return int(pd.to_numeric(series, errors="coerce").fillna(0).sum())


def build_platform_summary(public_confirmed: pd.DataFrame) -> pd.DataFrame:
    if public_confirmed.empty:
        return pd.DataFrame(
            columns=[
                "platform",
                "confirmed_mention_count",
                "anonymous_source_count",
                "total_view_count",
                "total_like_count",
                "total_comment_count",
            ]
        )
    return (
        public_confirmed.groupby("platform", dropna=False)
        .agg(
            confirmed_mention_count=("mention_public_id", "count"),
            anonymous_source_count=("source_public_anonymous_id", "nunique"),
            total_view_count=("view_count", numeric_sum),
            total_like_count=("like_count", numeric_sum),
            total_comment_count=("comment_count", numeric_sum),
        )
        .reset_index()
    )


def explode_studio_terms(public_confirmed: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in public_confirmed.iterrows():
        terms = [term for term in str(row.get("matched_studio_terms", "")).split(";") if compact_spaces(term)]
        if not terms:
            terms = ["UNMATCHED"]
        for term in terms:
            canonical_term = STUDIO_TERM_ALIASES.get(term, term)
            rows.append(
                {
                    "matched_studio_term": canonical_term,
                    "mention_public_id": row["mention_public_id"],
                    "platform": row["platform"],
                    "source_public_anonymous_id": row["source_public_anonymous_id"],
                    "view_count": row.get("view_count", ""),
                    "like_count": row.get("like_count", ""),
                    "comment_count": row.get("comment_count", ""),
                }
            )
    return pd.DataFrame(rows)


def build_studio_summary(public_confirmed: pd.DataFrame) -> pd.DataFrame:
    exploded = explode_studio_terms(public_confirmed)
    if exploded.empty:
        return pd.DataFrame(
            columns=[
                "matched_studio_term",
                "confirmed_mention_count",
                "platform_count",
                "anonymous_source_count",
                "total_view_count",
                "total_like_count",
                "total_comment_count",
            ]
        )
    return (
        exploded.groupby("matched_studio_term", dropna=False)
        .agg(
            confirmed_mention_count=("mention_public_id", "nunique"),
            platform_count=("platform", "nunique"),
            anonymous_source_count=("source_public_anonymous_id", "nunique"),
            total_view_count=("view_count", numeric_sum),
            total_like_count=("like_count", numeric_sum),
            total_comment_count=("comment_count", numeric_sum),
        )
        .reset_index()
        .sort_values(["confirmed_mention_count", "total_view_count"], ascending=[False, False])
    )


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def write_report(checked: pd.DataFrame, confirmed: pd.DataFrame, public_confirmed: pd.DataFrame) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    classification_counts = Counter(checked["mention_classification"])
    platform_counts = Counter(confirmed["platform"]) if not confirmed.empty else Counter()
    classification_table = "\n".join(
        f"| {classification} | {count} |" for classification, count in sorted(classification_counts.items())
    )
    platform_table = "\n".join(
        f"| {platform} | {count} |" for platform, count in sorted(platform_counts.items())
    )
    report = f"""# Yeonhui Yoga Week Mention Filter Report

Generated: {generated_at}

## Purpose

Filter the external viral mention review queue to confirmed 2026 Yeonhui Yoga Week mentions.

## Strict Confirmation Rule

A row is confirmed only when both conditions are true:

1. `title` or `description` directly contains `연희요가위크` after whitespace normalization.
2. `published_at` is on or after `2026-02-01`, the month when internal planning first started.

Search query text is not used as confirmation evidence.
Studio/place names alone are not used as confirmation evidence.

## Inputs

- Review queue: `{REVIEW_QUEUE.relative_to(ROOT)}`

## Outputs

- Internal checked CSV: `{CHECKED_INTERNAL.relative_to(ROOT)}`
- Internal confirmed CSV: `{CONFIRMED_INTERNAL.relative_to(ROOT)}`
- Public anonymized confirmed CSV: `{PUBLIC_CONFIRMED.relative_to(ROOT)}`
- Public platform summary: `{PUBLIC_PLATFORM_SUMMARY.relative_to(ROOT)}`
- Public studio summary: `{PUBLIC_STUDIO_SUMMARY.relative_to(ROOT)}`

## Result

- Input candidate mentions: {len(checked)}
- Confirmed event mentions: {len(confirmed)}
- Public confirmed rows: {len(public_confirmed)}
- Not confirmed / needs review: {int((~checked["confirmed_event_mention"].astype(bool)).sum())}

## Classification Counts

| classification | rows |
|---|---:|
{classification_table}

## Confirmed Platform Counts

| platform | confirmed_rows |
|---|---:|
{platform_table}

## Public Identity Handling

Internal files retain public source names, public IDs, profile URLs, and exact source URLs for provenance checks.
The public confirmed CSV replaces source identity with `external_source_####` and omits exact source URLs.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    if not REVIEW_QUEUE.exists():
        raise FileNotFoundError(f"Missing review queue: {REVIEW_QUEUE}")

    queue = pd.read_csv(REVIEW_QUEUE, dtype=str, keep_default_na=False)
    checked = build_checked_frame(queue)
    confirmed = checked[checked["confirmed_event_mention"].astype(bool)].copy()
    public_confirmed = build_public_confirmed(confirmed)
    platform_summary = build_platform_summary(public_confirmed)
    studio_summary = build_studio_summary(public_confirmed)

    write_csv(checked, CHECKED_INTERNAL)
    write_csv(confirmed, CONFIRMED_INTERNAL)
    write_csv(public_confirmed, PUBLIC_CONFIRMED)
    write_csv(platform_summary, PUBLIC_PLATFORM_SUMMARY)
    write_csv(studio_summary, PUBLIC_STUDIO_SUMMARY)
    write_report(checked, confirmed, public_confirmed)

    print(f"Wrote {CHECKED_INTERNAL}")
    print(f"Wrote {CONFIRMED_INTERNAL}")
    print(f"Wrote {PUBLIC_CONFIRMED}")
    print(f"Wrote {PUBLIC_PLATFORM_SUMMARY}")
    print(f"Wrote {PUBLIC_STUDIO_SUMMARY}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Input rows: {len(checked)}")
    print(f"Confirmed rows: {len(confirmed)}")
    print(f"Not confirmed / needs review: {int((~checked['confirmed_event_mention'].astype(bool)).sum())}")


if __name__ == "__main__":
    main()
