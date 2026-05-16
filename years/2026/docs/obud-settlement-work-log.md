# Obud Settlement Work Log

## 2026-05-16 - Settlement rule transcription and first estimate

### Request

The user provided KakaoTalk messages and screenshots sent by Bigblue Yoga representative Yoo Donghwan about Obud settlement rules.

Key message content:

- One-time tickets are settled after subtracting a 5% fee.
- Obud pass settlement follows the pass settlement table shown in the screenshot.
- Repeated reserver frequency can be used to infer which pass size a participant likely used.

### Screenshot Transcription

One-time ticket:

- Settlement timing: three business days after the service date.
- Settlement method: transfer the transaction amount to the designated account after subtracting a 5% fee.
- Event one-time ticket price used in the current project: 25,000 KRW.
- Estimated one-time settlement per completed use: 23,750 KRW.

Pass settlement table:

| Monthly completed pass-use count | Settlement rate | 20,000 KRW | 25,000 KRW | 30,000 KRW | 35,000 KRW | 40,000 KRW |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-9 | 75% | 15,000 | 18,750 | 22,500 | 26,250 | 30,000 |
| 10-99 | 65% | 13,000 | 16,250 | 19,500 | 22,750 | 26,000 |
| 100+ | 55% | 11,000 | 13,750 | 16,500 | 19,250 | 22,000 |

### Public Official Document Search

The public Obud website was checked for a public official settlement manual or owner-facing settlement table.

Checked:

- `https://www.obud.co/`
- `https://www.obud.co/faq`
- `https://www.obud.co/obud-pass`
- `https://www.obud.co/contact/register`
- `https://www.obud.co/sitemap.xml`

Result:

- A public settlement-rate table was not found.
- The Obud Pass page publicly states the pass sells the right to use services from multiple partners and that actual service delivery is the responsibility of each partner.
- The partnership inquiry page directs spaces needing separate consultation to Obud's Kakao channel.

Conclusion:

- The current settlement formula is treated as representative-provided operating evidence.
- Final accounting claims require the final Obud settlement statement or written confirmation from Obud.

### Implementation

Added:

- `scripts/build_obud_settlement_analysis.py`
- `references/obud-settlement-rules.md`
- `reports/analysis/obud_settlement_analysis_report.md`
- `data/processed/analysis/public/obud_settlement_rules.csv`
- `data/processed/analysis/public/obud_pass_settlement_table.csv`
- `data/processed/analysis/public/obud_settlement_estimate_by_class.csv`
- `data/processed/analysis/public/obud_settlement_estimate_by_studio_month.csv`
- `data/processed/analysis/public/obud_pass_package_inference_summary.csv`
- `data/processed/analysis/private/obud_pass_participant_inference_private.csv`

Raw screenshots were copied to:

- `data/raw/settlement/obud/`

The raw screenshot folder is excluded from GitHub by `.gitignore`.

### Calculation Assumptions

- Canceled reservations are subtracted by class, month, and booking method.
- One-time settlement uses `25,000 * 0.95 = 23,750 KRW` per completed one-time use.
- Initial assumption before follow-up clarification: pass settlement used studio-month completed pass-use count to choose the settlement rate.
- The first estimate uses 25,000 KRW as the default class unit price because the event one-time ticket price was 25,000 KRW.
- Participant pass package inference is separate from settlement estimation and is not a confirmed purchase record.

### Verification

Generated output row counts:

- `obud_settlement_rules.csv`: 2 rows.
- `obud_pass_settlement_table.csv`: 15 rows.
- `obud_settlement_estimate_by_class.csv`: 111 rows.
- `obud_settlement_estimate_by_studio_month.csv`: 21 rows.
- `obud_pass_package_inference_summary.csv`: 6 rows.
- `obud_pass_participant_inference_private.csv`: 246 rows.

DuckDB was rebuilt and includes the public settlement tables.

## 2026-05-16 - Follow-up clarification from Yoo Donghwan

### New clarification

Kim Sungkyun asked whether the `10회`, `100회` pass settlement bands are based on the consumer's ticket use count or the yoga studio's completed pass volume. Yoo Donghwan answered `소비자 기준`.

Kim then reconfirmed whether the count means completed usage rather than purchased pass package size. Yoo answered `이용완료된 기준!`.

### Revised interpretation

- Pass settlement band basis: consumer-level, not studio-level.
- Count type: monthly completed pass uses, not purchased pass package count.
- Remaining limitation: this project only observes ON STUDIO records for the 2026 Yeonhui Yoga Week event. Obud's final settlement may use each consumer's full monthly Obud pass usage across all services, so project estimates remain proxy/lower-bound analysis.

### Implementation update

`scripts/build_obud_settlement_analysis.py` was updated so that:

- class/studio completed counts keep the established reservation-minus-cancellation aggregation;
- pass settlement rates are weighted from observed consumer-month completed pass-use bands;
- outputs use `consumer_completed_use_proxy_needs_final_obud_statement` as the estimate status;
- references and reports explicitly record the `소비자 기준` and `이용완료된 기준!` clarification.
