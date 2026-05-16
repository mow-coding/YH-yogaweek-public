# Obud Settlement Analysis Report

Generated: 2026-05-17

## Summary

- One-time ticket fee rule: 5% platform fee; estimated settlement per completed one-time use = 23,750 KRW.
- Pass settlement rule: consumer-level monthly completed pass-use count and class unit price table.
- Default class unit price used for first estimate: 25,000 KRW.
- Current estimate status: `consumer_completed_use_estimate_needs_final_obud_statement`.

## Pass Settlement Table

| usage_count_band | settlement_rate | class_unit_price_vat_included_krw | settlement_amount_per_completed_use_krw |
| --- | --- | --- | --- |
| 1~9회 | 0.75 | 20000 | 15000 |
| 1~9회 | 0.75 | 25000 | 18750 |
| 1~9회 | 0.75 | 30000 | 22500 |
| 1~9회 | 0.75 | 35000 | 26250 |
| 1~9회 | 0.75 | 40000 | 30000 |
| 10~99회 | 0.65 | 20000 | 13000 |
| 10~99회 | 0.65 | 25000 | 16250 |
| 10~99회 | 0.65 | 30000 | 19500 |
| 10~99회 | 0.65 | 35000 | 22750 |
| 10~99회 | 0.65 | 40000 | 26000 |
| 100회~ | 0.55 | 20000 | 11000 |
| 100회~ | 0.55 | 25000 | 13750 |
| 100회~ | 0.55 | 30000 | 16500 |
| 100회~ | 0.55 | 35000 | 19250 |
| 100회~ | 0.55 | 40000 | 22000 |

## Studio-Month Settlement Estimate

| service_month | studio_key | one_time_completed_count | pass_completed_count | pass_usage_band_breakdown | pass_settlement_rate_weighted_avg | estimated_total_settlement_krw |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05 | 연남장 | 59 | 42 | 1~9회:112; 10~99회:2 | 0.7484 | 2187074 |
| 2026-05 | 마이트리 | 40 | 35 | 1~9회:102; 10~99회:5 | 0.7442 | 1601170 |
| 2026-04 | 마인드플로우 | 26 | 39 | 1~9회:81; 10~99회:3 | 0.7459 | 1344789 |
| 2026-04 | 연남장 | 29 | 34 | 1~9회:70; 10~99회:3 | 0.7456 | 1322504 |
| 2026-04 | 시이작 | 27 | 33 | 1~9회:76; 10~99회:3 | 0.7455 | 1256252 |
| 2026-05 | 마인드플로우 | 36 | 20 | 1~9회:69 | 0.75 | 1230000 |
| 2026-05 | 대저택프라이빗 | 20 | 37 | 1~9회:66; 10~99회:1 | 0.749 | 1167814 |
| 2026-04 | 마이트리 | 5 | 45 | 1~9회:84; 10~99회:2 | 0.7475 | 959724 |
| 2026-04 | 연희정음 | 13 | 27 | 1~9회:57; 10~99회:1 | 0.75 | 815000 |
| 2026-05 | 시이작 | 16 | 16 | 1~9회:70; 10~99회:2 | 0.7488 | 679535 |
| 2026-04 | 빅블루요가 | 12 | 21 | 1~9회:69; 10~99회:7 | 0.7406 | 673826 |
| 2026-05 | 무릉 | 4 | 29 | 1~9회:37 | 0.75 | 638750 |
| 2026-05 | 빅블루요가 | 7 | 14 | 1~9회:78 | 0.75 | 428750 |
| 2026-04 | 숨명상센터 | 3 | 12 | 1~9회:25; 10~99회:3 | 0.7335 | 291294 |
| 2026-05 | 숨명상센터 | 3 | 2 | 1~9회:7 | 0.75 | 108750 |
| 2026-05 | 비전스트롤 콜라보 | 4 | 0 | 1~9회:6 | 0.0 | 95000 |
| 2026-05 | 너울너울 | 0 | 3 | 1~9회:13 | 0.75 | 56250 |
| 2026-04 | 너울너울 | 2 | 0 | 1~9회:10 | 0.0 | 47500 |
| 2026-05 | 데이스타콜라보 | 0 | 0 | 1~9회:9 | 0.0 | 0 |

## Pass Package Inference Summary

| inferred_pass_package_bucket | participant_count | total_completed_pass_count | min_completed_pass_count | max_completed_pass_count |
| --- | --- | --- | --- | --- |
| 20회권 이하 사용 추정 | 2 | 34 | 14 | 20 |
| 10회권 이하 사용 추정 | 2 | 18 | 9 | 9 |
| 8회권 이하 사용 추정 | 18 | 118 | 5 | 8 |
| 4회권 사용 완료 추정 | 45 | 180 | 4 | 4 |
| 4회권 이하 사용 또는 미사용분 존재 | 102 | 247 | 1 | 3 |
| pass_completed_0_or_cancelled | 77 | 0 | 0 | 0 |

## Interpretation

- This is not a final accounting statement. It is a data-analysis estimate built from ON STUDIO reservation and cancellation records.
- Canceled reservations are subtracted by class, service month, and booking method.
- The pass calculation now uses the representative-confirmed rule: the settlement band is determined by each consumer's monthly completed pass-use count.
- This project only observes Yeonhui Yoga Week ON STUDIO records, so consumer-level pass counts are observed proxies and may be lower than Obud's full monthly platform count.
- The pass calculation uses 25,000 KRW as the default class unit price because the event one-time ticket price was 25,000 KRW.
- Participant-level pass package inference is stored only in private output because it is a deidentified but still person-level behavioral table.

## Outputs

- `data/processed/analysis/public/obud_settlement_rules.csv`
- `data/processed/analysis/public/obud_pass_settlement_table.csv`
- `data/processed/analysis/public/obud_settlement_estimate_by_class.csv`
- `data/processed/analysis/public/obud_settlement_estimate_by_studio_month.csv`
- `data/processed/analysis/public/obud_pass_package_inference_summary.csv`
- `data/processed/analysis/private/obud_pass_participant_inference_private.csv`
- `references/obud-settlement-rules.md`

## Source Caveat

The rule source is a screenshot and representative message, not a downloaded final settlement statement. A public official settlement manual was not found in the Obud pages checked on 2026-05-16. The final Obud settlement statement or written Obud confirmation should be used before external accounting claims.
