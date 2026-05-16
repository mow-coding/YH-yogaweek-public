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
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "external_web" / "naver_blog_mentions_raw.csv"
DEFAULT_REPORT = ROOT / "reports" / "external_web" / "naver_blog_collection_report.md"
NAVER_BLOG_ENDPOINT = "https://openapi.naver.com/v1/search/blog.json"

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

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def clean_search_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = TAG_RE.sub("", text)
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


def naver_blog_search(
    *,
    query: str,
    client_id: str,
    client_secret: str,
    start: int,
    display: int,
    sort: str,
) -> dict[str, object]:
    response = requests.get(
        NAVER_BLOG_ENDPOINT,
        params={
            "query": query,
            "start": start,
            "display": display,
            "sort": sort,
        },
        headers={
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        },
        timeout=20,
    )
    if response.status_code == 401:
        raise SystemExit("Naver API authentication failed. Check .secrets/naver-client-id.txt and naver-client-secret.txt.")
    if response.status_code == 429:
        raise SystemExit("Naver API rate limit was reached. Wait a bit and run again.")
    response.raise_for_status()
    return response.json()


def normalize_post_date(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if re.fullmatch(r"\d{8}", text):
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text


def collect_rows(
    *,
    queries: Iterable[str],
    max_results_per_query: int,
    display: int,
    sort: str,
    sleep_seconds: float,
) -> list[dict[str, object]]:
    client_id = read_secret("naver-client-id.txt")
    client_secret = read_secret("naver-client-secret.txt")
    collected_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    rows: list[dict[str, object]] = []

    display = max(1, min(display, 100))
    max_results_per_query = max(1, min(max_results_per_query, 1000))

    for query in queries:
        query_total = None
        for start in range(1, max_results_per_query + 1, display):
            result = naver_blog_search(
                query=query,
                client_id=client_id,
                client_secret=client_secret,
                start=start,
                display=display,
                sort=sort,
            )
            query_total = result.get("total")
            items = result.get("items", [])
            if not items:
                break

            for offset, item in enumerate(items, start=0):
                rank = start + offset
                rows.append(
                    {
                        "platform": "naver_blog",
                        "query": query,
                        "query_rank": rank,
                        "api_total_for_query": query_total,
                        "title": clean_search_text(item.get("title")),
                        "link": item.get("link", ""),
                        "description": clean_search_text(item.get("description")),
                        "blogger_name": clean_search_text(item.get("bloggername")),
                        "blogger_link": item.get("bloggerlink", ""),
                        "post_date": normalize_post_date(item.get("postdate")),
                        "post_date_raw": item.get("postdate", ""),
                        "collected_at": collected_at,
                        "raw_title_html": item.get("title", ""),
                        "raw_description_html": item.get("description", ""),
                    }
                )

            if len(items) < display:
                break
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    return rows


def write_rows(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "platform",
        "query",
        "query_rank",
        "api_total_for_query",
        "title",
        "link",
        "description",
        "blogger_name",
        "blogger_link",
        "post_date",
        "post_date_raw",
        "collected_at",
        "raw_title_html",
        "raw_description_html",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, object]], queries: list[str], output_path: Path, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    query_counts = Counter(str(row["query"]) for row in rows)
    unique_links = {str(row["link"]) for row in rows if str(row.get("link", "")).strip()}
    query_table = "\n".join(
        f"| {query} | {query_counts.get(query, 0)} |" for query in queries
    )
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    report = f"""# Naver Blog Collection Report

Generated: {generated_at}

## Purpose

Collect public Naver Blog search results for 2026 Yeonhui Yoga Week viral/sns analysis.

## Inputs

- API: Naver Search API, blog endpoint
- Queries: {len(queries)}

## Outputs

- Raw CSV: `{output_path.relative_to(ROOT)}`
- Total search result rows saved: {len(rows)}
- Unique links: {len(unique_links)}

## Query Counts

| query | saved_rows |
|---|---:|
{query_table}

## Notes

- This file records search-result metadata and snippets only.
- API keys are read from `.secrets/naver-client-id.txt` and `.secrets/naver-client-secret.txt`.
- Public reporting should avoid exposing personal blog identities as ranking targets.
"""
    report_path.write_text(report, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect Naver Blog search results for viral analysis.")
    parser.add_argument("--queries-file", type=Path, default=None, help="Optional text file with one query per line.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output raw CSV path.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Collection report path.")
    parser.add_argument("--max-results-per-query", type=int, default=100, help="Maximum results per query, up to 1000.")
    parser.add_argument("--display", type=int, default=100, help="Results per API call, up to 100.")
    parser.add_argument("--sort", choices=["sim", "date"], default="sim", help="Naver API sort mode.")
    parser.add_argument("--sleep-seconds", type=float, default=0.15, help="Pause between paged API calls.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    queries = read_queries(args.queries_file)
    rows = collect_rows(
        queries=queries,
        max_results_per_query=args.max_results_per_query,
        display=args.display,
        sort=args.sort,
        sleep_seconds=args.sleep_seconds,
    )
    write_rows(rows, args.output)
    write_report(rows, queries, args.output, args.report)
    unique_links = {str(row["link"]) for row in rows if str(row.get("link", "")).strip()}
    print(f"Wrote {args.output}")
    print(f"Wrote {args.report}")
    print(f"Rows: {len(rows)}")
    print(f"Unique links: {len(unique_links)}")


if __name__ == "__main__":
    main()
