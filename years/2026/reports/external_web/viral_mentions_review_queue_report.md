# Viral Mentions Review Queue Report

Generated: 2026-05-16T16:27:02+09:00

## Purpose

Build an internal review queue from Naver Blog and YouTube raw collection files.

## Inputs

- Naver raw: `data\raw\external_web\naver_blog_mentions_raw.csv`
- YouTube raw: `data\raw\external_web\youtube_mentions_raw.csv`

## Output

- Review queue CSV: `data\interim\external_web\viral_mentions_review_queue.csv`
- Unique mention rows: 1143
- Rows needing manual relevance review: 1081

## Platform Counts

| platform | rows |
|---|---:|
| naver_blog | 1075 |
| youtube | 68 |

## Handling Rule

The review queue keeps public source names, public source IDs, and source URLs for internal provenance checks.
Future public outputs should mask or aggregate individual source identities unless explicit publication is needed and reviewed.
