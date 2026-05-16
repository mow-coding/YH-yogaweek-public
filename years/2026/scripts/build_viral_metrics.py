from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_PUBLIC_DIR = ROOT / "data" / "processed" / "analysis" / "public"
REPORT_EXTERNAL_DIR = ROOT / "reports" / "external_web"

CONFIRMED_PUBLIC = ANALYSIS_PUBLIC_DIR / "yeonhui_yoga_week_viral_mentions_public.csv"
VIRAL_OVERALL_SUMMARY = ANALYSIS_PUBLIC_DIR / "yeonhui_yoga_week_viral_overall_summary.csv"
VIRAL_PLATFORM_METRICS = ANALYSIS_PUBLIC_DIR / "yeonhui_yoga_week_viral_platform_metrics.csv"
VIRAL_STUDIO_METRICS = ANALYSIS_PUBLIC_DIR / "yeonhui_yoga_week_viral_studio_metrics.csv"
VIRAL_UNMATCHED_PUBLIC = ANALYSIS_PUBLIC_DIR / "yeonhui_yoga_week_viral_unmatched_mentions_public.csv"
REPORT_PATH = REPORT_EXTERNAL_DIR / "yeonhui_yoga_week_viral_analysis_report.md"
STUDIO_TERM_ALIASES = {
    "빅블루": "빅블루요가",
    "숨 명상센터": "숨명상센터",
    "대저택 프라이빗": "대저택프라이빗",
    "비전스트롤": "비전스트롤 콜라보",
}


def compact_spaces(value: object) -> str:
    return " ".join(("" if value is None else str(value)).split())


def safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def numeric_sum(series: pd.Series) -> int:
    return int(safe_numeric(series).sum())


def first_non_empty(series: pd.Series) -> str:
    for value in series:
        text = compact_spaces(value)
        if text:
            return text
    return ""


def percentile_0_100(values: pd.Series) -> pd.Series:
    numeric = safe_numeric(values)
    if numeric.empty:
        return pd.Series(dtype=float)
    ranks = numeric.rank(method="average", pct=True)
    return (ranks * 100).round(2)


def date_min(series: pd.Series) -> str:
    dates = pd.to_datetime(series, errors="coerce")
    if dates.notna().any():
        return str(dates.min().date())
    return ""


def date_max(series: pd.Series) -> str:
    dates = pd.to_datetime(series, errors="coerce")
    if dates.notna().any():
        return str(dates.max().date())
    return ""


def explode_studio_terms(mentions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in mentions.iterrows():
        terms = [compact_spaces(term) for term in str(row.get("matched_studio_terms", "")).split(";")]
        terms = [term for term in terms if term and term != "UNMATCHED"]
        if not terms:
            rows.append({**row.to_dict(), "matched_studio_term": "UNMATCHED"})
            continue
        for term in dict.fromkeys(terms):
            rows.append({**row.to_dict(), "matched_studio_term": STUDIO_TERM_ALIASES.get(term, term)})
    exploded = pd.DataFrame(rows)
    if exploded.empty:
        return exploded
    return exploded.drop_duplicates(subset=["mention_public_id", "matched_studio_term"])


def build_overall_summary(mentions: pd.DataFrame) -> pd.DataFrame:
    if mentions.empty:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "confirmed_mention_count": len(mentions),
                "platform_count": mentions["platform"].nunique(),
                "anonymous_source_count": mentions["source_public_anonymous_id"].nunique(),
                "naver_blog_mention_count": int((mentions["platform"] == "naver_blog").sum()),
                "youtube_video_count": int((mentions["platform"] == "youtube").sum()),
                "youtube_view_count": numeric_sum(mentions.loc[mentions["platform"] == "youtube", "view_count"]),
                "youtube_like_count": numeric_sum(mentions.loc[mentions["platform"] == "youtube", "like_count"]),
                "youtube_comment_count": numeric_sum(mentions.loc[mentions["platform"] == "youtube", "comment_count"]),
                "first_published_date": date_min(mentions["published_date"]),
                "last_published_date": date_max(mentions["published_date"]),
                "metric_scope": "Confirmed direct mentions of 연희요가위크 only; separate from Hype metrics.",
            }
        ]
    )


def build_platform_metrics(mentions: pd.DataFrame) -> pd.DataFrame:
    if mentions.empty:
        return pd.DataFrame()
    metrics = (
        mentions.groupby("platform", dropna=False)
        .agg(
            confirmed_mention_count=("mention_public_id", "count"),
            anonymous_source_count=("source_public_anonymous_id", "nunique"),
            youtube_view_count=("view_count", numeric_sum),
            youtube_like_count=("like_count", numeric_sum),
            youtube_comment_count=("comment_count", numeric_sum),
            first_published_date=("published_date", date_min),
            last_published_date=("published_date", date_max),
        )
        .reset_index()
    )
    metrics["mention_share"] = (
        metrics["confirmed_mention_count"] / metrics["confirmed_mention_count"].sum()
    ).round(4)
    metrics["viral_signal_note"] = "Platform-level external viral signal, not Hype."
    return metrics.sort_values(["confirmed_mention_count", "youtube_view_count"], ascending=[False, False])


