from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_EXTERNAL_DIR = ROOT / "data" / "raw" / "external_web"
INTERIM_EXTERNAL_DIR = ROOT / "data" / "interim" / "external_web"
REPORT_EXTERNAL_DIR = ROOT / "reports" / "external_web"
ANALYSIS_PUBLIC_DIR = ROOT / "data" / "processed" / "analysis" / "public"
EXTERNAL_DIR = ROOT / "data" / "external"

NAVER_RAW = RAW_EXTERNAL_DIR / "naver_blog_mentions_raw.csv"
YOUTUBE_RAW = RAW_EXTERNAL_DIR / "youtube_mentions_raw.csv"
REVIEW_QUEUE = INTERIM_EXTERNAL_DIR / "viral_mentions_review_queue.csv"
REPORT_PATH = REPORT_EXTERNAL_DIR / "viral_mentions_review_queue_report.md"

EVENT_KEYWORDS = [
    "연희요가위크",
    "연희 요가 위크",
    "연희요가축제",
    "연희 요가 축제",
]


def compact_spaces(value: object) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def normalize_for_match(value: object) -> str:
    return re.sub(r"\s+", "", str(value).lower())


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def load_studio_terms() -> list[str]:
    terms: set[str] = set()
    studio_metrics = ANALYSIS_PUBLIC_DIR / "studio_hype_metrics.csv"
    if studio_metrics.exists():
        frame = pd.read_csv(studio_metrics, dtype=str, keep_default_na=False)
        if "studio_key" in frame.columns:
            terms.update(compact_spaces(value) for value in frame["studio_key"] if compact_spaces(value))

    studio_locations = EXTERNAL_DIR / "studio_locations_public.csv"
    if studio_locations.exists():
        frame = pd.read_csv(studio_locations, dtype=str, keep_default_na=False)
        for column in ["studio_key", "normalized_studio_key", "display_name"]:
            if column in frame.columns:
                terms.update(compact_spaces(value) for value in frame[column] if compact_spaces(value))

    extra_terms = {
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
        "비전스트롤",
        "파츄코파라다이스",
        "궁동산",
        "궁둥산",
    }
    terms.update(extra_terms)
    return sorted(terms, key=lambda item: (-len(item), item))


def event_keyword_present(text: str) -> bool:
    normalized = normalize_for_match(text)
    return any(normalize_for_match(keyword) in normalized for keyword in EVENT_KEYWORDS)


def matched_terms(text: str, terms: list[str]) -> str:
    normalized = normalize_for_match(text)
    matches = [term for term in terms if normalize_for_match(term) in normalized]
    return ";".join(dict.fromkeys(matches))


def first_non_empty(values: pd.Series) -> str:
    for value in values:
        text = compact_spaces(value)
        if text:
            return text
    return ""


def min_numeric(values: pd.Series) -> str:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().any():
        return str(int(numeric.min()))
    return ""


def join_unique(values: pd.Series) -> str:
    unique = [compact_spaces(value) for value in values if compact_spaces(value)]
    return ";".join(dict.fromkeys(unique))


