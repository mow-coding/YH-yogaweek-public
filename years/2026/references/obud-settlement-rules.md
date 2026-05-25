# Obud Settlement Basis Reference

Created: 2026-05-25

## Source And Scope

This reference summarizes representative-provided settlement operating rules and the 2026-05-25 correction memo.

Local raw screenshots and private source messages are excluded from GitHub. Public outputs must not include final settlement amounts, account-level details, private conversation text, or estimated settlement totals that could be mistaken for final accounting values.

## Corrected Participation Basis

- Settlement participation is based on active ON STUDIO reservations' `people_count` or the organizer's official final participant count.
- ON STUDIO cancellation files are cancellation-history evidence only. They must not be subtracted again from the active reservation export.
- Reservation row count is not the participation count because one reservation row can contain multiple people.
- Settlement grouping uses `settlement_owner_key`, not only the venue/studio label in brackets.
- Bigblue Yoga scope includes classes hosted elsewhere when class title or class metadata identifies Bigblue/Yoo Donghwan responsibility.

## Public Rule Summary

| Booking method | Public basis |
| --- | --- |
| one_time | Active participant count and public formula basis only; final amount is official-statement-only |
| pass | Consumer monthly completed pass-use band determines rate; public output keeps rate bands and participant counts only |

## Pass Rate Bands

| Monthly completed pass-use count | Settlement rate |
| --- | ---: |
| 1-9 | 75% |
| 10-99 | 65% |
| 100+ | 55% |

## Final Amount Rule

The public release is not a final settlement statement. Actual final settlement amounts must be managed separately from the public package and verified only against the official settlement statement or organizer-confirmed final data.
