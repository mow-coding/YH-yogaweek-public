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
CLASSES_PUBLIC = ONSTUDIO_PUBLIC_DIR / "onstudio_classes_2026_yeonhui_yoga_week.csv"

PASS_SETTLEMENT_RATES = [
    {"usage_count_min": 1, "usage_count_max": 9, "settlement_rate": 0.75},
    {"usage_count_min": 10, "usage_count_max": 99, "settlement_rate": 0.65},
    {"usage_count_min": 100, "usage_count_max": None, "settlement_rate": 0.55},
]

DEPRECATED_PUBLIC_OUTPUTS = [
    ANALYSIS_PUBLIC_DIR / ("obud_settlement_" + "estimate_by_class.csv"),
    ANALYSIS_PUBLIC_DIR / ("obud_settlement_" + "estimate_by_studio_month.csv"),
]


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


def inferred_pass_package(active_pass_count: int) -> str:
    if active_pass_count <= 0:
        return "active_pass_0"
    if active_pass_count <= 3:
        return "4회권 이하 참여 또는 미사용분 존재 가능"
    if active_pass_count == 4:
        return "4회권 참여 완료 가능성"
    if active_pass_count <= 8:
        return "8회권 이하 참여 가능성"
    if active_pass_count <= 10:
        return "10회권 이하 참여 가능성"
    if active_pass_count <= 20:
        return "20회권 이하 참여 가능성"
    return "복수 패스 또는 데이터 확인 필요"


def build_class_metadata(classes: pd.DataFrame) -> pd.DataFrame:
    metadata = classes.copy()
    metadata["class_title_base"] = metadata["class_name"].map(class_title_base)
    metadata["class_base_key"] = metadata["class_title_base"].map(canonical_key)
    metadata["class_metadata_text"] = (
        metadata["class_name"].fillna("") + " " + metadata["description_raw"].fillna("")
    )
    return metadata[["class_base_key", "class_title_base", "class_metadata_text"]].drop_duplicates(
        "class_base_key"
    )


def has_bigblue_evidence(row: pd.Series) -> bool:
    text = f"{row.get('class_title_base', '')} {row.get('class_metadata_text', '')}"
    return any(keyword in text for keyword in ["빅블루", "Big Blue", "bigblue", "BIGBLUE", "유동환"])


def settlement_owner_for_row(row: pd.Series) -> tuple[str, str]:
    if has_bigblue_evidence(row):
        return "빅블루요가", "class_title_or_metadata_contains_bigblue_or_yoo_donghwan"
    studio_key = compact_spaces(row.get("studio_key", ""))
    return studio_key, "class_bracket_studio_key"


