from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process

from review_processing_utils import normalize_studio_key as central_normalize_studio_key


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "data" / "processed" / "analysis" / "public"
REPORT_DIR = ROOT / "reports" / "analysis"

CAPACITY = PUBLIC_DIR / "onstudio_calendar_capacity_reference.csv"
CLASS_HYPE = PUBLIC_DIR / "class_hype_metrics.csv"
STUDIO_HYPE = PUBLIC_DIR / "studio_hype_metrics.csv"
CLASS_OUTPUT = PUBLIC_DIR / "class_capacity_hype_metrics.csv"
STUDIO_OUTPUT = PUBLIC_DIR / "studio_capacity_hype_metrics.csv"
REPORT = REPORT_DIR / "capacity_hype_analysis_report.md"


STUDIO_ALIASES = {
    "데이스타콜라보|연희스페셜": "데이스타콜라보",
    "대저택 프라이빗": "대저택프라이빗",
    "마이트리|연희스페셜": "마이트리",
    "마인드플로우|연희스페셜": "마인드플로우",
    "빅블루요가|연희스페셜": "빅블루요가",
    "비전스트롤 콜라보|옥상요가": "비전스트롤 콜라보",
    "숨 명상센터": "숨명상센터",
    "시이작|어린이날 키즈요가": "시이작",
    "시이작|연희스페셜": "시이작",
    "연남장|커뮤니티허브": "연남장",
    "연희정음|랜드마크": "연희정음",
}


def normalize_text(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\([^)]*\)", "", text)
    text = text.replace("|", "")
    text = re.sub(r"[^0-9A-Za-z가-힣]", "", text)
    return text.strip()


def normalize_studio(value: str) -> str:
    text = str(value or "").strip()
    text = STUDIO_ALIASES.get(text, text)
    if "|" in text:
        text = text.split("|", 1)[0]
    text = STUDIO_ALIASES.get(text.strip(), text.strip())
    return central_normalize_studio_key(text)


def class_match_key(studio: str, title: str) -> str:
    return normalize_text(normalize_studio(studio) + normalize_text(title))


def build_capacity_by_class(capacity: pd.DataFrame) -> pd.DataFrame:
    cap = capacity.copy()
    cap["studio_key_capacity"] = cap["location_text"].map(normalize_studio)
    cap["class_title_capacity"] = cap["class_title_without_teacher"].fillna(cap["class_title_text"])
    cap["capacity_match_key"] = cap.apply(
        lambda row: class_match_key(row["studio_key_capacity"], row["class_title_capacity"]),
        axis=1,
    )
    grouped = (
        cap.groupby(["capacity_match_key"], dropna=False)
        .agg(
            studio_key_capacity=("studio_key_capacity", "first"),
            class_title_capacity=("class_title_capacity", "first"),
            capacity_session_count=("capacity", "count"),
            total_reserved_count_capacity=("reserved_count", "sum"),
            total_capacity=("capacity", "sum"),
            avg_capacity=("capacity", "mean"),
            min_capacity=("capacity", "min"),
            max_capacity=("capacity", "max"),
            avg_fill_rate=("fill_rate", "mean"),
            median_fill_rate=("fill_rate", "median"),
            sold_out_session_count=("fill_rate", lambda s: int((s >= 1.0).sum())),
            high_fill_session_count=("fill_rate", lambda s: int((s >= 0.8).sum())),
            low_fill_session_count=("fill_rate", lambda s: int((s < 0.5).sum())),
            empty_session_count=("reserved_count", lambda s: int((s == 0).sum())),
            capacity_needs_review_count=("needs_review", "sum"),
            first_class_date=("class_date", "min"),
            last_class_date=("class_date", "max"),
        )
        .reset_index()
    )
    grouped["weighted_fill_rate"] = grouped["total_reserved_count_capacity"] / grouped["total_capacity"].replace(0, pd.NA)
    grouped["sold_out_session_share"] = grouped["sold_out_session_count"] / grouped["capacity_session_count"].replace(0, pd.NA)
    grouped["high_fill_session_share"] = grouped["high_fill_session_count"] / grouped["capacity_session_count"].replace(0, pd.NA)
    return grouped