def normalize_naver(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    output = pd.DataFrame(
        {
            "platform": "naver_blog",
            "source_url": raw.get("link", ""),
            "source_public_name": raw.get("blogger_name", ""),
            "source_public_id": "",
            "source_profile_url": raw.get("blogger_link", ""),
            "published_at": raw.get("post_date", ""),
            "title": raw.get("title", ""),
            "description": raw.get("description", ""),
            "search_query": raw.get("query", ""),
            "query_rank": raw.get("query_rank", ""),
            "view_count": "",
            "like_count": "",
            "comment_count": "",
            "channel_subscriber_count": "",
            "raw_source_file": str(NAVER_RAW.relative_to(ROOT)),
        }
    )
    return output


def normalize_youtube(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    output = pd.DataFrame(
        {
            "platform": "youtube",
            "source_url": raw.get("video_url", ""),
            "source_public_name": raw.get("channel_title", ""),
            "source_public_id": raw.get("channel_id", ""),
            "source_profile_url": raw.get("channel_id", "").map(
                lambda channel_id: f"https://www.youtube.com/channel/{channel_id}" if compact_spaces(channel_id) else ""
            ),
            "published_at": raw.get("published_at", ""),
            "title": raw.get("title", ""),
            "description": raw.get("description", ""),
            "search_query": raw.get("query", ""),
            "query_rank": raw.get("query_rank", ""),
            "view_count": raw.get("view_count", ""),
            "like_count": raw.get("like_count", ""),
            "comment_count": raw.get("comment_count", ""),
            "channel_subscriber_count": raw.get("channel_subscriber_count", ""),
            "raw_source_file": str(YOUTUBE_RAW.relative_to(ROOT)),
        }
    )
    return output


def build_review_queue() -> pd.DataFrame:
    raw_frames = [
        normalize_naver(read_csv_if_exists(NAVER_RAW)),
        normalize_youtube(read_csv_if_exists(YOUTUBE_RAW)),
    ]
    combined = pd.concat([frame for frame in raw_frames if not frame.empty], ignore_index=True)
    if combined.empty:
        return pd.DataFrame()

    grouped = (
        combined.groupby(["platform", "source_url"], dropna=False)
        .agg(
            source_public_name=("source_public_name", first_non_empty),
            source_public_id=("source_public_id", first_non_empty),
            source_profile_url=("source_profile_url", first_non_empty),
            published_at=("published_at", first_non_empty),
            title=("title", first_non_empty),
            description=("description", first_non_empty),
            search_queries=("search_query", join_unique),
            query_count=("search_query", lambda values: len(set(compact_spaces(value) for value in values if compact_spaces(value)))),
            best_query_rank=("query_rank", min_numeric),
            view_count=("view_count", first_non_empty),
            like_count=("like_count", first_non_empty),
            comment_count=("comment_count", first_non_empty),
            channel_subscriber_count=("channel_subscriber_count", first_non_empty),
            raw_source_files=("raw_source_file", join_unique),
            raw_row_count=("platform", "count"),
        )
        .reset_index()
    )

    studio_terms = load_studio_terms()
    text_for_matching = (
        grouped["title"].fillna("")
        + " "
        + grouped["description"].fillna("")
        + " "
        + grouped["source_public_name"].fillna("")
    )
    grouped["event_keyword_present"] = text_for_matching.map(event_keyword_present)
    grouped["matched_studio_terms"] = text_for_matching.map(lambda text: matched_terms(text, studio_terms))
    grouped["needs_manual_relevance_review"] = ~grouped["event_keyword_present"]
    grouped["source_identity_handling"] = (
        "raw/interim에는 공개 출처명과 공개 출처 URL을 보존하되, public 산출물에서는 필요 시 익명화"
    )
    grouped.insert(0, "mention_id", [f"mention_{index:04d}" for index in range(1, len(grouped) + 1)])

    ordered_columns = [
        "mention_id",
        "platform",
        "source_url",
        "source_public_name",
        "source_public_id",
        "source_profile_url",
        "published_at",
        "title",
        "description",
        "search_queries",
        "query_count",
        "best_query_rank",
        "event_keyword_present",
        "matched_studio_terms",
        "needs_manual_relevance_review",
        "view_count",
        "like_count",
        "comment_count",
        "channel_subscriber_count",
        "raw_row_count",
        "raw_source_files",
        "source_identity_handling",
    ]
    return grouped[ordered_columns].sort_values(["platform", "published_at", "source_url"], ascending=[True, False, True])


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def write_report(frame: pd.DataFrame) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    platform_counts = Counter(frame["platform"]) if not frame.empty else Counter()
    manual_review_count = int(frame["needs_manual_relevance_review"].astype(bool).sum()) if not frame.empty else 0
    platform_table = "\n".join(f"| {platform} | {count} |" for platform, count in sorted(platform_counts.items()))
    report = f"""# Viral Mentions Review Queue Report

Generated: {generated_at}

## Purpose

Build an internal review queue from Naver Blog and YouTube raw collection files.

## Inputs

- Naver raw: `{NAVER_RAW.relative_to(ROOT)}`
- YouTube raw: `{YOUTUBE_RAW.relative_to(ROOT)}`

## Output

- Review queue CSV: `{REVIEW_QUEUE.relative_to(ROOT)}`
- Unique mention rows: {len(frame)}
- Rows needing manual relevance review: {manual_review_count}

## Platform Counts

| platform | rows |
|---|---:|
{platform_table}

## Handling Rule

The review queue keeps public source names, public source IDs, and source URLs for internal provenance checks.
Future public outputs should mask or aggregate individual source identities unless explicit publication is needed and reviewed.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    frame = build_review_queue()
    write_csv(frame, REVIEW_QUEUE)
    write_report(frame)
    print(f"Wrote {REVIEW_QUEUE}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Rows: {len(frame)}")
    if not frame.empty:
        print(f"Needs manual relevance review: {int(frame['needs_manual_relevance_review'].astype(bool).sum())}")


if __name__ == "__main__":
    main()