def normalize_onstudio(frame: pd.DataFrame, source_kind: str, class_metadata: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["source_kind"] = source_kind
    output["people_count"] = output["people_count_text"].map(lambda value: safe_int(value, default=1))
    output["booking_method_group"] = output["booking_method_text"].map(booking_method_group)
    output["service_date"] = output["class_datetime_text"].map(parse_service_date)
    output["service_month"] = output["service_date"].str.slice(0, 7)
    output["class_title_base"] = output["class_info_text"].map(class_title_base)
    output["class_base_key"] = output["class_title_base"].map(canonical_key)
    output["studio_key"] = output["class_title_base"].map(canonical_studio_key_from_class_title)
    output = output.merge(
        class_metadata[["class_base_key", "class_metadata_text"]],
        on="class_base_key",
        how="left",
    )
    output["class_metadata_text"] = output["class_metadata_text"].fillna("")
    owner_values = output.apply(settlement_owner_for_row, axis=1)
    output["settlement_owner_key"] = [value[0] for value in owner_values]
    output["settlement_owner_basis"] = [value[1] for value in owner_values]
    return output


def aggregate_active_participation(reservations: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "service_month",
        "settlement_owner_key",
        "studio_key",
        "class_base_key",
        "class_title_base",
        "booking_method_group",
    ]
    return (
        reservations.groupby(group_cols, dropna=False)["people_count"]
        .sum()
        .reset_index(name="active_participant_count")
    )


def aggregate_active_participation_by_participant(reservations: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "service_month",
        "settlement_owner_key",
        "studio_key",
        "class_base_key",
        "class_title_base",
        "booking_method_group",
        "reserver_name",
    ]
    return (
        reservations.groupby(group_cols, dropna=False)["people_count"]
        .sum()
        .reset_index(name="active_participant_count")
    )


def aggregate_cancellation_history(cancellations: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["service_month", "settlement_owner_key", "studio_key", "class_base_key", "class_title_base"]
    return (
        cancellations.groupby(group_cols, dropna=False)["people_count"]
        .sum()
        .reset_index(name="cancellation_history_participant_count")
    )


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


def combine_text_values(values: pd.Series) -> str:
    return "; ".join(sorted({compact_spaces(value) for value in values if compact_spaces(value)}))


def build_pass_settlement_table() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rate_rule in PASS_SETTLEMENT_RATES:
        rows.append(
            {
                "usage_count_min": rate_rule["usage_count_min"],
                "usage_count_max": rate_rule["usage_count_max"] or "",
                "usage_count_band": pass_band_label(int(rate_rule["usage_count_min"])),
                "settlement_rate": rate_rule["settlement_rate"],
                "calculation_basis": "consumer_monthly_completed_pass_use_count",
                "public_release_note": "Rate table only; final amount must follow the official settlement statement.",
            }
        )
    return pd.DataFrame(rows)


def build_rule_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "booking_method_group": "one_time",
                "participation_basis": "ON STUDIO active reservation people_count or official final statement participant count",
                "formula_summary": "published one-time ticket amount minus platform fee, applied only in official settlement review",
                "public_release_note": "Public outputs do not publish estimated totals or account-level details.",
                "needs_confirmation": False,
            },
            {
                "booking_method_group": "pass",
                "participation_basis": "ON STUDIO active reservation people_count or official final statement participant count",
                "formula_summary": "consumer monthly completed pass-use band determines settlement rate",
                "public_release_note": "Public outputs show participation basis and rate bands only.",
                "needs_confirmation": False,
            },
        ]
    )