def attach_capacity_to_hype(hype: pd.DataFrame, capacity_by_class: pd.DataFrame) -> pd.DataFrame:
    result = hype.copy().reset_index(drop=False).rename(columns={"index": "_hype_row_id"})
    result["hype_match_key"] = result.apply(
        lambda row: class_match_key(row["studio_key"], row["class_title_base"]),
        axis=1,
    )
    capacity_lookup = capacity_by_class.set_index("capacity_match_key", drop=False)
    capacity_keys_by_studio = {
        studio: group["capacity_match_key"].tolist()
        for studio, group in capacity_by_class.groupby("studio_key_capacity")
    }

    match_rows = []
    for _, row in result.iterrows():
        key = row["hype_match_key"]
        studio = row["studio_key"]
        hype_row_id = row["_hype_row_id"]
        if key in capacity_lookup.index:
            cap_row = capacity_lookup.loc[key]
            if isinstance(cap_row, pd.DataFrame):
                cap_row = cap_row.iloc[0]
            match_rows.append(
                {
                    "_hype_row_id": hype_row_id,
                    "hype_match_key": key,
                    "capacity_match_key": cap_row["capacity_match_key"],
                    "capacity_match_score": 100.0,
                    "capacity_match_status": "exact_normalized",
                }
            )
            continue
        candidates = capacity_keys_by_studio.get(studio, [])
        if not candidates:
            match_rows.append(
                {
                    "_hype_row_id": hype_row_id,
                    "hype_match_key": key,
                    "capacity_match_key": "",
                    "capacity_match_score": 0.0,
                    "capacity_match_status": "no_capacity_candidate_same_studio",
                }
            )
            continue
        best = process.extractOne(key, candidates, scorer=fuzz.WRatio)
        if best and best[1] >= 88:
            match_rows.append(
                {
                    "_hype_row_id": hype_row_id,
                    "hype_match_key": key,
                    "capacity_match_key": best[0],
                    "capacity_match_score": float(best[1]),
                    "capacity_match_status": "fuzzy_same_studio",
                }
            )
        else:
            match_rows.append(
                {
                    "_hype_row_id": hype_row_id,
                    "hype_match_key": key,
                    "capacity_match_key": best[0] if best else "",
                    "capacity_match_score": float(best[1]) if best else 0.0,
                    "capacity_match_status": "needs_review",
                }
            )

    matches = pd.DataFrame(match_rows)
    result = result.merge(matches, on=["_hype_row_id", "hype_match_key"], how="left")
    result = result.merge(capacity_by_class, on="capacity_match_key", how="left")
    result["capacity_hype_segment"] = result.apply(classify_capacity_hype_segment, axis=1)
    return result


def classify_capacity_hype_segment(row: pd.Series) -> str:
    reservation_hype = row.get("reservation_hype")
    review_hype = row.get("review_hype")
    fill_rate = row.get("weighted_fill_rate")
    if pd.isna(fill_rate):
        return "capacity_missing"
    strong_hype = (pd.notna(reservation_hype) and reservation_hype >= 70) or (pd.notna(review_hype) and review_hype >= 70)
    high_fill = fill_rate >= 0.85
    low_fill = fill_rate < 0.5
    if strong_hype and high_fill:
        return "expand_or_repeat_candidate"
    if strong_hype and low_fill:
        return "message_or_schedule_review"
    if (not strong_hype) and high_fill:
        return "small_capacity_or_niche_strength"
    if low_fill:
        return "demand_development_candidate"
    return "steady_middle"


def build_studio_summary(class_metrics: pd.DataFrame, studio_hype: pd.DataFrame) -> pd.DataFrame:
    matched = class_metrics[class_metrics["capacity_match_status"].isin(["exact_normalized", "fuzzy_same_studio"])].copy()
    matched = matched.drop_duplicates(subset=["studio_key", "capacity_match_key"])
    grouped = (
        matched.groupby("studio_key", dropna=False)
        .agg(
            matched_class_count=("capacity_match_key", "nunique"),
            capacity_session_count=("capacity_session_count", "sum"),
            total_reserved_count_capacity=("total_reserved_count_capacity", "sum"),
            total_capacity=("total_capacity", "sum"),
            sold_out_session_count=("sold_out_session_count", "sum"),
            high_fill_session_count=("high_fill_session_count", "sum"),
            low_fill_session_count=("low_fill_session_count", "sum"),
            expand_or_repeat_candidate_count=(
                "capacity_hype_segment",
                lambda s: int((s == "expand_or_repeat_candidate").sum()),
            ),
            message_or_schedule_review_count=(
                "capacity_hype_segment",
                lambda s: int((s == "message_or_schedule_review").sum()),
            ),
            demand_development_candidate_count=(
                "capacity_hype_segment",
                lambda s: int((s == "demand_development_candidate").sum()),
            ),
        )
        .reset_index()
    )
    grouped["weighted_fill_rate"] = grouped["total_reserved_count_capacity"] / grouped["total_capacity"].replace(0, pd.NA)
    grouped["sold_out_session_share"] = grouped["sold_out_session_count"] / grouped["capacity_session_count"].replace(0, pd.NA)
    grouped["high_fill_session_share"] = grouped["high_fill_session_count"] / grouped["capacity_session_count"].replace(0, pd.NA)
    keep_cols = [
        "studio_key",
        "class_count",
        "reservation_count",
        "review_count",
        "reservation_hype",
        "review_hype",
        "satisfaction_hype",
        "operations_stability",
        "participant_price_proxy_krw",
    ]
    return studio_hype[keep_cols].merge(grouped, on="studio_key", how="left").sort_values(
        ["weighted_fill_rate", "reservation_hype"], ascending=False
    )


