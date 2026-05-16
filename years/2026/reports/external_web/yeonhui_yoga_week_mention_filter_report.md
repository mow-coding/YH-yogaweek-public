# Yeonhui Yoga Week Mention Filter Report

Generated: 2026-05-17T02:50:26+09:00

## Purpose

Filter the external viral mention review queue to confirmed 2026 Yeonhui Yoga Week mentions.

## Strict Confirmation Rule

A row is confirmed only when both conditions are true:

1. `title` or `description` directly contains `연희요가위크` after whitespace normalization.
2. `published_at` is on or after `2026-02-01`, the month when internal planning first started.

Search query text is not used as confirmation evidence.
Studio/place names alone are not used as confirmation evidence.

## Inputs

- Review queue: `data\interim\external_web\viral_mentions_review_queue.csv`

## Outputs

- Internal checked CSV: `data\interim\external_web\yeonhui_yoga_week_mentions_checked.csv`
- Internal confirmed CSV: `data\interim\external_web\yeonhui_yoga_week_mentions_confirmed_internal.csv`
- Public anonymized confirmed CSV: `data\processed\analysis\public\yeonhui_yoga_week_viral_mentions_public.csv`
- Public platform summary: `data\processed\analysis\public\yeonhui_yoga_week_viral_platform_summary.csv`
- Public studio summary: `data\processed\analysis\public\yeonhui_yoga_week_viral_studio_summary.csv`

## Result

- Input candidate mentions: 1143
- Confirmed event mentions: 60
- Public confirmed rows: 60
- Not confirmed / needs review: 1083

## Classification Counts

| classification | rows |
|---|---:|
| confirmed_2026_yeonhui_yoga_week | 60 |
| not_confirmed_no_direct_event_keyword | 1083 |

## Confirmed Platform Counts

| platform | confirmed_rows |
|---|---:|
| naver_blog | 58 |
| youtube | 2 |

## Public Identity Handling

Internal files retain public source names, public IDs, profile URLs, and exact source URLs for provenance checks.
The public confirmed CSV replaces source identity with `external_source_####` and omits exact source URLs.
