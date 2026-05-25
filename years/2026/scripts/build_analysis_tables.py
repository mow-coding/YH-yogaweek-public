from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

from review_processing_utils import (
    ANALYSIS_PUBLIC_DIR,
    CLASS_HYPE_METRICS_PUBLIC,
    OBUD_AI_CHECKED_PRIVATE,
    OBUD_DEIDENTIFIED_PUBLIC,
    ONSTUDIO_CANCELLATIONS_PUBLIC,
    ONSTUDIO_CLASSES_PUBLIC,
    ONSTUDIO_RESERVATIONS_PUBLIC,
    REFERENCE_DIR,
    REPORT_ANALYSIS_DIR,
    STUDIO_HYPE_METRICS_PUBLIC,
    booking_method_group,
    canonical_class_key,
    canonical_class_title_display,
    compact_spaces,
    percentile_0_100,
    safe_float,
    safe_int,
    studio_key_from_class_title,
    write_csv,
    write_text,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
STUDIO_LOCATIONS_PUBLIC = ROOT_DIR / "data" / "external" / "studio_locations_public.csv"
EVENT_LOCATION_CATALOG_GIS_PUBLIC = ANALYSIS_PUBLIC_DIR / "event_location_catalog_gis.csv"
LOCATION_DISTANCE_MATRIX_PUBLIC = ANALYSIS_PUBLIC_DIR / "location_distance_matrix.csv"
CLASS_SCHEDULE_GIS_PUBLIC = ANALYSIS_PUBLIC_DIR / "class_schedule_gis.csv"
TRANSITION_FEASIBILITY_PUBLIC = ANALYSIS_PUBLIC_DIR / "transition_feasibility_public.csv"
SINGLE_TICKET_PRICE_KRW = 25_000
PASS_PER_USE_PROXY_KRW = 17_500
TICKET_PRICE_TABLE = [
    {"ticket_type": "연희요가위크 1회권", "uses": 1, "price_krw": 25_000, "per_use_price_krw": 25_000},
    {"ticket_type": "연희요가위크 4회권", "uses": 4, "price_krw": 80_000, "per_use_price_krw": 20_000},
    {"ticket_type": "연희요가위크 8회권", "uses": 8, "price_krw": 144_000, "per_use_price_krw": 18_000},
    {"ticket_type": "연희요가위크 10회권", "uses": 10, "price_krw": 170_000, "per_use_price_krw": 17_000},
    {"ticket_type": "연희요가위크 20회권", "uses": 20, "price_krw": 300_000, "per_use_price_krw": 15_000},
]


def optional_csv_count(path: Path) -> str:
    if not path.exists():
        return "미생성"
    return f"{pd.read_csv(path, dtype=str, keep_default_na=False).shape[0]}행"


def optional_manual_verification_count(path: Path) -> str:
    if not path.exists():
        return "미생성"
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    if "needs_manual_verification" not in frame.columns:
        return "컬럼 없음"
    flags = frame["needs_manual_verification"].astype(str).str.lower().isin(["true", "1", "yes"])
    return f"{int(flags.sum())}행"


def base_title_if_available(title: str, known_titles: set[str]) -> str:
    match = re.search(r"\s+\([^)]{1,40}\)$", title)
    if not match:
        return title
    candidate = title[: match.start()].strip()
    return candidate if candidate in known_titles else title


def load_known_class_titles() -> set[str]:
    titles: set[str] = set()
    classes = pd.read_csv(ONSTUDIO_CLASSES_PUBLIC, dtype=str, keep_default_na=False)
    titles.update(canonical_class_title_display(item) for item in classes["class_name"] if str(item).strip())
    for path in [ONSTUDIO_RESERVATIONS_PUBLIC, ONSTUDIO_CANCELLATIONS_PUBLIC]:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        titles.update(canonical_class_title_display(item) for item in frame["class_info_text"] if str(item).strip())
    return titles


def add_class_dimensions(frame: pd.DataFrame, known_titles: set[str]) -> pd.DataFrame:
    output = frame.copy()
    output["class_title_standard"] = output["class_info_text"].map(canonical_class_title_display)
    output["class_title_base"] = output["class_title_standard"].map(
        lambda title: canonical_class_title_display(base_title_if_available(title, known_titles))
    )
    output["class_key"] = output["class_title_standard"].map(canonical_class_key)
    output["class_base_key"] = output["class_title_base"].map(canonical_class_key)
    output["studio_key"] = output["class_title_base"].map(studio_key_from_class_title)
    output["booking_method_group"] = output["booking_method_text"].map(booking_method_group)
    output["people_count"] = output["people_count_text"].map(safe_int).fillna(1).astype(int)
    return output


def weighted_average(values: pd.Series, weights: pd.Series) -> float | None:
    numeric_values = pd.to_numeric(values, errors="coerce")
    numeric_weights = pd.to_numeric(weights, errors="coerce").fillna(0)
    valid = numeric_values.notna() & (numeric_weights > 0)
    if not valid.any():
        return None
    return float((numeric_values[valid] * numeric_weights[valid]).sum() / numeric_weights[valid].sum())


def build_public_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    reviewer_values = [value for value in reviews["masked_reviewer"].dropna().unique() if str(value).strip()]
    reviewer_map = {value: f"reviewer_{index:04d}" for index, value in enumerate(sorted(reviewer_values), start=1)}

    public = pd.DataFrame(
        {
            "review_id": reviews["review_id"],
            "review_capture_order": reviews["review_capture_order"],
            "source_image": reviews["source_image"],
            "reviewer_public_id": reviews["masked_reviewer"].map(reviewer_map).fillna(""),
            "review_date_iso": reviews["review_date_iso"],
            "visit_count": reviews["visit_count"],
            "overall_rating": reviews["overall_rating"],
            "class_rating": reviews["class_rating"],
            "atmosphere_rating": reviews["atmosphere_rating"],
            "facility_rating": reviews["facility_rating"],
            "class_title_ocr": reviews["class_title_ocr"],
            "class_title_matched": reviews["class_title_matched"],
            "class_title_base": reviews["class_title_base"],
            "class_key": reviews["class_key"],
            "class_base_key": reviews["class_base_key"],
            "studio_key": reviews["studio_key"],
            "review_text": reviews["review_text"],
            "ticket_type": reviews["ticket_type"],
            "ticket_count": reviews["ticket_count"],
            "class_match_score": reviews["class_match_score"],
            "confidence": reviews["confidence"],
            "needs_review": reviews["needs_review"],
            "ai_validation_mode": reviews["ai_validation_mode"],
            "ai_tags_json": reviews["ai_tags_json"],
            "representative_sentence": reviews["representative_sentence"],
        }
    )
    return public


def tag_count(tags: pd.Series, tag_name: str) -> int:
    count = 0
    for raw in tags.dropna():
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if payload.get(tag_name):
            count += 1
    return count


def build_class_metrics(reservations: pd.DataFrame, cancellations: pd.DataFrame, reviews: pd.DataFrame) -> pd.DataFrame:
    title_sources = []
    for priority, frame in enumerate([reservations, cancellations, reviews]):
        if frame.empty:
            continue
        subset = frame[["class_base_key", "studio_key", "class_title_base"]].copy()
        subset["source_priority"] = priority
        title_sources.append(subset)
    title_lookup = (
        pd.concat(title_sources, ignore_index=True)
        .assign(title_count=1)
        .groupby(["class_base_key", "studio_key", "class_title_base"], dropna=False)
        .agg(title_count=("title_count", "sum"), source_priority=("source_priority", "min"))
        .reset_index()
        .sort_values(["class_base_key", "studio_key", "source_priority", "title_count"], ascending=[True, True, True, False])
        .drop_duplicates(["class_base_key", "studio_key"])
    )

    reservation_group = reservations.groupby(["class_base_key", "studio_key"], dropna=False).agg(
        reservation_count=("people_count", "sum"),
        reservation_records=("people_count", "count"),
        pass_reservation_count=("booking_method_group", lambda values: int((values == "pass").sum())),
        one_time_reservation_count=("booking_method_group", lambda values: int((values == "one_time").sum())),
        unknown_reservation_count=("booking_method_group", lambda values: int((values == "unknown").sum())),
    )

    cancellation_group = cancellations.groupby(["class_base_key", "studio_key"], dropna=False).agg(
        cancellation_count=("people_count", "sum"),
        cancellation_records=("people_count", "count"),
    )

    review_group = reviews.groupby(["class_base_key", "studio_key"], dropna=False).agg(
        review_count=("review_id", "count"),
        avg_overall_rating=("overall_rating", lambda values: pd.to_numeric(values, errors="coerce").mean()),
        avg_class_rating=("class_rating", lambda values: pd.to_numeric(values, errors="coerce").mean()),
        avg_atmosphere_rating=("atmosphere_rating", lambda values: pd.to_numeric(values, errors="coerce").mean()),
        avg_facility_rating=("facility_rating", lambda values: pd.to_numeric(values, errors="coerce").mean()),
        avg_visit_count=("visit_count", lambda values: pd.to_numeric(values, errors="coerce").mean()),
        review_needs_review_count=("needs_review", lambda values: int(values.astype(str).str.lower().eq("true").sum())),
        instructor_tag_count=("ai_tags_json", lambda values: tag_count(values, "instructor")),
        space_tag_count=("ai_tags_json", lambda values: tag_count(values, "space")),
        atmosphere_tag_count=("ai_tags_json", lambda values: tag_count(values, "atmosphere")),
        difficulty_tag_count=("ai_tags_json", lambda values: tag_count(values, "difficulty")),
        recovery_tag_count=("ai_tags_json", lambda values: tag_count(values, "recovery")),
        revisit_intent_tag_count=("ai_tags_json", lambda values: tag_count(values, "revisit_intent")),
    )

    metrics = reservation_group.join(cancellation_group, how="outer").join(review_group, how="outer").reset_index()
    metrics = metrics.merge(
        title_lookup[["class_base_key", "studio_key", "class_title_base"]],
        on=["class_base_key", "studio_key"],
        how="left",
    )
    title_column = metrics.pop("class_title_base")
    metrics.insert(1, "class_title_base", title_column)
    count_columns = [
        "reservation_count",
        "reservation_records",
        "pass_reservation_count",
        "one_time_reservation_count",
        "unknown_reservation_count",
        "cancellation_count",
        "cancellation_records",
        "review_count",
        "review_needs_review_count",
        "instructor_tag_count",
        "space_tag_count",
        "atmosphere_tag_count",
        "difficulty_tag_count",
        "recovery_tag_count",
        "revisit_intent_tag_count",
    ]
    for column in count_columns:
        metrics[column] = metrics[column].fillna(0).astype(int)

    metrics["net_reservation_count"] = metrics["reservation_count"] - metrics["cancellation_count"]
    total_attempts = metrics["reservation_count"] + metrics["cancellation_count"]
    metrics["cancellation_rate"] = (metrics["cancellation_count"] / total_attempts.where(total_attempts != 0)).fillna(0)
    metrics["review_rate_per_reservation"] = (
        metrics["review_count"] / metrics["reservation_count"].where(metrics["reservation_count"] != 0)
    ).fillna(0)
    metrics["pass_reservation_share"] = (
        metrics["pass_reservation_count"] / metrics["reservation_count"].where(metrics["reservation_count"] != 0)
    ).fillna(0)
    metrics["one_time_reservation_share"] = (
        metrics["one_time_reservation_count"] / metrics["reservation_count"].where(metrics["reservation_count"] != 0)
    ).fillna(0)
    metrics["participant_price_proxy_krw"] = (
        metrics["one_time_reservation_count"] * SINGLE_TICKET_PRICE_KRW
        + metrics["pass_reservation_count"] * PASS_PER_USE_PROXY_KRW
    )

    metrics["reservation_hype"] = percentile_0_100(metrics["net_reservation_count"])
    review_count_score = percentile_0_100(metrics["review_count"])
    review_rate_score = percentile_0_100(metrics["review_rate_per_reservation"])
    metrics["review_hype"] = [
        round((count_score + rate_score) / 2, 2)
        for count_score, rate_score in zip(review_count_score, review_rate_score, strict=False)
    ]
    metrics["satisfaction_hype"] = [
        round((value / 5) * 100, 2) if pd.notna(value) else None
        for value in pd.to_numeric(metrics["avg_overall_rating"], errors="coerce")
    ]
    metrics["revisit_hype"] = percentile_0_100(metrics["avg_visit_count"])
    metrics["payment_hype"] = percentile_0_100(metrics["participant_price_proxy_krw"])
    metrics["operations_stability"] = (1 - metrics["cancellation_rate"]).clip(lower=0, upper=1).mul(100).round(2)
    metrics["price_proxy_note"] = (
        "1회권은 25,000원, 패스 예약은 회당 단가 후보의 중간값 17,500원으로 계산한 참가자 결제 반응 추정 지표"
    )

    return metrics.sort_values(["reservation_count", "review_count"], ascending=[False, False])


def build_studio_metrics(class_metrics: pd.DataFrame) -> pd.DataFrame:
    grouped_rows: list[dict[str, object]] = []
    for studio_key, group in class_metrics.groupby("studio_key", dropna=False):
        review_weight = group["review_count"]
        reservation_count = int(group["reservation_count"].sum())
        cancellation_count = int(group["cancellation_count"].sum())
        review_count = int(group["review_count"].sum())
        total_attempts = reservation_count + cancellation_count
        row = {
            "studio_key": studio_key,
            "class_count": int(group["class_base_key"].nunique()),
            "reservation_count": reservation_count,
            "cancellation_count": cancellation_count,
            "net_reservation_count": reservation_count - cancellation_count,
            "cancellation_rate": cancellation_count / total_attempts if total_attempts else 0,
            "review_count": review_count,
            "review_rate_per_reservation": review_count / reservation_count if reservation_count else 0,
            "pass_reservation_count": int(group["pass_reservation_count"].sum()),
            "one_time_reservation_count": int(group["one_time_reservation_count"].sum()),
            "participant_price_proxy_krw": int(group["participant_price_proxy_krw"].sum()),
            "avg_overall_rating": weighted_average(group["avg_overall_rating"], review_weight),
            "avg_class_rating": weighted_average(group["avg_class_rating"], review_weight),
            "avg_atmosphere_rating": weighted_average(group["avg_atmosphere_rating"], review_weight),
            "avg_facility_rating": weighted_average(group["avg_facility_rating"], review_weight),
            "avg_visit_count": weighted_average(group["avg_visit_count"], review_weight),
            "instructor_tag_count": int(group["instructor_tag_count"].sum()),
            "space_tag_count": int(group["space_tag_count"].sum()),
            "atmosphere_tag_count": int(group["atmosphere_tag_count"].sum()),
            "difficulty_tag_count": int(group["difficulty_tag_count"].sum()),
            "recovery_tag_count": int(group["recovery_tag_count"].sum()),
            "revisit_intent_tag_count": int(group["revisit_intent_tag_count"].sum()),
        }
        grouped_rows.append(row)

    metrics = pd.DataFrame(grouped_rows)
    metrics["reservation_hype"] = percentile_0_100(metrics["net_reservation_count"])
    review_count_score = percentile_0_100(metrics["review_count"])
    review_rate_score = percentile_0_100(metrics["review_rate_per_reservation"])
    metrics["review_hype"] = [
        round((count_score + rate_score) / 2, 2)
        for count_score, rate_score in zip(review_count_score, review_rate_score, strict=False)
    ]
    metrics["satisfaction_hype"] = [
        round((value / 5) * 100, 2) if value is not None and pd.notna(value) else None
        for value in metrics["avg_overall_rating"]
    ]
    metrics["revisit_hype"] = percentile_0_100(metrics["avg_visit_count"])
    metrics["payment_hype"] = percentile_0_100(metrics["participant_price_proxy_krw"])
    metrics["operations_stability"] = (1 - metrics["cancellation_rate"]).clip(lower=0, upper=1).mul(100).round(2)
    metrics["price_proxy_note"] = (
        "1회권은 25,000원, 패스 예약은 회당 단가 후보의 중간값 17,500원으로 계산한 참가자 결제 반응 추정 지표"
    )
    return metrics.sort_values(["reservation_count", "review_count"], ascending=[False, False])


def markdown_table(frame: pd.DataFrame, columns: list[str], rows: int = 10) -> str:
    if frame.empty:
        return "_데이터 없음_"
    subset = frame.head(rows)[columns].fillna("")
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body_lines = []
    for _, row in subset.iterrows():
        values = [compact_spaces(row[column]).replace("|", "/") for column in columns]
        body_lines.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *body_lines])


