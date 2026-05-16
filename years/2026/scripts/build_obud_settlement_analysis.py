from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

from review_processing_utils import (
    canonical_class_key,
    canonical_class_title_display,
    studio_key_from_class_title as canonical_studio_key_from_class_title,
)


ROOT = Path(__file__).resolve().parents[1]
ONSTUDIO_PUBLIC_DIR = ROOT / "data" / "processed" / "onstudio" / "public"
ANALYSIS_PUBLIC_DIR = ROOT / "data" / "processed" / "analysis" / "public"
ANALYSIS_PRIVATE_DIR = ROOT / "data" / "processed" / "analysis" / "private"
REPORT_DIR = ROOT / "reports" / "analysis"
REFERENCE_DIR = ROOT / "references"

RESERVATIONS_PUBLIC = ONSTUDIO_PUBLIC_DIR / "onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv"
CANCELLATIONS_PUBLIC = ONSTUDIO_PUBLIC_DIR / "onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv"

ONE_TIME_TICKET_PRICE_KRW = 25_000
ONE_TIME_FEE_RATE = 0.05
DEFAULT_CLASS_UNIT_PRICE_KRW = 25_000

PASS_SETTLEMENT_RATES = [
    {"usage_count_min": 1, "usage_count_max": 9, "settlement_rate": 0.75},
    {"usage_count_min": 10, "usage_count_max": 99, "settlement_rate": 0.65},
    {"usage_count_min": 100, "usage_count_max": None, "settlement_rate": 0.55},
]
PASS_CLASS_UNIT_PRICES = [20_000, 25_000, 30_000, 35_000, 40_000]


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def compact_spaces(value: object) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def safe_int(value: object, default: int = 0) -> int:
    match = re.search(r"-?\d+", str(value).replace(",", ""))
    return int(match.group(0)) if match else default


def booking_method_group(value: object) -> str:
    text = str(value)
    if "1회권" in text:
        return "one_time"
    if "패스" in text:
        return "pass"
    return "unknown"


def studio_key_from_class_title(class_title: object) -> str:
    return canonical_studio_key_from_class_title(class_title)


def class_title_base(class_title: object) -> str:
    title = compact_spaces(class_title)
    base = re.sub(r"\s+\([^)]{1,40}\)$", "", title).strip()
    return canonical_class_title_display(base)


def canonical_key(value: object) -> str:
    return canonical_class_key(value)


def parse_service_date(value: object) -> str:
    match = re.search(r"(?P<month>\d{1,2})\.(?P<day>\d{1,2})", str(value))
    if not match:
        return ""
    month = int(match.group("month"))
    day = int(match.group("day"))
    return date(2026, month, day).isoformat()


def pass_rate_for_count(count: int) -> float | None:
    if count <= 0:
        return None
    if count >= 100:
        return 0.55
    if count >= 10:
        return 0.65
    return 0.75


def pass_band_label(count: int) -> str:
    if count <= 0:
        return "0"
    if count >= 100:
        return "100회~"
    if count >= 10:
        return "10~99회"
    return "1~9회"


def inferred_pass_package(completed_pass_count: int) -> str:
    if completed_pass_count <= 0:
        return "pass_completed_0_or_cancelled"
    if completed_pass_count <= 3:
        return "4회권 이하 사용 또는 미사용분 존재"
    if completed_pass_count == 4:
        return "4회권 사용 완료 추정"
    if completed_pass_count <= 8:
        return "8회권 이하 사용 추정"
    if completed_pass_count <= 10:
        return "10회권 이하 사용 추정"
    if completed_pass_count <= 20:
        return "20회권 이하 사용 추정"
    return "복수 패스 또는 데이터 확인 필요"


def build_pass_settlement_table() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rate_rule in PASS_SETTLEMENT_RATES:
        for price in PASS_CLASS_UNIT_PRICES:
            rows.append(
                {
                    "usage_count_min": rate_rule["usage_count_min"],
                    "usage_count_max": rate_rule["usage_count_max"] or "",
                    "usage_count_band": pass_band_label(int(rate_rule["usage_count_min"])),
                    "settlement_rate": rate_rule["settlement_rate"],
                    "class_unit_price_vat_included_krw": price,
                    "settlement_amount_per_completed_use_krw": int(price * rate_rule["settlement_rate"]),
                    "source": "obud settlement screenshot provided by Bigblue Yoga representative",
                }
            )
    return pd.DataFrame(rows)


