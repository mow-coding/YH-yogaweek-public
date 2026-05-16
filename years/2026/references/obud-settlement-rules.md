# Obud Settlement Rules Reference

Created: 2026-05-16

## Source

This reference is transcribed from KakaoTalk screenshots and a message sent by Bigblue Yoga representative Yoo Donghwan to analyst Kim Sungkyun.

Local raw screenshot copies are stored under `years/2026/data/raw/settlement/obud/` and are excluded from GitHub by `.gitignore`.

## Public Official Document Check

On 2026-05-16, the public Obud website, FAQ, Obud Pass page, partnership inquiry page, and sitemap were checked for a publicly available settlement-rate document.

Checked URLs:

- `https://www.obud.co/`
- `https://www.obud.co/faq`
- `https://www.obud.co/obud-pass`
- `https://www.obud.co/contact/register`
- `https://www.obud.co/sitemap.xml`

Result: no public Obud settlement table or owner-facing settlement manual was found in the publicly indexed pages checked. The Obud Pass page publicly states that the pass sells the right to use services from multiple partners and that actual service delivery is the responsibility of each partner. The partnership inquiry page directs spaces needing separate consultation to Obud's Kakao channel.

Therefore, the settlement table in this project should be treated as representative-provided operating evidence, not as a public official document. Before using the estimates as accounting evidence, obtain the final Obud settlement statement or written confirmation from Obud.

## One-Time Ticket Settlement

- Obud has no separate entry, registration, or monthly platform fee for this event context.
- A fee occurs only when a reservation is made through Obud.
- One-time ticket settlement: transfer the transaction amount to the designated account after subtracting a 5% fee, three business days after the service date.
- Event one-time ticket price used in this project: 25,000 KRW.
- Estimated one-time settlement per completed use: 23,750 KRW.

## Pass Settlement

The screenshot states that pass reservations are settled according to monthly completed pass-use count from the 1st to the last day of each month.

On 2026-05-16, Kim Sungkyun asked Yoo Donghwan whether the `10회`, `100회` count is based on consumer ticket use or studio-level ticket volume. Yoo answered `소비자 기준`. Kim then reconfirmed whether the count means completed usage rather than purchased pass package, and Yoo answered `이용완료된 기준!`.

Therefore, this project records the pass settlement band as:

- basis entity: consumer, not studio;
- count type: monthly completed pass uses, not purchased pass package count;
- settlement evidence status: representative-confirmed operating rule, still not a final Obud accounting statement.

| Monthly completed pass-use count | Settlement rate |
| --- | ---: |
| 1-9 | 75% |
| 10-99 | 65% |
| 100+ | 55% |

The table is applied to the class unit price including VAT. For the first estimate in this project, 25,000 KRW is used as the default class unit price because the event one-time ticket price was 25,000 KRW.

## Remaining Limitation

The `consumer/completed-use` basis is now clarified. The remaining limitation is data coverage:

- This project only has ON STUDIO records for the 2026 Yeonhui Yoga Week event.
- Obud's actual settlement may use each consumer's full monthly Obud pass usage across all participating studios/services, not only this event.
- Therefore, project-level pass estimates are consumer-level observed-use proxies, not final accounting figures.

The final Obud settlement statement should be used before external accounting claims.