def main() -> int:
    for path in [CAPACITY, CLASS_HYPE, STUDIO_HYPE]:
        if not path.exists():
            raise SystemExit(f"Missing input: {path}")
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    capacity = pd.read_csv(CAPACITY)
    class_hype = pd.read_csv(CLASS_HYPE)
    studio_hype = pd.read_csv(STUDIO_HYPE)
    capacity_by_class = build_capacity_by_class(capacity)
    class_metrics = attach_capacity_to_hype(class_hype, capacity_by_class)
    studio_metrics = build_studio_summary(class_metrics, studio_hype)

    class_metrics.to_csv(CLASS_OUTPUT, index=False, encoding="utf-8-sig")
    studio_metrics.to_csv(STUDIO_OUTPUT, index=False, encoding="utf-8-sig")

    matched_count = int(class_metrics["capacity_match_status"].isin(["exact_normalized", "fuzzy_same_studio"]).sum())
    needs_review_count = int((class_metrics["capacity_match_status"] == "needs_review").sum())
    missing_count = int((class_metrics["capacity_match_status"] == "no_capacity_candidate_same_studio").sum())
    segment_counts = class_metrics["capacity_hype_segment"].value_counts(dropna=False)
    top_expand = class_metrics[class_metrics["capacity_hype_segment"] == "expand_or_repeat_candidate"].sort_values(
        ["weighted_fill_rate", "reservation_hype"], ascending=False
    )

    lines = [
        "# Capacity + Hype Analysis Report",
        "",
        f"작성일: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## 요약",
        "",
        f"- Hype 수업 행: {len(class_hype)}",
        f"- ON STUDIO 캘린더 정원 수업 그룹: {len(capacity_by_class)}",
        f"- 정원 자동 매칭 성공: {matched_count}",
        f"- 같은 요가원 후보 없음: {missing_count}",
        f"- 수동 검토 필요: {needs_review_count}",
        "",
        "## 반응 프로필 세그먼트",
        "",
    ]
    for segment, count in segment_counts.items():
        lines.append(f"- {segment}: {int(count)}")
    lines.extend(["", "## 확장/반복 후보 상위", ""])
    if top_expand.empty:
        lines.append("- 없음")
    else:
        for row in top_expand.head(15).itertuples(index=False):
            lines.append(
                f"- {row.class_title_base}: weighted_fill_rate={row.weighted_fill_rate:.2f}, "
                f"reservation_hype={row.reservation_hype:.2f}, review_hype={row.review_hype:.2f}, "
                f"sessions={int(row.capacity_session_count)}"
            )
    lines.extend(
        [
            "",
            "## 해석 기준",
            "",
            "- `expand_or_repeat_candidate`: Hype가 높고 정원 대비 채움률도 높아 다음 회차 확장/반복 후보.",
            "- `message_or_schedule_review`: Hype는 있으나 채움률이 낮아 시간대, 장소, 홍보 문구, 정원 설정을 점검.",
            "- `small_capacity_or_niche_strength`: 채움률은 높지만 Hype가 낮거나 중간이라 소규모 강점/니치 수업 후보.",
            "- `demand_development_candidate`: 채움률이 낮아 수요 개발 또는 기획 재검토 후보.",
            "",
            "## 산출물",
            "",
            f"- `{CLASS_OUTPUT.relative_to(ROOT)}`",
            f"- `{STUDIO_OUTPUT.relative_to(ROOT)}`",
            "",
            "## 한계",
            "",
            "- 정원은 ON STUDIO 캘린더 복사본 기준이며, 현장 노쇼나 대기자 흐름은 반영하지 못한다.",
            "- 수업명 매칭은 정규화 키와 RapidFuzz를 사용했으며, 낮은 점수는 수동 검토 대상으로 남긴다.",
            "- 채움률이 높다는 사실은 수요 신호이지만, 수업 품질이나 수익성을 단독으로 증명하지 않는다.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Class output rows: {len(class_metrics)}")
    print(f"Studio output rows: {len(studio_metrics)}")
    print(f"Matched class rows: {matched_count}")
    print(f"Needs review: {needs_review_count}")
    print(f"Report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
