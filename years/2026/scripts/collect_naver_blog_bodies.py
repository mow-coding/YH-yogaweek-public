from __future__ import annotations

import argparse
import csv
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
CONFIRMED_INTERNAL = ROOT / "data" / "interim" / "external_web" / "yeonhui_yoga_week_mentions_confirmed_internal.csv"
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "external_web" / "naver_blog_bodies_raw.csv"
DEFAULT_REPORT = ROOT / "reports" / "external_web" / "naver_blog_body_collection_report.md"

USER_AGENT = "Mozilla/5.0 (compatible; YeonhuiYogaWeekResearchBot/1.0; public research metadata collection)"
ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\ufeff]")
SPACE_RE = re.compile(r"[ \t\r\f\v]+")
NEWLINE_RE = re.compile(r"\n{3,}")


def clean_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = ZERO_WIDTH_RE.sub("", text)
    text = text.replace("\xa0", " ")
    text = SPACE_RE.sub(" ", text)
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return NEWLINE_RE.sub("\n\n", text).strip()


def request_text(url: str) -> tuple[int, str, str]:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=25,
    )
    response.raise_for_status()
    return response.status_code, response.url, response.text


def extract_post_url(initial_url: str, html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    iframe = soup.find("iframe", id="mainFrame")
    if iframe and iframe.get("src"):
        return urljoin(initial_url, str(iframe["src"]))
    return initial_url


def extract_body(post_html: str) -> tuple[str, str]:
    soup = BeautifulSoup(post_html, "html.parser")
    selectors = [
        "div.se-main-container",
        "div#postViewArea",
        "div.post-view",
        "div.post_ct",
        "div.view",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue
        for removable in node.select("script, style, iframe"):
            removable.decompose()
        text = clean_text(node.get_text("\n", strip=True))
        if text:
            return text, selector
    return "", ""


def collect_body(row: pd.Series, sleep_seconds: float) -> dict[str, object]:
    source_url = str(row.get("source_url", "")).strip()
    fetched_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    base = {
        "mention_id": row.get("mention_id", ""),
        "source_url": source_url,
        "title": row.get("title", ""),
        "source_public_name": row.get("source_public_name", ""),
        "published_at": row.get("published_at", ""),
        "fetched_at": fetched_at,
        "initial_status_code": "",
        "initial_final_url": "",
        "post_view_url": "",
        "post_status_code": "",
        "post_final_url": "",
        "body_text": "",
        "body_text_chars": 0,
        "body_text_lines": 0,
        "body_extraction_selector": "",
        "body_fetch_status": "not_attempted",
        "body_fetch_error": "",
    }

    if not source_url:
        base["body_fetch_status"] = "missing_url"
        return base

    try:
        initial_status, initial_final_url, initial_html = request_text(source_url)
        post_url = extract_post_url(initial_final_url, initial_html)
        post_status, post_final_url, post_html = (
            request_text(post_url) if post_url != initial_final_url else (initial_status, initial_final_url, initial_html)
        )
        body_text, selector = extract_body(post_html)
        base.update(
            {
                "initial_status_code": initial_status,
                "initial_final_url": initial_final_url,
                "post_view_url": post_url,
                "post_status_code": post_status,
                "post_final_url": post_final_url,
                "body_text": body_text,
                "body_text_chars": len(body_text),
                "body_text_lines": len(body_text.splitlines()) if body_text else 0,
                "body_extraction_selector": selector,
                "body_fetch_status": "success" if body_text else "empty_body",
            }
        )
    except Exception as exc:
        base["body_fetch_status"] = "failed"
        base["body_fetch_error"] = f"{type(exc).__name__}: {exc}"

    if sleep_seconds > 0:
        time.sleep(sleep_seconds)
    return base


def write_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "mention_id",
        "source_url",
        "title",
        "source_public_name",
        "published_at",
        "fetched_at",
        "initial_status_code",
        "initial_final_url",
        "post_view_url",
        "post_status_code",
        "post_final_url",
        "body_text",
        "body_text_chars",
        "body_text_lines",
        "body_extraction_selector",
        "body_fetch_status",
        "body_fetch_error",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, object]], output_path: Path, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    total = len(rows)
    success = sum(1 for row in rows if row.get("body_fetch_status") == "success")
    empty = sum(1 for row in rows if row.get("body_fetch_status") == "empty_body")
    failed = sum(1 for row in rows if row.get("body_fetch_status") == "failed")
    total_chars = sum(int(row.get("body_text_chars") or 0) for row in rows)
    report = f"""# Naver Blog Body Collection Report

Generated: {generated_at}

## Purpose

Collect publicly accessible body text for confirmed Naver Blog mentions of 2026 Yeonhui Yoga Week.

## Scope

- Input: `{CONFIRMED_INTERNAL.relative_to(ROOT)}`
- Platform filtered: `naver_blog`
- Access mode: public page fetch only, no login, no private content access
- Output raw CSV: `{output_path.relative_to(ROOT)}`

## Result

- Naver confirmed rows attempted: {total}
- Successful body fetches: {success}
- Empty body fetches: {empty}
- Failed fetches: {failed}
- Total fetched body characters: {total_chars}

## Notes

- This raw file may contain personal writing and source identity, so it stays under `data/raw` and is not a public output.
- Public analysis should use anonymized summaries or aggregate features derived from this file.
"""
    report_path.write_text(report, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public Naver Blog body text for confirmed viral mentions.")
    parser.add_argument("--input", type=Path, default=CONFIRMED_INTERNAL, help="Confirmed internal mentions CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output raw body CSV path.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Body collection report path.")
    parser.add_argument("--sleep-seconds", type=float, default=0.7, help="Pause between blog fetches.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Missing input CSV: {args.input}")

    confirmed = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    naver_rows = confirmed[confirmed["platform"].eq("naver_blog")].copy()
    rows = [collect_body(row, args.sleep_seconds) for _, row in naver_rows.iterrows()]
    write_csv(rows, args.output)
    write_report(rows, args.output, args.report)

    success = sum(1 for row in rows if row.get("body_fetch_status") == "success")
    print(f"Wrote {args.output}")
    print(f"Wrote {args.report}")
    print(f"Attempted: {len(rows)}")
    print(f"Successful body fetches: {success}")


if __name__ == "__main__":
    main()
