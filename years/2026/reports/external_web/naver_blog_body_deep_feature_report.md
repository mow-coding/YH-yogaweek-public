# Naver Blog Body Deep Feature Report

Generated: 2026-05-17T02:50:32+09:00

## Purpose

Use full Naver Blog body text to judge whether each confirmed post is a real 2026 Yeonhui Yoga Week mention,
how deeply the author wrote about the experience, and whether the post looks like a thin or mixed-context mention.

## Inputs

- Raw body CSV: `data\raw\external_web\naver_blog_bodies_raw.csv`
- Basic body features: `data\interim\external_web\naver_blog_body_features_internal.csv`

## Outputs

- Internal deep features: `data\interim\external_web\naver_blog_body_deep_features_internal.csv`
- Public deep features without source URL/body text: `data\processed\analysis\public\yeonhui_yoga_week_naver_blog_body_deep_features_public.csv`
- Public post type summary: `data\processed\analysis\public\yeonhui_yoga_week_naver_blog_body_post_type_summary.csv`
- Public quality summary: `data\processed\analysis\public\yeonhui_yoga_week_naver_blog_body_quality_summary.csv`

## Result

- Body rows analyzed: 58
- Strong/basic body-confirmed rows: 56
- High-depth participant/context rows: 30
- Positive or very positive tone rows: 47
- Manual review recommended rows: 5

## Post Type Summary

| interpretive_post_type | mention_count | average_relevance_score | average_depth_score | average_emotional_intensity_score | manual_review_recommended_count |
| --- | --- | --- | --- | --- | --- |
| immersive_participant_review | 18 | 94.44 | 93.5 | 74.0 | 0 |
| participant_experience_review | 16 | 90.19 | 71.5 | 39.81 | 0 |
| space_or_program_overview | 8 | 74.62 | 54.12 | 27.0 | 0 |
| event_reference_or_light_review | 7 | 72.14 | 33.57 | 22.71 | 0 |
| official_or_promotional_notice | 4 | 96.75 | 72.0 | 49.75 | 0 |
| mixed_context_event_mention | 3 | 68.67 | 49.0 | 36.67 | 3 |
| title_only_or_extraction_gap | 2 | 32.0 | 53.5 | 20.0 | 2 |

## Quality Summary

| body_relevance_level | experience_depth_label | sentiment_tone | mention_count | manual_review_recommended_count | average_body_text_chars |
| --- | --- | --- | --- | --- | --- |
| confirmed_body_strong | high_depth | very_positive | 15 | 0 | 2380.47 |
| confirmed_body_strong | high_depth | positive | 8 | 0 | 1623.5 |
| confirmed_body_strong | medium_depth | positive | 7 | 0 | 773.14 |
| confirmed_body_basic | high_depth | very_positive | 3 | 0 | 1993.67 |
| confirmed_body_basic | low_depth | positive | 3 | 1 | 945.67 |
| confirmed_body_basic | medium_depth | very_positive | 3 | 1 | 1141.0 |
| confirmed_body_basic | medium_depth | neutral_or_unclear | 2 | 0 | 734.0 |
| confirmed_body_basic | medium_depth | positive | 2 | 0 | 580.5 |
| confirmed_body_basic | thin_reference | neutral_or_unclear | 2 | 0 | 142.5 |
| confirmed_body_strong | high_depth | neutral_or_unclear | 2 | 0 | 1072.0 |
| confirmed_body_strong | medium_depth | very_positive | 2 | 0 | 1311.0 |
| confirmed_body_basic | high_depth | positive | 1 | 0 | 1960.0 |
| confirmed_body_basic | low_depth | mixed | 1 | 0 | 888.0 |
| confirmed_body_basic | thin_reference | positive | 1 | 0 | 298.0 |
| confirmed_body_strong | low_depth | mixed | 1 | 0 | 488.0 |
| confirmed_body_strong | low_depth | neutral_or_unclear | 1 | 0 | 726.0 |
| confirmed_body_strong | low_depth | positive | 1 | 1 | 899.0 |
| confirmed_body_strong | medium_depth | neutral_or_unclear | 1 | 0 | 894.0 |
| needs_review_title_only | high_depth | negative_or_disappointed | 1 | 1 | 1176.0 |
| needs_review_title_only | low_depth | positive | 1 | 1 | 534.0 |

## Interpretation Notes

These scores are transparent rule-based proxies. They are intended for filtering, triage, and comparison,
not as a final human sentiment judgment. Raw body text is kept out of public outputs.