def build_rule_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "booking_method_group": "one_time",
                "rule_summary": "1회권 결제는 이용일 기준 영업일 3일 후 지정 계좌로 5% 수수료 제외 후 거래액 이체",
                "ticket_price_krw": ONE_TIME_TICKET_PRICE_KRW,
                "platform_fee_rate": ONE_TIME_FEE_RATE,
                "settlement_amount_per_completed_use_krw": int(ONE_TIME_TICKET_PRICE_KRW * (1 - ONE_TIME_FEE_RATE)),
                "settlement_timing": "이용일 기준 영업일 3일 후",
                "needs_confirmation": False,
            },
            {
                "booking_method_group": "pass",
                "rule_summary": "패스 예약은 소비자 개인의 매월 1일~말일까지 패스 이용 완료 건수에 따라 패스 정산 테이블 기준 정산",
                "ticket_price_krw": "",
                "platform_fee_rate": "",
                "settlement_amount_per_completed_use_krw": "",
                "settlement_timing": "월 단위 정산",
                "needs_confirmation": False,
            },
        ]
    )


def normalize_onstudio(frame: pd.DataFrame, source_kind: str) -> pd.DataFrame:
    output = frame.copy()
    output["source_kind"] = source_kind
    output["people_count"] = output["people_count_text"].map(lambda value: safe_int(value, default=1))
    output["booking_method_group"] = output["booking_method_text"].map(booking_method_group)
    output["service_date"] = output["class_datetime_text"].map(parse_service_date)
    output["service_month"] = output["service_date"].str.slice(0, 7)
    output["class_title_base"] = output["class_info_text"].map(class_title_base)
    output["class_base_key"] = output["class_title_base"].map(canonical_key)
    output["studio_key"] = output["class_title_base"].map(studio_key_from_class_title)
    return output


