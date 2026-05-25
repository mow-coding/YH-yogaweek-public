# Obud Settlement Work Log

## 2026-05-16 - Settlement rule transcription and first basis draft

### Request

The user provided representative notes and screenshots about Obud settlement rules.

Key message content:

- One-time tickets are settled after subtracting a platform fee.
- Obud pass settlement follows the pass settlement table shown in the screenshot.
- Repeated reserver frequency can be used to infer which pass size a participant likely used.

### Screenshot Transcription

One-time ticket:

- Settlement timing: three business days after the service date.
- Settlement method: apply the platform fee and use the official settlement process.
- Public outputs keep only the formula basis, not estimated final amounts.

Pass settlement table:

| Monthly completed pass-use count | Settlement rate |
| --- | ---: |
| 1-9 | 75% |
| 10-99 | 65% |
| 100+ | 55% |

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
- The partnership inquiry page directs spaces needing separate consultation to Obud's official inquiry channel.

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
- `data/processed/analysis/public/obud_settlement_basis_by_class.csv`
- `data/processed/analysis/public/obud_settlement_basis_by_owner_month.csv`
- `data/processed/analysis/public/obud_pass_package_inference_summary.csv`
- `data/processed/analysis/private/obud_pass_participant_inference_private.csv`

Raw screenshots were copied to:

- `data/raw/settlement/obud/`

The raw screenshot folder is excluded from GitHub by `.gitignore`.

### Calculation Assumptions

- Active reservation `people_count` is the public participation basis.
- Cancellation files are cancellation-history evidence only and are not subtracted again from the active reservation export.
- Public outputs keep rate bands and formula basis only.
- Participant pass package inference is separate from public settlement basis outputs and is not a confirmed purchase record.

### Verification

Generated output row counts:

- `obud_settlement_rules.csv`: 2 rows.
- `obud_pass_settlement_table.csv`: 15 rows.
- `obud_settlement_basis_by_class.csv`: 108 rows.
- `obud_settlement_basis_by_owner_month.csv`: 19 rows.
- `obud_pass_package_inference_summary.csv`: 6 rows.
- `obud_pass_participant_inference_private.csv`: 246 rows.

DuckDB was rebuilt and includes the public settlement tables.

## 2026-05-25 - Correction request applied

### Correction

Yoo Donghwan requested that the settlement package be corrected so public outputs keep participation basis and formula logic only.

Applied corrections:

- Active reservation `people_count` is the settlement participation basis.
- ON STUDIO cancellation files are used only as cancellation-history evidence and are not subtracted again from active reservations.
- Settlement owner grouping now uses `settlement_owner_key`, separate from the venue/studio bracket label.
- Bigblue-responsible classes hosted at another venue are included in the Bigblue settlement owner scope when class title or metadata identifies Bigblue/Yoo Donghwan responsibility.
- Public outputs no longer publish estimated settlement totals or amount-estimate columns.

### Verification

- `obud_settlement_basis_by_class.csv`: 108 rows.
- `obud_settlement_basis_by_owner_month.csv`: 19 rows.
- Bigblue 2026-04 owner-month row includes both `빅블루요가` and `연희정음` as hosting studio keys.
- Deprecated public estimate files were removed.

## 2026-05-16 - Follow-up clarification from Yoo Donghwan

### New clarification

Kim Sungkyun asked whether the `10회`, `100회` pass settlement bands are based on the consumer's ticket use count or the yoga studio's completed pass volume. Yoo Donghwan answered `소비자 기준`.

Kim then reconfirmed whether the count means completed usage rather than purchased pass package size. Yoo answered `이용완료된 기준!`.

### Revised interpretation

- Pass settlement band basis: consumer-level, not studio-level.
- Count type: monthly completed pass uses, not purchased pass package count.
- Remaining limitation: this project only observes ON STUDIO records for the 2026 Yeonhui Yoga Week event. Final settlement amounts must be checked against the official settlement statement or organizer-confirmed final data.

### Implementation update

`scripts/build_obud_settlement_analysis.py` was updated so that:

- class/studio completed counts keep the established reservation-minus-cancellation aggregation;
- pass settlement rates are weighted from observed consumer-month completed pass-use bands;
- outputs use `consumer_completed_use_proxy_needs_final_obud_statement` as the estimate status;
- references and reports explicitly record the `소비자 기준` and `이용완료된 기준!` clarification.
