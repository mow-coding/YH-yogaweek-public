from __future__ import annotations

import argparse
import csv
import html
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]
SECRETS_DIR = ROOT / ".secrets"
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "external_web" / "youtube_mentions_raw.csv"
DEFAULT_REPORT = ROOT / "reports" / "external_web" / "youtube_collection_report.md"
YOUTUBE_SEARCH_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNELS_ENDPOINT = "https://www.googleapis.com/youtube/v3/channels"

DEFAULT_QUERIES = [
    "연희요가위크",
    "연희 요가 위크",
    "2026 연희요가위크",
    "연희 요가 축제",
    "연희요가위크 후기",
    "오붓 연희요가위크",
    "빅블루요가 연희요가위크",
    "마이트리 연희요가위크",
    "마인드플로우 연희요가위크",
    "시이작 연희요가위크",
    "연희정음 연희요가위크",
    "연남장 연희요가위크",
]

SPACE_RE = re.compile(r"\s+")


def clean_search_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = html.unescape(text)
    return SPACE_RE.sub(" ", text).strip()


def read_secret(filename: str) -> str:
    path = SECRETS_DIR / filename
    if not path.exists():
        raise SystemExit(f"Missing secret file: {path}")
    value = path.read_text(encoding="utf-8-sig").strip()
    if not value:
        raise SystemExit(f"Secret file is empty: {path}")
    return value


def read_queries(path: Path | None) -> list[str]:
    if path is None:
        return DEFAULT_QUERIES
    if not path.exists():
        raise SystemExit(f"Missing query file: {path}")
    queries: list[str] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        query = line.strip()
        if query and not query.startswith("#"):
            queries.append(query)
    if not queries:
        raise SystemExit(f"No queries found in: {path}")
    return queries


def youtube_get(endpoint: str, params: dict[str, object]) -> dict[str, object]:
    response = requests.get(endpoint, params=params, timeout=20)
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code == 403:
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        message = str(error.get("message", "")).strip()
        raise SystemExit(f"YouTube API request was blocked: {message}")
    if response.status_code == 400:
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        message = str(error.get("message", "")).strip()
        raise SystemExit(f"YouTube API request was invalid: {message}")

    response.raise_for_status()
    return payload


def search_videos(
    *,
    query: str,
    api_key: str,
    max_results_per_query: int,
    page_size: int,
    order: str,
    published_after: str | None,
    published_before: str | None,
    sleep_seconds: float,
) -> tuple[list[dict[str, object]], int]:
    rows: list[dict[str, object]] = []
    page_token = ""
    search_calls = 0
    rank = 1

    while len(rows) < max_results_per_query:
        request_size = min(page_size, max_results_per_query - len(rows))
        params: dict[str, object] = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": request_size,
            "order": order,
            "regionCode": "KR",
            "relevanceLanguage": "ko",
            "safeSearch": "moderate",
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token
        if published_after:
            params["publishedAfter"] = published_after
        if published_before:
            params["publishedBefore"] = published_before

        payload = youtube_get(YOUTUBE_SEARCH_ENDPOINT, params)
        search_calls += 1
        items = payload.get("items", [])
        if not items:
            break

        page_info = payload.get("pageInfo", {}) if isinstance(payload.get("pageInfo"), dict) else {}
        for item in items:
            video_id = item.get("id", {}).get("videoId", "")
            snippet = item.get("snippet", {})
            if not video_id:
                continue
            rows.append(
                {
                    "platform": "youtube",
                    "query": query,
                    "query_rank": rank,
                    "api_total_for_query": page_info.get("totalResults", ""),
                    "video_id": video_id,
                    "video_url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": clean_search_text(snippet.get("title")),
                    "description": clean_search_text(snippet.get("description")),
                    "channel_title": clean_search_text(snippet.get("channelTitle")),
                    "channel_id": snippet.get("channelId", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail_default_url": (
                        snippet.get("thumbnails", {}).get("default", {}).get("url", "")
                        if isinstance(snippet.get("thumbnails"), dict)
                        else ""
                    ),
                }
            )
            rank += 1

        page_token = str(payload.get("nextPageToken", "") or "")
        if not page_token:
            break
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    return rows, search_calls


