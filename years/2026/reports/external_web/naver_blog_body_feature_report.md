# Naver Blog Body Feature Report

Generated: 2026-05-17T02:50:26+09:00

## Purpose

Use fetched Naver Blog body text to improve noise handling and qualitative interpretation.

## Inputs

- Raw body CSV: `data\raw\external_web\naver_blog_bodies_raw.csv`

## Outputs

- Internal body features: `data\interim\external_web\naver_blog_body_features_internal.csv`
- Public theme summary: `data\processed\analysis\public\yeonhui_yoga_week_naver_blog_body_theme_summary.csv`
- Public studio/body summary: `data\processed\analysis\public\yeonhui_yoga_week_naver_blog_body_studio_summary.csv`

## Result

- Body rows: 58
- Body rows containing `연희요가위크`: 56
- Body rows flagged as noise risk: 2

## Theme Summary

| primary_body_theme | mention_count | body_event_keyword_present_count |
|---|---:|---:|
| wellness_recovery | 18 | 18 |
| class_experience | 15 | 15 |
| space_experience | 12 | 10 |
| participant_review | 8 | 8 |
| visual_or_lifestyle | 3 | 3 |
| official_or_studio_promo | 2 | 2 |

## Body Studio/Place Summary

| body_matched_studio_term | mention_count |
|---|---:|
| 연희정음 | 22 |
| 마인드플로우 | 18 |
| 연남장 | 16 |
| 시이작 | 11 |
| UNMATCHED | 10 |
| 빅블루요가 | 10 |
| 숨명상센터 | 10 |
| 마이트리 | 7 |
| 대저택프라이빗 | 5 |
| 바운드하우스 | 5 |
| 비전스트롤 콜라보 | 3 |
| 너울너울 | 1 |
| 무릉 | 1 |

## Noise Handling

Rows where the title/snippet matched but body text does not contain `연희요가위크` are not automatically discarded.
They are flagged as `body_noise_risk=true` because the body extraction may miss image-only text or the event name may appear only in the title.