def write_reports(
    reservations: pd.DataFrame,
    cancellations: pd.DataFrame,
    public_reviews: pd.DataFrame,
    class_metrics: pd.DataFrame,
    studio_metrics: pd.DataFrame,
    ai_status_counts: str,
    ai_mode_counts: str,
    ai_model_counts: str,
) -> None:
    today = date.today().isoformat()
    analysis_report_path = REPORT_ANALYSIS_DIR / "yeonhui_yoga_week_analysis_report.md"
    core_lineage_report_path = REPORT_ANALYSIS_DIR / "methodology_core_analysis_generated.md"

    reservation_table = markdown_table(
        class_metrics,
        [
            "class_title_base",
            "studio_key",
            "reservation_count",
            "cancellation_count",
            "review_count",
            "avg_overall_rating",
        ],
        rows=10,
    )
    studio_table = markdown_table(
        studio_metrics,
        [
            "studio_key",
            "class_count",
            "reservation_count",
            "cancellation_count",
            "review_count",
            "avg_overall_rating",
        ],
        rows=12,
    )

    analysis_report = f"""# 2026 연희 요가 위크 1차 분석 리포트

작성일: {today}

## 1. 분석 범위
이번 1차 리포트는 ON STUDIO 예약/취소 데이터, 오붓 플랫폼 리뷰 스크린샷 96건의 Google Vision OCR 결과,
Gemini Vision 구조화 검수 결과, 티켓 가격표, 그리고 수업/요가원별 Hype 지표를 대상으로 한다.
GIS, Google Drive, SNS/블로그 Viral, 정산, Capacity, F&B/스폰서 분석은 별도 스크립트와 별도 리포트에서 다룬다.
이 파일은 예약/취소, 오붓 리뷰, Hype 지표를 재생성하는 core 분석 리포트다.

## 2. 데이터 요약
- ON STUDIO 수업 카탈로그: {pd.read_csv(ONSTUDIO_CLASSES_PUBLIC).shape[0]}건
- ON STUDIO 예약: {len(reservations)}건
- ON STUDIO 취소: {len(cancellations)}건
- 오붓 리뷰 OCR/구조화: {len(public_reviews)}건
- public 리뷰 검수 필요: {public_reviews['needs_review'].astype(str).str.lower().eq('true').sum()}건

## 3. 예약/취소/리뷰 반응이 큰 수업
{reservation_table}

## 4. 요가원별 반응 요약
{studio_table}

## 5. Hype 지수 해석법
Hype 지수는 줄세우기용 총점이 아니라 각 수업과 요가원의 반응 프로필이다.
`예약 Hype`, `리뷰 Hype`, `만족 Hype`, `재방문 Hype`, `결제 Hype`, `운영 안정성`을 따로 봐야 한다.
예를 들어 리뷰 수가 적어도 만족도가 높으면 소규모 고밀도 수업으로 해석할 수 있고,
예약은 많지만 취소율이 높으면 운영 안정성이나 시간대 적합성을 따로 점검해야 한다.

## 6. 가격/결제 기준
- 1회권: 25,000원
- 4회권: 80,000원, 회당 20,000원
- 8회권: 144,000원, 회당 18,000원
- 10회권: 170,000원, 회당 17,000원
- 20회권: 300,000원, 회당 15,000원

정산 기준표는 `scripts/build_obud_settlement_analysis.py`에서 별도 생성한다. 이 core 리포트의 `participant_price_proxy_krw`는 실제 정산액이 아니다.
1회권은 25,000원, 패스 예약은 회당 단가 후보의 중간값 17,500원으로 둔 참가자 결제 반응 추정 지표다.

## 7. 한계
- 리뷰 스크린샷은 최신순 96건이며, 플랫폼 전체 리뷰의 최종본인지 마지막 확인이 필요하다.
- Gemini Vision 구조화 검수는 96건 전부 성공했고, 규칙 기반 fallback으로 남은 행은 0건이다.
- 리뷰 작성자 실명 매칭은 private 내부 검토용이며 외부 리포트에는 개인 식별자를 포함하지 않는다.
- 취소율은 `취소 / (예약 + 취소)` 기준의 운영 지표로 계산했다.

## 8. 산출물
- public 리뷰 표: `{OBUD_DEIDENTIFIED_PUBLIC.relative_to(Path.cwd())}`
- 수업별 Hype 지표: `{CLASS_HYPE_METRICS_PUBLIC.relative_to(Path.cwd())}`
- 요가원별 Hype 지표: `{STUDIO_HYPE_METRICS_PUBLIC.relative_to(Path.cwd())}`
"""

    lineage_report = f"""# 방법론 및 데이터 계보

작성일: {today}

## 1. 처리 원칙
모든 데이터는 `원천자료 수집 -> 전처리 -> OCR -> 구조화 -> 비식별/내부 매칭 -> 분석 -> 리포트`
순서로 처리했다. public 산출물에는 전화번호, 실명, API key, 원본 스크린샷을 포함하지 않는다.

## 2. 원천자료와 접근 권한
| 자료 | 위치 | 접근/권한 | 사용 범위 |
|---|---|---|---|
| ON STUDIO 예약/취소/수업/강사 | `data/raw/onstudio/` | 축제 참여 요가원별 ON STUDIO 계정 접근 가능 | 예약/취소/수업 분석 |
| 오붓 리뷰 스크린샷 | `data/raw/obud_reviews/screenshots/` | 오붓 리뷰 화면이 마우스 드래그/텍스트 복사를 허용하지 않아 사용자가 최신순으로 직접 화면 캡처. 원본은 private/raw | OCR 및 리뷰 분석 |
| Google Vision OCR 텍스트 | `data/raw/obud_reviews/ocr_text/` | OCR API key는 로컬 파일/환경변수, 결과 원문은 raw | OCR 구조화 |
| Gemini Vision 검수 결과 | `data/processed/obud_reviews/private/obud_reviews_ai_checked_private.csv` | Gemini API key는 로컬 전용. 원본 이미지와 OCR 텍스트를 함께 사용해 JSON 구조화 검수 | 리뷰 구조화 품질 검수 |
| 티켓 가격표 | `references/obud-ticket-pricing.md` | 사용자 제공 이미지 기반 기록 | 가격 추정 기준 |
| 요가원/행사 장소 주소 | `data/external/studio_locations_public.csv` | ON STUDIO 수업 설명과 공개 웹 검색으로 수집. 최종 예약/시간표에 남은 active 장소만 GIS seed로 사용하며, 초기 기획안에만 남은 궁동산 행은 active GIS에서 제외 | GIS 1차 분석 |

## 3. 실행 스크립트 계보
| 단계 | 스크립트 | 입력 | 출력 | 현재 상태 |
|---|---|---|---|---|
| ON STUDIO 전처리 | `scripts/preprocess_onstudio.py` | `data/raw/onstudio/` | processed ON STUDIO CSV | 완료 |
| 예약/취소 비식별 | `scripts/deidentify_reservation_cancel.py` | private 예약/취소 CSV | public 비식별 CSV | 완료 |
| public DuckDB 생성 | `scripts/build_public_duckdb.py` | public CSV | `data/database/yogaweek_public.duckdb` | 완료/재실행 가능 |
| Google Vision OCR | `scripts/ocr_obud_reviews_google_vision.py` | 리뷰 스크린샷 | OCR txt/json, manifest | 완료 |
| OCR 통합표 | `scripts/build_obud_google_ocr_raw_table.py` | OCR txt | `data/interim/obud_reviews/google_vision_ocr_raw.csv` | 완료 |
| 리뷰 필드 파싱 | `scripts/parse_obud_reviews.py` | OCR raw CSV | `data/processed/obud_reviews/private/obud_reviews_extracted_private.csv` | 완료 |
| 수업명 매칭 | `scripts/match_review_classes.py` | 리뷰 파싱표, ON STUDIO 수업명 | 같은 private 리뷰표에 매칭 컬럼 추가 | 완료 |
| AI/규칙 검수 | `scripts/ai_review_quality_check.py` | 수업명 매칭 private 리뷰표 | `data/processed/obud_reviews/private/obud_reviews_ai_checked_private.csv` | 완료 |
| 리뷰 작성자 내부 매칭 | `scripts/match_reviewers_private.py` | 리뷰 private, 예약 private | `data/processed/obud_reviews/private/review_reviewer_match_private.csv` | 완료 |
| 분석 테이블/리포트 | `scripts/build_analysis_tables.py` | 예약/취소/review/가격 | public 리뷰, Hype metrics, 리포트 | 완료 |
| GIS 좌표화 | `scripts/geocode_studio_locations_arcgis.py` | `data/external/studio_locations_public.csv` | 좌표가 채워진 장소 테이블, 지오코딩 리포트 | 완료 |
| GIS 분석 | `scripts/build_gis_tables.py` | 장소 좌표, Hype metrics | GIS CSV, GeoJSON, HTML 지도, GIS 리포트 | 완료 |
| GIS 거리 행렬 | `scripts/build_gis_distance_matrix.py` | 행사 위치 카탈로그 | location nodes, distance matrix | 완료/재실행 가능 |
| GIS 시간표/동선 | `scripts/build_gis_schedule_flows.py` | 예약/취소, 거리 행렬, Hype GIS | class schedule, transition feasibility | 완료/재실행 가능 |
| GIS 심화 리포트 | `scripts/build_gis_deep_report.py` | GIS 심화 public tables | 심화 리포트, 이동 지도, 시간-공간 큐브 | 완료/재실행 가능 |

## 4. 행 수 검증
- ON STUDIO 수업: {pd.read_csv(ONSTUDIO_CLASSES_PUBLIC).shape[0]}건
- ON STUDIO 예약: {len(reservations)}건
- ON STUDIO 취소: {len(cancellations)}건
- 오붓 리뷰 public: {len(public_reviews)}건
- 수업별 Hype metrics: {len(class_metrics)}행
- 요가원별 Hype metrics: {len(studio_metrics)}행
- GIS 위치 seed: {optional_csv_count(STUDIO_LOCATIONS_PUBLIC)}
- GIS 위치 카탈로그: {optional_csv_count(EVENT_LOCATION_CATALOG_GIS_PUBLIC)}
- GIS 위치 카탈로그 중 수동 확인 필요: {optional_manual_verification_count(EVENT_LOCATION_CATALOG_GIS_PUBLIC)}
- GIS 장소 간 거리 matrix: {optional_csv_count(LOCATION_DISTANCE_MATRIX_PUBLIC)}
- GIS 수업 시간표: {optional_csv_count(CLASS_SCHEDULE_GIS_PUBLIC)}
- GIS public same-day 이동 가능성: {optional_csv_count(TRANSITION_FEASIBILITY_PUBLIC)}

## 5. 비식별 정책
- public 예약/취소 표의 이름은 `participant_####`, 전화번호는 `PHONE_MASKED`로 대체했다.
- public 리뷰 표는 `masked_reviewer`를 직접 내보내지 않고 `reviewer_####` 형태의 내부 public ID만 사용한다.
- private 작성자 매칭표에는 실명/전화번호 후보가 포함될 수 있으므로 외부 공유 대상에서 제외한다.
- OCR API key는 `.secrets/google-api.txt`, Gemini API key는 `.secrets/gemini-api.txt`에 로컬 전용으로 보관하며, `.gitignore`에서 제외한다.

## 6. AI 검수 상태
- 검수 모드별 건수:
```text
{ai_mode_counts}
```

- API 상태별 건수:
```text
{ai_status_counts}
```

- Gemini 모델별 건수:
```text
{ai_model_counts}
```

모델이 둘로 나뉜 이유는 검수 중 `gemini-2.5-flash` 호출에서 쿼터 제한이 발생했기 때문이다.
이미 성공한 24건은 보존했고, 남은 72건은 `gemini-3.1-flash-lite`로 재시도해 완료했다.
두 모델 모두 같은 Pydantic 스키마로 검증했고, 최종 public 분석표는 96건 전부 Gemini Vision 구조화 검수가 완료된 표를 기준으로 재생성했다.

## 7. 분석 지표 정의
- 순예약 수: `reservation_count - cancellation_count`
- 취소율: `cancellation_count / (reservation_count + cancellation_count)`
- 리뷰 작성률: `review_count / reservation_count`
- 예약 Hype: 순예약 수의 percentile 점수
- 리뷰 Hype: 리뷰 수 percentile과 리뷰 작성률 percentile의 평균
- 만족 Hype: 평균 전체 별점 / 5 * 100
- 재방문 Hype: 평균 방문회차 percentile
- 결제 Hype: 참가자 결제 반응 추정 지표의 percentile
- 운영 안정성: `(1 - cancellation_rate) * 100`

## 8. 재현 명령
```powershell
python scripts\\preprocess_onstudio.py
python scripts\\deidentify_reservation_cancel.py
python scripts\\ocr_obud_reviews_google_vision.py
python scripts\\build_obud_google_ocr_raw_table.py
python scripts\\parse_obud_reviews.py
python scripts\\match_review_classes.py
python scripts\\ai_review_quality_check.py --use-api
python scripts\\match_reviewers_private.py
python scripts\\build_analysis_tables.py
python scripts\\geocode_studio_locations_arcgis.py
python scripts\\build_gis_tables.py
python scripts\\build_gis_distance_matrix.py
python scripts\\build_gis_schedule_flows.py
python scripts\\build_gis_deep_report.py
python scripts\\build_public_duckdb.py
```

## 9. GIS 방법론 참고 자료
- GIS 1차 분석은 `ON STUDIO 수업 설명 주소 -> ArcGIS 지오코딩 -> 좌표/Hype 결합 -> Folium 지도/GeoJSON` 순서로 만들었다.
- 상세 참고 자료와 후속 분석 후보는 `docs/gis-method-references.md`에 기록했다.
- GIS 심화 분석은 `장소 노드 -> OSMnx 보행 거리 matrix -> 수업 시간표 -> same-day 이동 가능성 -> 이동 지도/시간-공간 큐브` 순서로 만들었다.
- 개인별 itinerary와 transition은 private 산출물로만 보관하고, public 리포트에는 장소/수업 쌍 단위 집계만 사용한다.
"""

    write_text(analysis_report_path, analysis_report)
    write_text(core_lineage_report_path, lineage_report)