def build_settlement_basis(
    reservations: pd.DataFrame,
    cancellations: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    counts = aggregate_active_participation(reservations)
    participant_counts = aggregate_active_participation_by_participant(reservations)
    participant_month_pass = (
        participant_counts[participant_counts["booking_method_group"] == "pass"]
        .groupby(["service_month", "reserver_name"], dropna=False)["active_participant_count"]
        .sum()
        .reset_index(name="consumer_month_pass_participation_count_for_rate")
    )
    participant_month_pass["pass_usage_band"] = participant_month_pass[
        "consumer_month_pass_participation_count_for_rate"
    ].map(pass_band_label)
    participant_month_pass["pass_settlement_rate"] = participant_month_pass[
        "consumer_month_pass_participation_count_for_rate"
    ].map(pass_rate_for_count)

    pass_reservation_class = (
        reservations[reservations["booking_method_group"] == "pass"]
        .groupby(
            [
                "service_month",
                "settlement_owner_key",
                "studio_key",
                "class_base_key",
                "class_title_base",
                "reserver_name",
            ],
            dropna=False,
        )["people_count"]
        .sum()
        .reset_index(name="observed_pass_participant_count_for_rate_weight")
    )
    pass_reservation_class = pass_reservation_class.merge(
        participant_month_pass,
        on=["service_month", "reserver_name"],
        how="left",
    )
    pass_rate_source = pass_reservation_class[
        pass_reservation_class["consumer_month_pass_participation_count_for_rate"].fillna(0).astype(int) > 0
    ].copy()
    pass_rate_source["pass_settlement_rate"] = pass_rate_source["pass_settlement_rate"].fillna(0)
    pass_rate_source["weighted_rate_numerator"] = (
        pass_rate_source["observed_pass_participant_count_for_rate_weight"]
        * pass_rate_source["pass_settlement_rate"]
    )

    pass_rate_group_cols = [
        "service_month",
        "settlement_owner_key",
        "studio_key",
        "class_base_key",
        "class_title_base",
    ]
    pass_rate_by_class = (
        pass_rate_source.groupby(pass_rate_group_cols, dropna=False)
        .agg(
            observed_pass_participant_count_for_rate_weight=(
                "observed_pass_participant_count_for_rate_weight",
                "sum",
            ),
            weighted_rate_numerator=("weighted_rate_numerator", "sum"),
            consumer_month_pass_participation_count_min=(
                "consumer_month_pass_participation_count_for_rate",
                "min",
            ),
            consumer_month_pass_participation_count_max=(
                "consumer_month_pass_participation_count_for_rate",
                "max",
            ),
        )
        .reset_index()
    )
    pass_breakdown = (
        pass_rate_source.groupby(pass_rate_group_cols, dropna=False)
        .apply(
            lambda group: band_breakdown(
                group["pass_usage_band"],
                group["observed_pass_participant_count_for_rate_weight"],
            ),
            include_groups=False,
        )
        .reset_index(name="pass_usage_band_breakdown")
    )
    pass_rate_by_class = pass_rate_by_class.merge(pass_breakdown, on=pass_rate_group_cols, how="left")
    pass_rate_by_class["pass_settlement_rate_weighted_avg"] = (
        pass_rate_by_class["weighted_rate_numerator"]
        / pass_rate_by_class["observed_pass_participant_count_for_rate_weight"].replace(0, pd.NA)
    ).astype("Float64").fillna(0).round(4)

    pivot = counts.pivot_table(
        index=["service_month", "settlement_owner_key", "studio_key", "class_base_key", "class_title_base"],
        columns="booking_method_group",
        values="active_participant_count",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    for column in ["one_time", "pass", "unknown"]:
        if column not in pivot.columns:
            pivot[column] = 0
    pivot = pivot.rename(
        columns={
            "one_time": "one_time_participant_count",
            "pass": "pass_participant_count",
            "unknown": "unknown_participant_count",
        }
    )

    enriched = pivot.merge(pass_rate_by_class, on=pass_rate_group_cols, how="left").fillna(
        {
            "pass_usage_band_breakdown": "",
            "pass_settlement_rate_weighted_avg": 0,
            "observed_pass_participant_count_for_rate_weight": 0,
            "weighted_rate_numerator": 0,
        }
    )
    cancellation_history = aggregate_cancellation_history(cancellations)
    enriched = enriched.merge(cancellation_history, on=pass_rate_group_cols, how="left").fillna(
        {"cancellation_history_participant_count": 0}
    )

    count_columns = [
        "one_time_participant_count",
        "pass_participant_count",
        "unknown_participant_count",
        "observed_pass_participant_count_for_rate_weight",
        "cancellation_history_participant_count",
    ]
    for column in count_columns:
        enriched[column] = enriched[column].astype(int)
    enriched["total_settlement_participant_count"] = (
        enriched["one_time_participant_count"]
        + enriched["pass_participant_count"]
        + enriched["unknown_participant_count"]
    )
    fallback_rate_mask = (enriched["pass_participant_count"] > 0) & (
        enriched["pass_settlement_rate_weighted_avg"] == 0
    )
    enriched.loc[fallback_rate_mask, "pass_settlement_rate_weighted_avg"] = pass_rate_for_count(1)
    enriched.loc[fallback_rate_mask, "pass_usage_band_breakdown"] = "1~9회:fallback"
    enriched["settlement_basis_status"] = "basis_only_no_public_settlement_amount"
    enriched["assumption_note"] = (
        "Settlement participation uses active reservation people_count. "
        "Cancellation rows are retained only as cancellation history and are not subtracted again. "
        "Final amounts must use the official settlement statement or organizer-confirmed final data."
    )

    owner_basis = reservations[
        ["service_month", "settlement_owner_key", "studio_key", "class_base_key", "settlement_owner_basis"]
    ].drop_duplicates()
    enriched = enriched.merge(
        owner_basis,
        on=["service_month", "settlement_owner_key", "studio_key", "class_base_key"],
        how="left",
    )

    owner_month = (
        enriched.groupby(["service_month", "settlement_owner_key"], dropna=False)
        .agg(
            class_count=("class_base_key", "nunique"),
            hosting_studio_count=("studio_key", "nunique"),
            hosting_studio_keys=("studio_key", combine_text_values),
            one_time_participant_count=("one_time_participant_count", "sum"),
            pass_participant_count=("pass_participant_count", "sum"),
            unknown_participant_count=("unknown_participant_count", "sum"),
            total_settlement_participant_count=("total_settlement_participant_count", "sum"),
            cancellation_history_participant_count=("cancellation_history_participant_count", "sum"),
            pass_usage_band_breakdown=("pass_usage_band_breakdown", combine_band_breakdowns),
            observed_pass_participant_count_for_rate_weight=(
                "observed_pass_participant_count_for_rate_weight",
                "sum",
            ),
            weighted_rate_numerator=("weighted_rate_numerator", "sum"),
        )
        .reset_index()
    )
    owner_month["pass_settlement_rate_weighted_avg"] = (
        owner_month["weighted_rate_numerator"]
        / owner_month["observed_pass_participant_count_for_rate_weight"].replace(0, pd.NA)
    ).astype("Float64").fillna(0).round(4)
    owner_month["settlement_basis_status"] = "basis_only_no_public_settlement_amount"
    owner_month["assumption_note"] = enriched["assumption_note"].iloc[0] if not enriched.empty else ""

    class_columns = [
        "service_month",
        "settlement_owner_key",
        "studio_key",
        "class_base_key",
        "class_title_base",
        "one_time_participant_count",
        "pass_participant_count",
        "unknown_participant_count",
        "total_settlement_participant_count",
        "cancellation_history_participant_count",
        "observed_pass_participant_count_for_rate_weight",
        "consumer_month_pass_participation_count_min",
        "consumer_month_pass_participation_count_max",
        "pass_usage_band_breakdown",
        "pass_settlement_rate_weighted_avg",
        "settlement_owner_basis",
        "settlement_basis_status",
        "assumption_note",
    ]
    owner_columns = [
        "service_month",
        "settlement_owner_key",
        "class_count",
        "hosting_studio_count",
        "hosting_studio_keys",
        "one_time_participant_count",
        "pass_participant_count",
        "unknown_participant_count",
        "total_settlement_participant_count",
        "cancellation_history_participant_count",
        "pass_usage_band_breakdown",
        "pass_settlement_rate_weighted_avg",
        "settlement_basis_status",
        "assumption_note",
    ]

    class_sort_cols = ["total_settlement_participant_count", "pass_participant_count", "one_time_participant_count"]
    owner_sort_cols = ["total_settlement_participant_count", "pass_participant_count", "one_time_participant_count"]
    return (
        enriched[class_columns].sort_values(class_sort_cols, ascending=False),
        owner_month[owner_columns].sort_values(owner_sort_cols, ascending=False),
    )


def build_pass_package_inference(reservations: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    participant = (
        reservations[reservations["booking_method_group"] == "pass"]
        .groupby(["reserver_name"], dropna=False)["people_count"]
        .sum()
        .reset_index(name="active_pass_participant_count")
    )
    participant["active_pass_participant_count"] = participant["active_pass_participant_count"].astype(int)
    participant["inferred_pass_package_bucket"] = participant["active_pass_participant_count"].map(
        inferred_pass_package
    )
    participant["inference_note"] = (
        "Derived from deidentified active pass reservations. This is not a confirmed purchase record."
    )
    summary = (
        participant.groupby("inferred_pass_package_bucket", dropna=False)
        .agg(
            participant_count=("reserver_name", "count"),
            total_active_pass_participant_count=("active_pass_participant_count", "sum"),
            min_active_pass_participant_count=("active_pass_participant_count", "min"),
            max_active_pass_participant_count=("active_pass_participant_count", "max"),
        )
        .reset_index()
        .sort_values(["max_active_pass_participant_count", "participant_count"], ascending=False)
    )
    return participant.sort_values("active_pass_participant_count", ascending=False), summary


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
    owner_month: pd.DataFrame,
    package_summary: pd.DataFrame,
) -> None:
    reference = """# Obud Settlement Basis Reference

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
"""
    write_text(REFERENCE_DIR / "obud-settlement-rules.md", reference)

    report = f"""# Obud Settlement Basis Report

Generated: {date.today().isoformat()}

## Summary

- Current output type: participation basis and formula review only.
- Participation basis: active ON STUDIO reservation `people_count`, not reservation row count.
- Cancellation data role: cancellation history only; not subtracted again from active reservations.
- Settlement owner basis: separate `settlement_owner_key`, so Bigblue-responsible classes hosted at other venues stay in the Bigblue scope.
- Final amount policy: official settlement statement or organizer-confirmed final data only.

## Pass Rate Bands

{markdown_table(pass_table, ["usage_count_band", "settlement_rate", "calculation_basis"], rows=10)}

## Settlement Owner-Month Participation Basis

{markdown_table(owner_month, ["service_month", "settlement_owner_key", "hosting_studio_keys", "one_time_participant_count", "pass_participant_count", "total_settlement_participant_count", "pass_settlement_rate_weighted_avg"], rows=20)}

## Pass Package Inference Summary

{markdown_table(package_summary, ["inferred_pass_package_bucket", "participant_count", "total_active_pass_participant_count", "min_active_pass_participant_count", "max_active_pass_participant_count"], rows=20)}

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
"""
    write_text(REPORT_DIR / "obud_settlement_analysis_report.md", report)


def remove_deprecated_outputs() -> None:
    for path in DEPRECATED_PUBLIC_OUTPUTS:
        if path.exists():
            path.unlink()


def main() -> None:
    class_metadata = build_class_metadata(read_csv(CLASSES_PUBLIC))
    reservations = normalize_onstudio(read_csv(RESERVATIONS_PUBLIC), "reservation", class_metadata)
    cancellations = normalize_onstudio(read_csv(CANCELLATIONS_PUBLIC), "cancellation_history", class_metadata)

    pass_table = build_pass_settlement_table()
    rule_summary = build_rule_summary()
    class_basis, owner_month_basis = build_settlement_basis(reservations, cancellations)
    participant_inference, package_summary = build_pass_package_inference(reservations)

    remove_deprecated_outputs()
    write_csv(rule_summary, ANALYSIS_PUBLIC_DIR / "obud_settlement_rules.csv")
    write_csv(pass_table, ANALYSIS_PUBLIC_DIR / "obud_pass_settlement_table.csv")
    write_csv(class_basis, ANALYSIS_PUBLIC_DIR / "obud_settlement_basis_by_class.csv")
    write_csv(owner_month_basis, ANALYSIS_PUBLIC_DIR / "obud_settlement_basis_by_owner_month.csv")
    write_csv(package_summary, ANALYSIS_PUBLIC_DIR / "obud_pass_package_inference_summary.csv")
    write_csv(participant_inference, ANALYSIS_PRIVATE_DIR / "obud_pass_participant_inference_private.csv")
    write_reference_and_report(pass_table, owner_month_basis, package_summary)

    print("Created Obud settlement basis outputs")
    print(f"Class basis rows: {len(class_basis)}")
    print(f"Owner-month basis rows: {len(owner_month_basis)}")
    print(f"Pass package inference rows: {len(participant_inference)}")


if __name__ == "__main__":
    main()