def build_studio_metrics(mentions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    exploded = explode_studio_terms(mentions)
    unmatched = exploded[exploded["matched_studio_term"] == "UNMATCHED"].copy()
    matched = exploded[exploded["matched_studio_term"] != "UNMATCHED"].copy()

    if matched.empty:
        return pd.DataFrame(), unmatched

    metrics = (
        matched.groupby("matched_studio_term", dropna=False)
        .agg(
            confirmed_mention_count=("mention_public_id", "nunique"),
            naver_blog_mention_count=(
                "platform",
                lambda values: int((values == "naver_blog").sum()),
            ),
            youtube_video_count=("platform", lambda values: int((values == "youtube").sum())),
            platform_count=("platform", "nunique"),
            anonymous_source_count=("source_public_anonymous_id", "nunique"),
            youtube_view_count=("view_count", numeric_sum),
            youtube_like_count=("like_count", numeric_sum),
            youtube_comment_count=("comment_count", numeric_sum),
            first_published_date=("published_date", date_min),
            last_published_date=("published_date", date_max),
        )
        .reset_index()
    )

    metrics["mention_score"] = percentile_0_100(metrics["confirmed_mention_count"])
    metrics["source_score"] = percentile_0_100(metrics["anonymous_source_count"])
    metrics["youtube_reach_score"] = percentile_0_100(metrics["youtube_view_count"].map(lambda value: math.log1p(float(value))))
    metrics["platform_diversity_score"] = (metrics["platform_count"] / 2 * 100).clip(upper=100).round(2)
    metrics["viral_signal_score"] = (
        metrics["mention_score"] * 0.45
        + metrics["source_score"] * 0.25
        + metrics["youtube_reach_score"] * 0.20
        + metrics["platform_diversity_score"] * 0.10
    ).round(2)
    metrics["viral_signal_formula"] = (
        "0.45*mention_score + 0.25*source_score + 0.20*youtube_reach_score + 0.10*platform_diversity_score"
    )
    metrics["metric_scope"] = "External web viral signal only; not merged into Hype."
    metrics = metrics.sort_values(
        ["viral_signal_score", "confirmed_mention_count", "youtube_view_count"],
        ascending=[False, False, False],
    )
    return metrics, unmatched


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        values = [compact_spaces(row.get(column, "")) for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_report(
    mentions: pd.DataFrame,
    overall: pd.DataFrame,
    platform_metrics: pd.DataFrame,
    studio_metrics: pd.DataFrame,
    unmatched: pd.DataFrame,
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    platform_table = markdown_table(platform_metrics) if not platform_metrics.empty else ""
    studio_table = (
        markdown_table(studio_metrics[
            [
                "matched_studio_term",
                "confirmed_mention_count",
                "anonymous_source_count",
                "youtube_view_count",
                "viral_signal_score",
            ]
        ].head(20))
        if not studio_metrics.empty
        else ""
    )
    overall_row = overall.iloc[0].to_dict() if not overall.empty else {}
    report = f"""# Yeonhui Yoga Week Viral Analysis Report

Generated: {generated_at}

## Scope

This report treats `Viral` as a separate external web diffusion signal.
It is not merged into existing Hype metrics.

Confirmed mentions are limited to rows where title or description directly contains `연희요가위크`
and the published date is on or after 2026-02-01.

## Inputs

- Public confirmed mentions: `{CONFIRMED_PUBLIC.relative_to(ROOT)}`

## Outputs

- Overall summary: `{VIRAL_OVERALL_SUMMARY.relative_to(ROOT)}`
- Platform metrics: `{VIRAL_PLATFORM_METRICS.relative_to(ROOT)}`
- Studio/place metrics: `{VIRAL_STUDIO_METRICS.relative_to(ROOT)}`
- Unmatched confirmed mentions: `{VIRAL_UNMATCHED_PUBLIC.relative_to(ROOT)}`

## Overall

- Confirmed mentions: {overall_row.get("confirmed_mention_count", 0)}
- Platforms: {overall_row.get("platform_count", 0)}
- Anonymous sources: {overall_row.get("anonymous_source_count", 0)}
- Naver blog mentions: {overall_row.get("naver_blog_mention_count", 0)}
- YouTube videos: {overall_row.get("youtube_video_count", 0)}
- YouTube views: {overall_row.get("youtube_view_count", 0)}
- Publication window: {overall_row.get("first_published_date", "")} to {overall_row.get("last_published_date", "")}
- Confirmed mentions without studio/place match: {len(unmatched)}

## Platform Metrics

{platform_table}

## Studio/Place Viral Metrics

{studio_table}

## Score Interpretation

`viral_signal_score` is a descriptive external-web signal only.
It is calculated from mention count, anonymous source count, YouTube reach proxy, and platform diversity.
It should be interpreted alongside reservation/review Hype, not added into it.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    if not CONFIRMED_PUBLIC.exists():
        raise FileNotFoundError(f"Missing confirmed public file: {CONFIRMED_PUBLIC}")

    mentions = pd.read_csv(CONFIRMED_PUBLIC, dtype=str, keep_default_na=False)
    overall = build_overall_summary(mentions)
    platform_metrics = build_platform_metrics(mentions)
    studio_metrics, unmatched = build_studio_metrics(mentions)

    write_csv(overall, VIRAL_OVERALL_SUMMARY)
    write_csv(platform_metrics, VIRAL_PLATFORM_METRICS)
    write_csv(studio_metrics, VIRAL_STUDIO_METRICS)
    write_csv(unmatched, VIRAL_UNMATCHED_PUBLIC)
    write_report(mentions, overall, platform_metrics, studio_metrics, unmatched)

    print(f"Wrote {VIRAL_OVERALL_SUMMARY}")
    print(f"Wrote {VIRAL_PLATFORM_METRICS}")
    print(f"Wrote {VIRAL_STUDIO_METRICS}")
    print(f"Wrote {VIRAL_UNMATCHED_PUBLIC}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Confirmed mentions: {len(mentions)}")
    print(f"Studio/place metric rows: {len(studio_metrics)}")
    print(f"Unmatched confirmed mentions: {len(unmatched)}")


if __name__ == "__main__":
    main()