def main() -> None:
    if not OBUD_AI_CHECKED_PRIVATE.exists():
        raise FileNotFoundError(
            f"Missing AI-checked private table. Run scripts/ai_review_quality_check.py first: {OBUD_AI_CHECKED_PRIVATE}"
        )

    known_titles = load_known_class_titles()
    reservations = add_class_dimensions(
        pd.read_csv(ONSTUDIO_RESERVATIONS_PUBLIC, dtype=str, keep_default_na=False), known_titles
    )
    cancellations = add_class_dimensions(
        pd.read_csv(ONSTUDIO_CANCELLATIONS_PUBLIC, dtype=str, keep_default_na=False), known_titles
    )
    reviews = pd.read_csv(OBUD_AI_CHECKED_PRIVATE, dtype=str, keep_default_na=False)

    public_reviews = build_public_reviews(reviews)
    write_csv(public_reviews, OBUD_DEIDENTIFIED_PUBLIC)

    price_table = pd.DataFrame(TICKET_PRICE_TABLE)
    write_csv(price_table, ANALYSIS_PUBLIC_DIR / "ticket_price_reference.csv")

    class_metrics = build_class_metrics(reservations, cancellations, public_reviews)
    studio_metrics = build_studio_metrics(class_metrics)
    write_csv(class_metrics, CLASS_HYPE_METRICS_PUBLIC)
    write_csv(studio_metrics, STUDIO_HYPE_METRICS_PUBLIC)

    ai_status_counts = reviews["ai_provider_status"].value_counts().to_string()
    ai_mode_counts = reviews["ai_validation_mode"].value_counts().to_string()
    ai_model_counts = reviews["ai_model"].fillna("").replace("", "unknown").value_counts().to_string()
    write_reports(
        reservations,
        cancellations,
        public_reviews,
        class_metrics,
        studio_metrics,
        ai_status_counts,
        ai_mode_counts,
        ai_model_counts,
    )

    print(f"Wrote {OBUD_DEIDENTIFIED_PUBLIC}")
    print(f"Wrote {CLASS_HYPE_METRICS_PUBLIC}")
    print(f"Wrote {STUDIO_HYPE_METRICS_PUBLIC}")
    print(f"Wrote {REPORT_ANALYSIS_DIR / 'yeonhui_yoga_week_analysis_report.md'}")
    print(f"Wrote {REPORT_ANALYSIS_DIR / 'methodology_core_analysis_generated.md'}")
    print("Preserved reports/analysis/methodology_and_data_lineage.md for integrated project lineage")


if __name__ == "__main__":
    main()