def aggregate_completed_counts(reservations: pd.DataFrame, cancellations: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["service_month", "studio_key", "class_base_key", "class_title_base", "booking_method_group"]
    reservation_group = (
        reservations.groupby(group_cols, dropna=False)["people_count"].sum().reset_index(name="reservation_count")
    )
    cancellation_group = (
        cancellations.groupby(group_cols, dropna=False)["people_count"].sum().reset_index(name="cancellation_count")
    )
    merged = reservation_group.merge(cancellation_group, on=group_cols, how="outer").fillna(0)
    merged["reservation_count"] = merged["reservation_count"].astype(int)
    merged["cancellation_count"] = merged["cancellation_count"].astype(int)
    merged["completed_count"] = (merged["reservation_count"] - merged["cancellation_count"]).clip(lower=0).astype(int)
    return merged


def aggregate_completed_counts_by_participant(reservations: pd.DataFrame, cancellations: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "service_month",
        "studio_key",
        "class_base_key",
        "class_title_base",
        "booking_method_group",
        "reserver_name",
    ]
    reservation_group = (
        reservations.groupby(group_cols, dropna=False)["people_count"].sum().reset_index(name="reservation_count")
    )
    cancellation_group = (
        cancellations.groupby(group_cols, dropna=False)["people_count"].sum().reset_index(name="cancellation_count")
    )
    merged = reservation_group.merge(cancellation_group, on=group_cols, how="outer").fillna(0)
    merged["reservation_count"] = merged["reservation_count"].astype(int)
    merged["cancellation_count"] = merged["cancellation_count"].astype(int)
    merged["completed_count"] = (merged["reservation_count"] - merged["cancellation_count"]).clip(lower=0).astype(int)
    return merged


def band_breakdown(labels: pd.Series, counts: pd.Series) -> str:
    bucket: dict[str, int] = {}
    for label, count in zip(labels, counts):
        label_text = str(label)
        count_int = int(count)
        if count_int <= 0 or label_text in {"0", "", "nan", "<NA>"}:
            continue
        bucket[label_text] = bucket.get(label_text, 0) + count_int
    return "; ".join(f"{label}:{count}" for label, count in sorted(bucket.items())) or ""


def combine_band_breakdowns(values: pd.Series) -> str:
    bucket: dict[str, int] = {}
    for value in values:
        for label, count in re.findall(r"(1~9회|10~99회|100회~):(\d+)", str(value)):
            bucket[label] = bucket.get(label, 0) + int(count)
    order = ["1~9회", "10~99회", "100회~"]
    return "; ".join(f"{label}:{bucket[label]}" for label in order if label in bucket)


def build_settlement_estimates(counts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    reservations = normalize_onstudio(read_csv(RESERVATIONS_PUBLIC), "reservation")
    cancellations = normalize_onstudio(read_csv(CANCELLATIONS_PUBLIC), "cancellation")
    participant_counts = aggregate_completed_counts_by_participant(reservations, cancellations)
    participant_month_pass = (
        participant_counts[participant_counts["booking_method_group"] == "pass"]
        .groupby(["service_month", "reserver_name"], dropna=False)["completed_count"]
        .sum()
        .reset_index(name="consumer_month_pass_completed_count_for_rate")
    )
    participant_month_pass["pass_usage_band"] = participant_month_pass[
        "consumer_month_pass_completed_count_for_rate"
    ].map(pass_band_label)
    participant_month_pass["pass_settlement_rate"] = participant_month_pass[
        "consumer_month_pass_completed_count_for_rate"
    ].map(pass_rate_for_count)

    # We can identify the consumer-month band from repeated pass reservations, but the raw copied
    # tables do not have a unique booking id that lets us allocate cancellations to exact rows.
    # Therefore class/studio completed counts stay on the established aggregate reservation-cancel
    # basis, while rates are weighted from observed consumer-month pass usage among reservations.
    pass_reservation_class = (
        reservations[reservations["booking_method_group"] == "pass"]
        .groupby(
            ["service_month", "studio_key", "class_base_key", "class_title_base", "reserver_name"],
            dropna=False,
        )["people_count"]
        .sum()
        .reset_index(name="observed_pass_reservation_count_for_rate_weight")
    )
    pass_reservation_class = pass_reservation_class.merge(
        participant_month_pass,
        on=["service_month", "reserver_name"],
        how="left",
    )
    pass_rate_source = pass_reservation_class[
        pass_reservation_class["consumer_month_pass_completed_count_for_rate"].fillna(0).astype(int) > 0
    ].copy()
    pass_rate_source["pass_settlement_rate"] = pass_rate_source["pass_settlement_rate"].fillna(0)
    pass_rate_source["weighted_rate_numerator"] = (
        pass_rate_source["observed_pass_reservation_count_for_rate_weight"]
        * pass_rate_source["pass_settlement_rate"]
    )

    pass_rate_by_class = (
        pass_rate_source.groupby(
            ["service_month", "studio_key", "class_base_key", "class_title_base"],
            dropna=False,
        )
        .agg(
            observed_pass_reservation_count_for_rate_weight=(
                "observed_pass_reservation_count_for_rate_weight",
                "sum",
            ),
            weighted_rate_numerator=("weighted_rate_numerator", "sum"),
            consumer_month_pass_completed_count_min=("consumer_month_pass_completed_count_for_rate", "min"),
            consumer_month_pass_completed_count_max=("consumer_month_pass_completed_count_for_rate", "max"),
        )
        .reset_index()
    )
    pass_breakdown = (
        pass_rate_source.groupby(
            ["service_month", "studio_key", "class_base_key", "class_title_base"],
            dropna=False,
        )
        .apply(
            lambda group: band_breakdown(
                group["pass_usage_band"],
                group["observed_pass_reservation_count_for_rate_weight"],
            )
        )
        .reset_index(name="pass_usage_band_breakdown")
    )
    pass_rate_by_class = pass_rate_by_class.merge(
        pass_breakdown,
        on=["service_month", "studio_key", "class_base_key", "class_title_base"],
        how="left",
    )
    pass_rate_by_class["pass_settlement_rate_weighted_avg"] = (
        pass_rate_by_class["weighted_rate_numerator"]
        / pass_rate_by_class["observed_pass_reservation_count_for_rate_weight"].replace(0, pd.NA)
    ).astype("Float64").fillna(0).round(4)

    pivot = counts.pivot_table(
        index=["service_month", "studio_key", "class_base_key", "class_title_base"],
        columns="booking_method_group",
        values="completed_count",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    for column in ["one_time", "pass", "unknown"]:
        if column not in pivot.columns:
            pivot[column] = 0

    pivot = pivot.rename(
        columns={
            "one_time": "one_time_completed_count",
            "pass": "pass_completed_count",
            "unknown": "unknown_completed_count",
        }
    )

    enriched = pivot.merge(
        pass_rate_by_class,
        on=["service_month", "studio_key", "class_base_key", "class_title_base"],
        how="left",
    ).fillna(
        {
            "pass_usage_band_breakdown": "",
            "pass_settlement_rate_weighted_avg": 0,
            "observed_pass_reservation_count_for_rate_weight": 0,
            "weighted_rate_numerator": 0,
        }
    )
    count_columns = [
        "one_time_completed_count",
        "unknown_completed_count",
        "pass_completed_count",
    ]
    for column in count_columns:
        enriched[column] = enriched[column].astype(int)

    enriched["class_unit_price_vat_included_krw"] = DEFAULT_CLASS_UNIT_PRICE_KRW
    enriched["class_unit_price_source"] = "event 1회권 price default; verify if class-specific list price differs"
    enriched["one_time_settlement_per_use_krw"] = int(ONE_TIME_TICKET_PRICE_KRW * (1 - ONE_TIME_FEE_RATE))
    fallback_rate_mask = (enriched["pass_completed_count"] > 0) & (
        enriched["pass_settlement_rate_weighted_avg"] == 0
    )
    enriched.loc[fallback_rate_mask, "pass_settlement_rate_weighted_avg"] = pass_rate_for_count(1)
    enriched.loc[fallback_rate_mask, "pass_usage_band_breakdown"] = "1~9회:fallback"
    enriched["pass_settlement_per_use_krw_weighted_avg"] = (
        enriched["class_unit_price_vat_included_krw"] * enriched["pass_settlement_rate_weighted_avg"]
    ).astype("Float64").fillna(0).round(0)
    enriched["estimated_one_time_settlement_krw"] = (
        enriched["one_time_completed_count"] * enriched["one_time_settlement_per_use_krw"]
    )
    enriched["estimated_pass_settlement_krw"] = (
        enriched["pass_completed_count"] * enriched["pass_settlement_per_use_krw_weighted_avg"]
    ).round(0).astype(int)
    enriched["estimated_total_settlement_krw"] = (
        enriched["estimated_one_time_settlement_krw"] + enriched["estimated_pass_settlement_krw"]
    )
    enriched["settlement_estimate_status"] = "consumer_completed_use_estimate_needs_final_obud_statement"
    enriched["assumption_note"] = (
        "Canceled reservations are subtracted by class/month/method. "
        "Pass settlement band is clarified as consumer-level monthly completed pass-use count. "
        "This project only observes Yeonhui Yoga Week ON STUDIO records, not each consumer's full Obud monthly usage, "
        "so the pass estimate is a lower-bound estimate until the final Obud settlement statement is available."
    )

    studio_month = (
        enriched.groupby(["service_month", "studio_key"], dropna=False)
        .agg(
            class_count=("class_base_key", "nunique"),
            one_time_completed_count=("one_time_completed_count", "sum"),
            pass_completed_count=("pass_completed_count", "sum"),
            unknown_completed_count=("unknown_completed_count", "sum"),
            estimated_one_time_settlement_krw=("estimated_one_time_settlement_krw", "sum"),
            estimated_pass_settlement_krw=("estimated_pass_settlement_krw", "sum"),
            estimated_total_settlement_krw=("estimated_total_settlement_krw", "sum"),
            pass_usage_band_breakdown=("pass_usage_band_breakdown", combine_band_breakdowns),
            class_unit_price_vat_included_krw=("class_unit_price_vat_included_krw", "first"),
        )
        .reset_index()
    )
    studio_month["pass_settlement_rate_weighted_avg"] = (
        studio_month["estimated_pass_settlement_krw"]
        / (studio_month["pass_completed_count"].replace(0, pd.NA) * DEFAULT_CLASS_UNIT_PRICE_KRW)
    ).astype("Float64").fillna(0).round(4)
    studio_month["settlement_estimate_status"] = "consumer_completed_use_estimate_needs_final_obud_statement"
    studio_month["assumption_note"] = enriched["assumption_note"].iloc[0] if not enriched.empty else ""

    sort_cols = ["estimated_total_settlement_krw", "pass_completed_count", "one_time_completed_count"]
    return (
        enriched.sort_values(sort_cols, ascending=False),
        studio_month.sort_values(sort_cols, ascending=False),
    )


def build_pass_package_inference(reservations: pd.DataFrame, cancellations: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    group_cols = ["reserver_name"]
    reservation_group = (
        reservations[reservations["booking_method_group"] == "pass"]
        .groupby(group_cols, dropna=False)["people_count"]
        .sum()
        .reset_index(name="pass_reservation_count")
    )
    cancellation_group = (
        cancellations[cancellations["booking_method_group"] == "pass"]
        .groupby(group_cols, dropna=False)["people_count"]
        .sum()
        .reset_index(name="pass_cancellation_count")
    )
    participant = reservation_group.merge(cancellation_group, on=group_cols, how="outer").fillna(0)
    participant["pass_reservation_count"] = participant["pass_reservation_count"].astype(int)
    participant["pass_cancellation_count"] = participant["pass_cancellation_count"].astype(int)
    participant["completed_pass_count"] = (
        participant["pass_reservation_count"] - participant["pass_cancellation_count"]
    ).clip(lower=0).astype(int)
    participant["inferred_pass_package_bucket"] = participant["completed_pass_count"].map(inferred_pass_package)
    participant["inference_note"] = (
        "Derived from deidentified repeated pass reservations. This is not a confirmed purchase record."
    )
    summary = (
        participant.groupby("inferred_pass_package_bucket", dropna=False)
        .agg(
            participant_count=("reserver_name", "count"),
            total_completed_pass_count=("completed_pass_count", "sum"),
            min_completed_pass_count=("completed_pass_count", "min"),
            max_completed_pass_count=("completed_pass_count", "max"),
        )
        .reset_index()
        .sort_values(["max_completed_pass_count", "participant_count"], ascending=False)
    )
    return participant.sort_values("completed_pass_count", ascending=False), summary


def markdown_table(frame: pd.DataFrame, columns: list[str], rows: int = 10) -> str:
    subset = frame.head(rows)[columns].copy()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for _, row in subset.iterrows():
        values = [compact_spaces(row[column]).replace("|", "/") for column in columns]
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *body])


def write_reference_and_report(
    pass_table: pd.DataFrame,
    studio_month: pd.DataFrame,
    package_summary: pd.DataFrame,
) -> None:
    reference = """# Obud Settlement Rules Reference

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
"""
    write_text(REFERENCE_DIR / "obud-settlement-rules.md", reference)

    report = f"""# Obud Settlement Analysis Report

Generated: {date.today().isoformat()}

## Summary

- One-time ticket fee rule: 5% platform fee; estimated settlement per completed one-time use = 23,750 KRW.
- Pass settlement rule: consumer-level monthly completed pass-use count and class unit price table.
- Default class unit price used for first estimate: 25,000 KRW.
- Current estimate status: `consumer_completed_use_estimate_needs_final_obud_statement`.

## Pass Settlement Table

{markdown_table(pass_table, ["usage_count_band", "settlement_rate", "class_unit_price_vat_included_krw", "settlement_amount_per_completed_use_krw"], rows=15)}

## Studio-Month Settlement Estimate

{markdown_table(studio_month, ["service_month", "studio_key", "one_time_completed_count", "pass_completed_count", "pass_usage_band_breakdown", "pass_settlement_rate_weighted_avg", "estimated_total_settlement_krw"], rows=20)}

## Pass Package Inference Summary

{markdown_table(package_summary, ["inferred_pass_package_bucket", "participant_count", "total_completed_pass_count", "min_completed_pass_count", "max_completed_pass_count"], rows=20)}

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
"""
    write_text(REPORT_DIR / "obud_settlement_analysis_report.md", report)


def main() -> None:
    reservations = normalize_onstudio(read_csv(RESERVATIONS_PUBLIC), "reservation")
    cancellations = normalize_onstudio(read_csv(CANCELLATIONS_PUBLIC), "cancellation")

    pass_table = build_pass_settlement_table()
    rule_summary = build_rule_summary()
    counts = aggregate_completed_counts(reservations, cancellations)
    class_estimate, studio_month_estimate = build_settlement_estimates(counts)
    participant_inference, package_summary = build_pass_package_inference(reservations, cancellations)

    write_csv(rule_summary, ANALYSIS_PUBLIC_DIR / "obud_settlement_rules.csv")
    write_csv(pass_table, ANALYSIS_PUBLIC_DIR / "obud_pass_settlement_table.csv")
    write_csv(class_estimate, ANALYSIS_PUBLIC_DIR / "obud_settlement_estimate_by_class.csv")
    write_csv(studio_month_estimate, ANALYSIS_PUBLIC_DIR / "obud_settlement_estimate_by_studio_month.csv")
    write_csv(package_summary, ANALYSIS_PUBLIC_DIR / "obud_pass_package_inference_summary.csv")
    write_csv(participant_inference, ANALYSIS_PRIVATE_DIR / "obud_pass_participant_inference_private.csv")
    write_reference_and_report(pass_table, studio_month_estimate, package_summary)

    print("Created Obud settlement reference and estimates")
    print(f"Class estimate rows: {len(class_estimate)}")
    print(f"Studio-month estimate rows: {len(studio_month_estimate)}")
    print(f"Pass package inference rows: {len(participant_inference)}")


if __name__ == "__main__":
    main()