def chunked(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def fetch_video_details(api_key: str, video_ids: list[str], sleep_seconds: float) -> tuple[dict[str, dict[str, object]], int]:
    details: dict[str, dict[str, object]] = {}
    calls = 0
    for batch in chunked(video_ids, 50):
        payload = youtube_get(
            YOUTUBE_VIDEOS_ENDPOINT,
            {
                "part": "statistics,contentDetails,status",
                "id": ",".join(batch),
                "key": api_key,
            },
        )
        calls += 1
        for item in payload.get("items", []):
            video_id = item.get("id", "")
            statistics = item.get("statistics", {}) if isinstance(item.get("statistics"), dict) else {}
            content_details = item.get("contentDetails", {}) if isinstance(item.get("contentDetails"), dict) else {}
            status = item.get("status", {}) if isinstance(item.get("status"), dict) else {}
            details[video_id] = {
                "duration_iso": content_details.get("duration", ""),
                "caption": content_details.get("caption", ""),
                "licensed_content": content_details.get("licensedContent", ""),
                "view_count": statistics.get("viewCount", ""),
                "like_count": statistics.get("likeCount", ""),
                "comment_count": statistics.get("commentCount", ""),
                "favorite_count": statistics.get("favoriteCount", ""),
                "privacy_status": status.get("privacyStatus", ""),
                "embeddable": status.get("embeddable", ""),
                "made_for_kids": status.get("madeForKids", ""),
            }
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return details, calls


def fetch_channel_details(api_key: str, channel_ids: list[str], sleep_seconds: float) -> tuple[dict[str, dict[str, object]], int]:
    details: dict[str, dict[str, object]] = {}
    calls = 0
    for batch in chunked(channel_ids, 50):
        payload = youtube_get(
            YOUTUBE_CHANNELS_ENDPOINT,
            {
                "part": "snippet,statistics,status",
                "id": ",".join(batch),
                "key": api_key,
            },
        )
        calls += 1
        for item in payload.get("items", []):
            channel_id = item.get("id", "")
            snippet = item.get("snippet", {}) if isinstance(item.get("snippet"), dict) else {}
            statistics = item.get("statistics", {}) if isinstance(item.get("statistics"), dict) else {}
            status = item.get("status", {}) if isinstance(item.get("status"), dict) else {}
            details[channel_id] = {
                "channel_published_at": snippet.get("publishedAt", ""),
                "channel_description": clean_search_text(snippet.get("description")),
                "channel_custom_url": snippet.get("customUrl", ""),
                "channel_country": snippet.get("country", ""),
                "channel_view_count": statistics.get("viewCount", ""),
                "channel_subscriber_count": statistics.get("subscriberCount", ""),
                "channel_hidden_subscriber_count": statistics.get("hiddenSubscriberCount", ""),
                "channel_video_count": statistics.get("videoCount", ""),
                "channel_privacy_status": status.get("privacyStatus", ""),
                "channel_made_for_kids": status.get("madeForKids", ""),
            }
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return details, calls


def collect_rows(
    *,
    queries: Iterable[str],
    max_results_per_query: int,
    page_size: int,
    order: str,
    published_after: str | None,
    published_before: str | None,
    sleep_seconds: float,
) -> tuple[list[dict[str, object]], dict[str, int]]:
    api_key = read_secret("youtube-api-key.txt")
    collected_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    rows: list[dict[str, object]] = []
    counters = {"search_calls": 0, "video_detail_calls": 0, "channel_detail_calls": 0}

    page_size = max(1, min(page_size, 50))
    max_results_per_query = max(1, min(max_results_per_query, 500))

    for query in queries:
        query_rows, search_calls = search_videos(
            query=query,
            api_key=api_key,
            max_results_per_query=max_results_per_query,
            page_size=page_size,
            order=order,
            published_after=published_after,
            published_before=published_before,
            sleep_seconds=sleep_seconds,
        )
        counters["search_calls"] += search_calls
        rows.extend(query_rows)

    unique_video_ids = sorted({str(row["video_id"]) for row in rows if str(row.get("video_id", "")).strip()})
    details, detail_calls = fetch_video_details(api_key, unique_video_ids, sleep_seconds=sleep_seconds)
    counters["video_detail_calls"] += detail_calls

    unique_channel_ids = sorted({str(row["channel_id"]) for row in rows if str(row.get("channel_id", "")).strip()})
    channel_details, channel_calls = fetch_channel_details(api_key, unique_channel_ids, sleep_seconds=sleep_seconds)
    counters["channel_detail_calls"] += channel_calls

    for row in rows:
        row.update(details.get(str(row.get("video_id", "")), {}))
        row.update(channel_details.get(str(row.get("channel_id", "")), {}))
        row["collected_at"] = collected_at

    return rows, counters


def write_rows(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "platform",
        "query",
        "query_rank",
        "api_total_for_query",
        "video_id",
        "video_url",
        "title",
        "description",
        "channel_title",
        "channel_id",
        "published_at",
        "thumbnail_default_url",
        "duration_iso",
        "caption",
        "licensed_content",
        "view_count",
        "like_count",
        "comment_count",
        "favorite_count",
        "privacy_status",
        "embeddable",
        "made_for_kids",
        "channel_published_at",
        "channel_description",
        "channel_custom_url",
        "channel_country",
        "channel_view_count",
        "channel_subscriber_count",
        "channel_hidden_subscriber_count",
        "channel_video_count",
        "channel_privacy_status",
        "channel_made_for_kids",
        "collected_at",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    *,
    rows: list[dict[str, object]],
    queries: list[str],
    counters: dict[str, int],
    output_path: Path,
    report_path: Path,
    published_after: str | None,
    published_before: str | None,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    query_counts = Counter(str(row["query"]) for row in rows)
    unique_video_ids = {str(row["video_id"]) for row in rows if str(row.get("video_id", "")).strip()}
    unique_channel_ids = {str(row["channel_id"]) for row in rows if str(row.get("channel_id", "")).strip()}
    quota_estimate = counters["search_calls"] * 100 + counters["video_detail_calls"] + counters["channel_detail_calls"]
    query_table = "\n".join(f"| {query} | {query_counts.get(query, 0)} |" for query in queries)
    report = f"""# YouTube Collection Report

Generated: {generated_at}

## Purpose

Collect public YouTube search result metadata for 2026 Yeonhui Yoga Week viral/sns analysis.

## Inputs

- API: YouTube Data API v3
- Search method: `search.list`
- Video details method: `videos.list`
- Queries: {len(queries)}
- Published after: {published_after or ""}
- Published before: {published_before or ""}

## Outputs

- Raw CSV: `{output_path.relative_to(ROOT)}`
- Total search result rows saved: {len(rows)}
- Unique videos: {len(unique_video_ids)}
- Unique channels: {len(unique_channel_ids)}

## API Use

- Search calls: {counters["search_calls"]}
- Video detail calls: {counters["video_detail_calls"]}
- Channel detail calls: {counters["channel_detail_calls"]}
- Estimated quota units: {quota_estimate}

## Query Counts

| query | saved_rows |
|---|---:|
{query_table}

## Notes

- This file records public video metadata and links only.
- API keys are read from `.secrets/youtube-api-key.txt`.
- YouTube search results are not a complete archive of all platform activity.
- Public reporting should avoid treating individual channels as evaluation targets.
"""
    report_path.write_text(report, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect YouTube search results for viral analysis.")
    parser.add_argument("--queries-file", type=Path, default=None, help="Optional text file with one query per line.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output raw CSV path.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Collection report path.")
    parser.add_argument("--max-results-per-query", type=int, default=50, help="Maximum videos per query, up to 500.")
    parser.add_argument("--page-size", type=int, default=50, help="Results per API call, up to 50.")
    parser.add_argument(
        "--order",
        choices=["date", "rating", "relevance", "title", "videoCount", "viewCount"],
        default="relevance",
        help="YouTube search order.",
    )
    parser.add_argument(
        "--published-after",
        default="2026-01-01T00:00:00Z",
        help="RFC3339 lower bound for video publish date. Use '' to disable.",
    )
    parser.add_argument("--published-before", default="", help="RFC3339 upper bound for video publish date.")
    parser.add_argument("--sleep-seconds", type=float, default=0.15, help="Pause between API calls.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    queries = read_queries(args.queries_file)
    published_after = args.published_after.strip() or None
    published_before = args.published_before.strip() or None
    rows, counters = collect_rows(
        queries=queries,
        max_results_per_query=args.max_results_per_query,
        page_size=args.page_size,
        order=args.order,
        published_after=published_after,
        published_before=published_before,
        sleep_seconds=args.sleep_seconds,
    )
    write_rows(rows, args.output)
    write_report(
        rows=rows,
        queries=queries,
        counters=counters,
        output_path=args.output,
        report_path=args.report,
        published_after=published_after,
        published_before=published_before,
    )
    unique_video_ids = {str(row["video_id"]) for row in rows if str(row.get("video_id", "")).strip()}
    unique_channel_ids = {str(row["channel_id"]) for row in rows if str(row.get("channel_id", "")).strip()}
    quota_estimate = counters["search_calls"] * 100 + counters["video_detail_calls"] + counters["channel_detail_calls"]
    print(f"Wrote {args.output}")
    print(f"Wrote {args.report}")
    print(f"Rows: {len(rows)}")
    print(f"Unique videos: {len(unique_video_ids)}")
    print(f"Unique channels: {len(unique_channel_ids)}")
    print(f"Search calls: {counters['search_calls']}")
    print(f"Video detail calls: {counters['video_detail_calls']}")
    print(f"Channel detail calls: {counters['channel_detail_calls']}")
    print(f"Estimated quota units: {quota_estimate}")


if __name__ == "__main__":
    main()
