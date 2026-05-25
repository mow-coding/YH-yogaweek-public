# Obud Settlement Basis Report

Generated: 2026-05-25

## Summary

- Current output type: participation basis and formula review only.
- Participation basis: active ON STUDIO reservation `people_count`, not reservation row count.
- Cancellation data role: cancellation history only; not subtracted again from active reservations.
- Settlement owner basis: separate `settlement_owner_key`, so Bigblue-responsible classes hosted at other venues stay in the Bigblue scope.
- Final amount policy: official settlement statement or organizer-confirmed final data only.

## Pass Rate Bands

| usage_count_band | settlement_rate | calculation_basis |
| --- | --- | --- |
| 1~9회 | 0.75 | consumer_monthly_completed_pass_use_count |
| 10~99회 | 0.65 | consumer_monthly_completed_pass_use_count |
| 100회~ | 0.55 | consumer_monthly_completed_pass_use_count |

## Settlement Owner-Month Participation Basis

| service_month | settlement_owner_key | hosting_studio_keys | one_time_participant_count | pass_participant_count | total_settlement_participant_count | pass_settlement_rate_weighted_avg |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05 | 연남장 | 연남장 | 102 | 114 | 216 | 0.7482 |
| 2026-05 | 마이트리 | 마이트리 | 76 | 107 | 183 | 0.7453 |
| 2026-04 | 마인드플로우 | 마인드플로우 | 49 | 88 | 137 | 0.7466 |
| 2026-05 | 마인드플로우 | 마인드플로우 | 64 | 69 | 133 | 0.75 |
| 2026-04 | 연남장 | 연남장 | 59 | 73 | 132 | 0.7459 |
| 2026-04 | 시이작 | 시이작 | 46 | 81 | 127 | 0.7463 |
| 2026-04 | 빅블루요가 | 빅블루요가; 연희정음 | 26 | 84 | 110 | 0.7417 |
| 2026-04 | 마이트리 | 마이트리 | 21 | 88 | 109 | 0.7477 |
| 2026-05 | 시이작 | 시이작 | 32 | 72 | 104 | 0.7472 |
| 2026-05 | 빅블루요가 | 빅블루요가 | 21 | 78 | 99 | 0.75 |
| 2026-05 | 대저택프라이빗 | 대저택프라이빗 | 31 | 67 | 98 | 0.7485 |
| 2026-04 | 연희정음 | 연희정음 | 31 | 56 | 87 | 0.7482 |
| 2026-05 | 무릉 | 무릉 | 10 | 37 | 47 | 0.75 |
| 2026-04 | 숨명상센터 | 숨명상센터 | 4 | 29 | 33 | 0.7397 |
| 2026-05 | 너울너울 | 너울너울 | 3 | 13 | 16 | 0.75 |
| 2026-04 | 너울너울 | 너울너울 | 4 | 10 | 14 | 0.75 |
| 2026-05 | 데이스타콜라보 | 데이스타콜라보 | 2 | 9 | 11 | 0.75 |
| 2026-05 | 숨명상센터 | 숨명상센터 | 4 | 7 | 11 | 0.75 |
| 2026-05 | 비전스트롤 콜라보 | 비전스트롤 콜라보 | 4 | 6 | 10 | 0.75 |

## Pass Package Inference Summary

| inferred_pass_package_bucket | participant_count | total_active_pass_participant_count | min_active_pass_participant_count | max_active_pass_participant_count |
| --- | --- | --- | --- | --- |
| 20회권 이하 참여 가능성 | 5 | 81 | 13 | 20 |
| 10회권 이하 참여 가능성 | 17 | 165 | 9 | 10 |
| 8회권 이하 참여 가능성 | 24 | 180 | 5 | 8 |
| 4회권 참여 완료 가능성 | 155 | 620 | 4 | 4 |
| 4회권 이하 참여 또는 미사용분 존재 가능 | 18 | 42 | 1 | 3 |

## Interpretation

- This is not a final accounting statement and does not publish estimated settlement totals.
- Public files keep participation counts, rate bands, formula basis, and final-statement caveats.
- Participant-level pass package inference is stored only in private output because it is a deidentified but still person-level behavioral table.

## Outputs

- `data/processed/analysis/public/obud_settlement_rules.csv`
- `data/processed/analysis/public/obud_pass_settlement_table.csv`
- `data/processed/analysis/public/obud_settlement_basis_by_class.csv`
- `data/processed/analysis/public/obud_settlement_basis_by_owner_month.csv`
- `data/processed/analysis/public/obud_pass_package_inference_summary.csv`
- `data/processed/analysis/private/obud_pass_participant_inference_private.csv`
- `references/obud-settlement-rules.md`
