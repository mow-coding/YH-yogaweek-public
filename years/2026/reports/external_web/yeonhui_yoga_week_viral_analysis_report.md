# Yeonhui Yoga Week Viral Analysis Report

Generated: 2026-05-17T02:50:32+09:00

## Scope

This report treats `Viral` as a separate external web diffusion signal.
It is not merged into existing Hype metrics.

Confirmed mentions are limited to rows where title or description directly contains `연희요가위크`
and the published date is on or after 2026-02-01.

## Inputs

- Public confirmed mentions: `data\processed\analysis\public\yeonhui_yoga_week_viral_mentions_public.csv`

## Outputs

- Overall summary: `data\processed\analysis\public\yeonhui_yoga_week_viral_overall_summary.csv`
- Platform metrics: `data\processed\analysis\public\yeonhui_yoga_week_viral_platform_metrics.csv`
- Studio/place metrics: `data\processed\analysis\public\yeonhui_yoga_week_viral_studio_metrics.csv`
- Unmatched confirmed mentions: `data\processed\analysis\public\yeonhui_yoga_week_viral_unmatched_mentions_public.csv`

## Overall

- Confirmed mentions: 60
- Platforms: 2
- Anonymous sources: 34
- Naver blog mentions: 58
- YouTube videos: 2
- YouTube views: 1808
- Publication window: 2026-03-20 to 2026-05-16
- Confirmed mentions without studio/place match: 17

## Platform Metrics

| platform | confirmed_mention_count | anonymous_source_count | youtube_view_count | youtube_like_count | youtube_comment_count | first_published_date | last_published_date | mention_share | viral_signal_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| naver_blog | 58 | 32 | 0 | 0 | 0 | 2026-03-20 | 2026-05-16 | 0.9667 | Platform-level external viral signal, not Hype. |
| youtube | 2 | 2 | 1808 | 8 | 1 | 2026-04-24 | 2026-04-24 | 0.0333 | Platform-level external viral signal, not Hype. |

## Studio/Place Viral Metrics

| matched_studio_term | confirmed_mention_count | anonymous_source_count | youtube_view_count | viral_signal_score |
| --- | --- | --- | --- | --- |
| 연희정음 | 12 | 8 | 0 | 82.75 |
| 마인드플로우 | 12 | 5 | 0 | 76.5 |
| 시이작 | 8 | 7 | 0 | 71.25 |
| 숨명상센터 | 8 | 3 | 0 | 58.75 |
| 연남장 | 5 | 5 | 0 | 56.25 |
| 빅블루요가 | 7 | 4 | 0 | 55.75 |
| 마이트리 | 4 | 4 | 0 | 46.75 |
| 너울너울 | 1 | 1 | 1480 | 39.0 |
| 대저택프라이빗 | 1 | 1 | 0 | 29.0 |
| 비전스트롤 콜라보 | 1 | 1 | 0 | 29.0 |

## Score Interpretation

`viral_signal_score` is a descriptive external-web signal only.
It is calculated from mention count, anonymous source count, YouTube reach proxy, and platform diversity.
It should be interpreted alongside reservation/review Hype, not added into it.
