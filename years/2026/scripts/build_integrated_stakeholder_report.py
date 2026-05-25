from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


YEAR_DIR = Path(__file__).resolve().parents[1]
PUBLIC_ANALYSIS = YEAR_DIR / "data" / "processed" / "analysis" / "public"
PUBLIC_ONSTUDIO = YEAR_DIR / "data" / "processed" / "onstudio" / "public"
PUBLIC_REVIEWS = YEAR_DIR / "data" / "processed" / "obud_reviews" / "public"
PRIVATE_REVIEWS = YEAR_DIR / "data" / "processed" / "obud_reviews" / "private"
REPORT_PATH = YEAR_DIR / "reports" / "stakeholders" / "yeonhui_yoga_week_integrated_stakeholder_report.md"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def fmt_int(value: float | int | str | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{int(round(float(value))):,}"


def fmt_money(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{int(round(float(value))):,}원"


def fmt_pct(value: float | int | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value) * 100:.{decimals}f}%"


def fmt_score(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):.2f}"


def md_table(headers: list[str], rows: Iterable[Iterable[object]]) -> str:
    def cell(value: object) -> str:
        text = "" if value is None else str(value)
        return text.replace("\n", " ").replace("|", "&#124;")

    out = [
        "| " + " | ".join(cell(header) for header in headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(value) for value in row) + " |")
    return "\n".join(out)


def top_rows(df: pd.DataFrame, sort_col: str, cols: list[str], n: int = 5) -> pd.DataFrame:
    if df.empty or sort_col not in df.columns:
        return pd.DataFrame(columns=cols)
    return df.sort_values(sort_col, ascending=False).head(n)[cols]


def count_review_tags(reviews: pd.DataFrame) -> dict[str, int]:
    counts = {
        "강사": 0,
        "공간": 0,
        "분위기": 0,
        "난이도": 0,
        "회복감": 0,
        "재참여 의향": 0,
    }
    key_map = {
        "instructor": "강사",
        "space": "공간",
        "atmosphere": "분위기",
        "difficulty": "난이도",
        "recovery": "회복감",
        "revisit_intent": "재참여 의향",
    }
    if "ai_tags_json" not in reviews.columns:
        return counts
    for raw in reviews["ai_tags_json"].fillna("{}"):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for key, label in key_map.items():
            if parsed.get(key):
                counts[label] += 1
    return counts


def main() -> None:
    classes = read_csv(PUBLIC_ONSTUDIO / "onstudio_classes_2026_yeonhui_yoga_week.csv")
    reservations = read_csv(PUBLIC_ONSTUDIO / "onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv")
    cancellations = read_csv(PUBLIC_ONSTUDIO / "onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv")
    reviews = read_csv(PUBLIC_REVIEWS / "obud_reviews_deidentified.csv")
    ai_private = read_csv(PRIVATE_REVIEWS / "obud_reviews_ai_checked_private.csv")
    class_hype = read_csv(PUBLIC_ANALYSIS / "class_hype_metrics.csv")
    studio_hype = read_csv(PUBLIC_ANALYSIS / "studio_hype_metrics.csv")
    class_capacity = read_csv(PUBLIC_ANALYSIS / "class_capacity_hype_metrics.csv")
    studio_capacity = read_csv(PUBLIC_ANALYSIS / "studio_capacity_hype_metrics.csv")
    viral_overall = read_csv(PUBLIC_ANALYSIS / "yeonhui_yoga_week_viral_overall_summary.csv")
    viral_studio = read_csv(PUBLIC_ANALYSIS / "yeonhui_yoga_week_viral_studio_metrics.csv")
    distance = read_csv(PUBLIC_ANALYSIS / "location_distance_matrix.csv")
    transitions = read_csv(PUBLIC_ANALYSIS / "transition_feasibility_public.csv")
    location_transitions = read_csv(PUBLIC_ANALYSIS / "location_transition_feasibility_public.csv")
    location_nodes = read_csv(PUBLIC_ANALYSIS / "location_nodes.csv")
    schedule = read_csv(PUBLIC_ANALYSIS / "class_schedule_gis.csv")
    fnb = read_csv(PUBLIC_ANALYSIS / "fnb_partner_brands_public.csv")
    sponsor_assets = read_csv(PUBLIC_ANALYSIS / "sponsor_asset_inventory_public.csv")
    drive_opportunities = read_csv(PUBLIC_ANALYSIS / "google_drive_archive_analysis_opportunity_matrix.csv")
    notion_pages = read_csv(PUBLIC_ANALYSIS / "notion_shared_page_summary_public.csv")
    notion_themes = read_csv(PUBLIC_ANALYSIS / "notion_shared_communication_theme_summary_public.csv")
    capacity_compare = read_csv(PUBLIC_ANALYSIS / "capacity_reference_comparison.csv")
    settlement = read_csv(PUBLIC_ANALYSIS / "obud_settlement_estimate_by_studio_month.csv")

    ai_model_counts = {}
    if not ai_private.empty and "ai_model" in ai_private.columns:
        ai_model_counts = ai_private["ai_model"].value_counts().to_dict()
    ai_fallback_count = 0
    if not ai_private.empty and "ai_validation_mode" in ai_private.columns:
        ai_fallback_count = int((ai_private["ai_validation_mode"] == "rule_based_fallback").sum())
    ai_needs_review = 0
    if not ai_private.empty and "needs_review" in ai_private.columns:
        ai_needs_review = int(ai_private["needs_review"].fillna(False).astype(bool).sum())

    review_tag_counts = count_review_tags(reviews)
    overall_review_avg = reviews["overall_rating"].mean() if "overall_rating" in reviews.columns else None
    class_review_avg = reviews["class_rating"].mean() if "class_rating" in reviews.columns else None
    atmosphere_review_avg = reviews["atmosphere_rating"].mean() if "atmosphere_rating" in reviews.columns else None
    facility_review_avg = reviews["facility_rating"].mean() if "facility_rating" in reviews.columns else None
    avg_visit_count = reviews["visit_count"].mean() if "visit_count" in reviews.columns else None

    cap_segments = {}
    if "capacity_hype_segment" in class_capacity.columns:
        cap_segments = class_capacity["capacity_hype_segment"].value_counts().to_dict()

    settlement_total = settlement["estimated_total_settlement_krw"].sum() if "estimated_total_settlement_krw" in settlement.columns else None
    settlement_one_time = settlement["one_time_completed_count"].sum() if "one_time_completed_count" in settlement.columns else None
    settlement_pass = settlement["pass_completed_count"].sum() if "pass_completed_count" in settlement.columns else None

    viral_row = viral_overall.iloc[0].to_dict() if len(viral_overall) else {}
    comfortable_count = int((transitions.get("feasibility_status", pd.Series(dtype=str)) == "comfortable").sum()) if not transitions.empty else 0
    tight_count = int((transitions.get("feasibility_status", pd.Series(dtype=str)) == "tight").sum()) if not transitions.empty else 0
    difficult_count = int((transitions.get("feasibility_status", pd.Series(dtype=str)) == "difficult").sum()) if not transitions.empty else 0
    no_gap_count = int((transitions.get("feasibility_status", pd.Series(dtype=str)) == "no_gap").sum()) if not transitions.empty else 0

    walk_pairs = distance.copy()
    if not walk_pairs.empty and "origin_location_key" in walk_pairs.columns and "destination_location_key" in walk_pairs.columns:
        walk_pairs = walk_pairs[walk_pairs["origin_location_key"] != walk_pairs["destination_location_key"]]
    avg_walk_minutes = walk_pairs["walk_minutes"].mean() if "walk_minutes" in walk_pairs.columns and not walk_pairs.empty else None
    max_walk = top_rows(walk_pairs, "walk_minutes", ["origin_display_name", "destination_display_name", "walk_minutes"], 1)
    max_walk_desc = "-"
    if len(max_walk):
        row = max_walk.iloc[0]
        max_walk_desc = f"{row['origin_display_name']} -> {row['destination_display_name']} {fmt_score(row['walk_minutes'])}분"

    reservation_top = top_rows(
        studio_hype,
        "reservation_count",
        ["studio_key", "reservation_count", "review_count", "avg_overall_rating", "reservation_hype"],
        6,
    )
    review_density_top = top_rows(
        studio_hype,
        "review_rate_per_reservation",
        ["studio_key", "reservation_count", "review_count", "review_rate_per_reservation", "review_hype"],
        6,
    )
    satisfaction_top = top_rows(
        studio_hype,
        "satisfaction_hype",
        ["studio_key", "reservation_count", "review_count", "avg_overall_rating", "satisfaction_hype"],
        6,
    )
    capacity_top = top_rows(
        studio_capacity,
        "weighted_fill_rate",
        [
            "studio_key",
            "reservation_count",
            "review_count",
            "weighted_fill_rate",
            "sold_out_session_count",
            "capacity_session_count",
            "expand_or_repeat_candidate_count",
        ],
        8,
    )
    viral_top = top_rows(
        viral_studio,
        "viral_signal_score",
        ["matched_studio_term", "confirmed_mention_count", "viral_signal_score", "first_published_date", "last_published_date"],
        8,
    )
    settlement_top = top_rows(
        settlement,
        "estimated_total_settlement_krw",
        [
            "service_month",
            "studio_key",
            "one_time_completed_count",
            "pass_completed_count",
            "pass_settlement_rate_weighted_avg",
            "estimated_total_settlement_krw",
        ],
        8,
    )
    review_class_top = (
        reviews.groupby(["studio_key", "class_title_base"], dropna=False)
        .size()
        .reset_index(name="review_count")
        .sort_values("review_count", ascending=False)
        .head(10)
        if not reviews.empty and {"studio_key", "class_title_base"}.issubset(reviews.columns)
        else pd.DataFrame(columns=["studio_key", "class_title_base", "review_count"])
    )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = []
    lines.append("# 2026 연희 요가 위크 통합 분석 보고서")
    lines.append("")
    lines.append(f"작성일: {generated_at}")
    lines.append("")
    lines.append("대상 행사: 2026 연희 요가 위크")
    lines.append("")
    lines.append("보고서 버전: 1차 분석 통합본")
    lines.append("")
    lines.append("공유 등급: 공개용. 원본 자료, 내부 매칭표, API key, 전화번호, 원본 스크린샷, 원문 URL은 제외한다.")
    lines.append("")
    lines.append("## 1. 책임과 수행 범위")
    lines.append("")
    lines.append(md_table(
        ["구분", "조직/소속", "이름", "계정", "이 보고서에서의 의미"],
        [
            ["책임자/관리자", "빅블루 요가", "유동환", "`bigblue.yoga@gmail.com`", "프로젝트 데이터 수집과 관리의 책임 주체. Google Drive 자료는 이 계정에서 공유받은 자료만 수집 대상으로 삼았다."],
            ["분석 담당자", "빅블루 요가", "김성균", "`mow.coding@gmail.com`", "로컬 전처리, OCR, AI 검수, Hype, GIS, 외부 확산, 정원, 정산 추정 분석과 보고서 작성을 수행한 담당자."],
        ],
    ))
    lines.append("")
    lines.append("**공개 안전 원칙:** 이 보고서는 원본 데이터를 그대로 공개하는 문서가 아니다. 외부 공유본에는 실명, 전화번호, API key, 원본 스크린샷, 내부 리뷰 매칭표, Google Drive/Notion/웹 원문을 포함하지 않는다. 예약자 실명과 전화번호는 공개용 표에서 제거했고, 리뷰 작성자도 외부 공유용 ID로 대체했다. Google Drive와 Notion 원문은 내부 검증용으로만 보관하고, 외부에는 집계와 요약만 사용한다.")
    lines.append("")
    lines.append("## 2. 한 문장 결론")
    lines.append("")
    lines.append("2026 연희 요가 위크는 단순히 여러 요가원이 수업을 많이 연 행사가 아니라, 연희동의 요가원, 공간, F&B, 플랫폼, 참가자가 함께 만든 지역 기반 웰니스 네트워크 실험이었다. 예약과 취소, 리뷰, 정원, 공간 이동성, 외부 웹 언급, 스폰서/F&B 접점을 함께 보면 차기 회차는 더 촘촘한 시간표, 더 명확한 스폰서십 측정, 더 안전한 데이터 수집 구조로 발전시킬 수 있다.")
    lines.append("")
    lines.append("## 3. 이 보고서를 읽는 9가지 관점")
    lines.append("")
    lines.append("이 보고서는 9개의 별도 보고서가 아니라 하나의 통합 보고서다. 다만 독자마다 관심사가 다르므로, 아래처럼 서로 다른 질문에 답하도록 구성했다.")
    lines.append("")
    lines.append(md_table(
        ["독자", "읽어야 할 핵심", "전달 메시지"],
        [
            ["2026 참여 요가원", "수업 반응, 정원 대비 채움률, 리뷰, 취소율", "각 요가원은 서로 다른 방식으로 축제의 밀도를 만들었다. 다음 회차에는 강점별로 시간표와 정원을 조정할 수 있다."],
            ["2026 공식 파트너", "예약 플랫폼, 공간 허브, 데이터 구조", "파트너십은 단순 노출이 아니라 지역 웰니스 실험을 데이터로 함께 축적하는 구조였다."],
            ["2026 공식 스폰서", "F&B/굿즈 접점, 동선, 리뷰/바이럴 확산", "스폰서십은 물품 제공을 넘어 참가자의 이동과 기억 속에 브랜드 접점을 설계하는 장치가 될 수 있다."],
            ["2026 참가자", "리뷰 반영, 개인정보 보호, 다음 개선", "참가자의 예약과 리뷰는 다음 축제의 수업 구성, 장소 안내, 이동 동선 개선에 사용된다."],
            ["차기 참여 희망 요가원", "작은 수업의 강점, 리뷰 밀도, 반복 후보", "대형 수업만 유리한 구조가 아니다. 소규모 수업도 만족도와 재방문 신호로 강점을 보여줄 수 있다."],
            ["차기 공식 파트너 후보", "플랫폼, 공간, 로컬 커뮤니티, 데이터 결합", "연희 요가 위크는 예약, 공간, 콘텐츠, 지역 상권을 연결하는 협업 실험장이다."],
            ["차기 공식 스폰서 후보", "측정 가능한 스폰서십 설계", "쿠폰, 굿즈, F&B 루트, 수업 테마 연계형 스폰서십은 다음 회차부터 성과 측정 구조로 설계할 수 있다."],
            ["차기 일반 참가자", "기대 가능한 경험", "한 곳에서 끝나는 행사가 아니라 연희동 여러 공간을 걸으며 수련, 음악, 명상, 식음 경험을 엮는 축제다."],
            ["공공기관", "민간 주도 지역 축제의 공공적 가능성", "관 주도 행사는 아니지만 건강문화, 생활권 문화, 지역상권, 민간 협력 모델을 보여주는 기초 근거가 있다."],
        ],
    ))
    lines.append("")
    lines.append("## 4. 분석 방법은 왜 이렇게 설계했나")
    lines.append("")
    lines.append("행사 분석은 단순히 순위를 매기는 일이 아니다. 이번 분석은 세 가지 표준적 사고방식을 축소 적용했다.")
    lines.append("")
    lines.append("첫째, 프로그램 평가 방식이다. CDC Program Evaluation Framework는 이해관계자 참여, 프로그램 설명, 평가 질문 설정, 신뢰 가능한 근거 수집, 결론 도출, 활용과 공유를 강조한다. 이 프로젝트에서는 그 흐름을 따라 예약, 리뷰, 정원, 공간, 외부 확산, 스폰서 자료를 함께 추적했다.")
    lines.append("")
    lines.append("둘째, 이벤트 임팩트 평가 방식이다. GOV.UK의 major event impact and legacy toolkit과 eventIMPACTS Toolkit은 행사 전후 자료 수집, 참석/미디어/사회적 신호, 평가 계획의 중요성을 강조한다. 다만 연희 요가 위크는 민간 주도 소규모 지역 축제이므로 경제효과를 과장하지 않고, 실제로 확보한 운영 데이터와 공개 웹 신호만 사용했다.")
    lines.append("")
    lines.append("셋째, 재현 가능한 데이터 계보 방식이다. 원자료가 어디서 왔는지, 어떤 스크립트가 어떤 공개용 표를 만들었는지, 어떤 파일은 외부 공유 금지인지 기록했다. 초보자가 보더라도 `원천자료 -> 스크립트 -> 공개용 가공표 -> 보고서`의 흐름을 따라가며 같은 결과를 다시 확인할 수 있게 만드는 것이 목표다.")
    lines.append("")
    lines.append("주요 참고 자료: [CDC Program Evaluation Framework](https://www.cdc.gov/mmwr/volumes/73/rr/rr7306a1.htm), [GOV.UK Major Event Impact and Legacy Toolkit](https://www.gov.uk/government/publications/measuring-the-legacy-and-impact-of-major-events-a-toolkit/measuring-the-legacy-and-impact-of-major-events-a-toolkit), [eventIMPACTS](https://www.eventimpacts.com/impact-types), [OSMnx documentation](https://osmnx.readthedocs.io/en/stable/).")
    lines.append("")
    lines.append("## 5. 원천자료 수집과 전처리")
    lines.append("")
    lines.append(md_table(
        ["축", "원천자료", "수집/처리 방식", "외부 공유 방식"],
        [
            ["ON STUDIO 예약/취소", f"예약 {fmt_int(len(reservations))}건, 취소 {fmt_int(len(cancellations))}건", "플랫폼에 CSV 내보내기가 없어 화면 정보를 수동 복사해 표준 컬럼으로 정리했다.", "실명은 `participant_####`, 전화번호는 `PHONE_MASKED`로 바꾼 뒤 집계/비식별 표만 공유"],
            ["수업 정보", f"ON STUDIO 수업 {fmt_int(len(classes))}건", "수업명, 요가원, 장소, 시간 정보를 표준화했다.", "수업/요가원/장소 단위 공유 가능"],
            ["오붓 리뷰", f"스크린샷 {fmt_int(len(reviews))}건", "오붓 리뷰 화면에서 드래그 복사가 되지 않아 최신순으로 스크린샷을 저장했다. 이후 Google Vision OCR, Gemini Vision 구조화 검수, RapidFuzz 수업명 매칭을 적용했다.", "리뷰 작성자 실명 확정표는 내부용으로만 보관하고, 공개본에는 비식별 리뷰와 집계만 공유"],
            ["정원/채움률", f"ON STUDIO 캘린더 {fmt_int(len(capacity_compare))}행", "ON STUDIO 캘린더 복사 자료와 Google Drive 기획표를 대조했다. 실제 운영 기준은 ON STUDIO 캘린더를 우선했다.", "수업별 정원, 예약수, 채움률 집계만 공유"],
            ["GIS", f"행사 장소 {fmt_int(len(location_nodes))}곳", "공개 주소를 기준으로 좌표를 만들고, OSMnx 보행 네트워크 거리와 시간표 기반 이동 가능성을 계산했다.", "개인 이동 순서는 내부용으로만 보관하고, 장소쌍/수업쌍 집계와 지도만 공유"],
            ["외부 확산(Viral)", f"직접 확인된 외부 언급 {fmt_int(viral_row.get('confirmed_mention_count'))}건", "네이버 블로그와 유튜브 공개 검색 결과를 수집하고, 본문 확인을 통해 행사 직접 언급만 남겼다.", "출처 실명/URL 원문은 제외하고 플랫폼/요가원 단위 집계만 공유"],
            ["Google Drive 기획자료", f"분석 기회 {fmt_int(len(drive_opportunities))}축", "`bigblue.yoga@gmail.com` 계정에서 공유받은 2026년 이후 연희 요가 축제 관련 자료만 내부 아카이브로 보존했다.", "원본은 공유하지 않고 정원, F&B, 스폰서, 기획 맥락의 파생 집계만 공유"],
            ["Notion 커뮤니케이션", f"공유 페이지 {fmt_int(len(notion_pages))}건, 테마 {fmt_int(len(notion_themes))}개", "사용자가 제공한 공유 URL 2건을 읽고 기획 의도와 운영 메시지를 요약했다.", "원문 JSON과 블록 원문은 내부 보관하고, 공개본에는 페이지/테마 요약만 공유"],
            ["오붓 정산 기준", f"완료 기준 1회권 {fmt_int(settlement_one_time)}건, 패스 {fmt_int(settlement_pass)}건", "유동환 대표가 전달한 카카오톡 설명과 오붓 화면 스크린샷을 기준으로 1회권 5% 수수료, 패스 월간 이용완료 건수별 정산률을 추정 계산했다.", "최종 회계자료가 아니라 추정치로만 표시"],
        ],
    ))
    lines.append("")
    lines.append("## 6. 품질 검수와 마스킹 결과")
    lines.append("")
    lines.append(md_table(
        ["항목", "결과", "의미"],
        [
            ["Gemini Vision 리뷰 검수", f"{fmt_int(len(ai_private))}건", "오붓 리뷰 96건 전부 이미지와 OCR 텍스트를 기준으로 구조화 검수했다."],
            ["AI 검수 대체 규칙 사용", f"{fmt_int(ai_fallback_count)}건", "최종 공개 분석에 규칙 기반 대체 검수만 남은 리뷰는 없다."],
            ["검수 필요 리뷰", f"{fmt_int(ai_needs_review)}건", "추가 확인 표시가 남은 리뷰가 0건이므로 1차 공개 분석에는 전건을 사용했다."],
            ["Gemini 모델 사용 내역", ", ".join(f"{model} {count}건" for model, count in ai_model_counts.items()), "중간 쿼터 이슈로 모델이 나뉘었지만, 두 결과 모두 같은 Pydantic 스키마로 검증했다."],
            ["예약/취소 마스킹", "실명/전화번호 제거", "공개용 예약/취소 표에는 개인 식별자가 남지 않도록 처리했다."],
            ["리뷰 작성자 마스킹", "`reviewer_####`", "내부 매칭표는 내부용으로만 보관하고 외부에는 비식별 ID만 사용한다."],
        ],
    ))
    lines.append("")
    lines.append("모델 사용 내역을 숨기지 않는 이유는 투명성 때문이다. 다만 모델이 다르더라도 결과는 같은 스키마로 검증했고, 최종 분석 표에는 전건 Gemini Vision 구조화 검수가 완료된 상태만 반영했다.")
    lines.append("")
    lines.append("## 7. 전체 규모 요약")
    lines.append("")
    lines.append(md_table(
        ["항목", "건수/행수"],
        [
            ["ON STUDIO 수업", fmt_int(len(classes))],
            ["ON STUDIO 예약", fmt_int(len(reservations))],
            ["ON STUDIO 취소", fmt_int(len(cancellations))],
            ["오붓 리뷰", fmt_int(len(reviews))],
            ["수업별 Hype 지표", fmt_int(len(class_hype))],
            ["요가원별 Hype 지표", fmt_int(len(studio_hype))],
            ["수업별 정원+Hype 지표", fmt_int(len(class_capacity))],
            ["GIS 장소 노드", fmt_int(len(location_nodes))],
            ["GIS 거리 matrix", fmt_int(len(distance))],
            ["GIS 수업 시간표", fmt_int(len(schedule))],
            ["GIS 같은 날 이동 가능성", fmt_int(len(transitions))],
            ["직접 확인된 외부 언급", fmt_int(viral_row.get("confirmed_mention_count"))],
            ["F&B 협업 브랜드 후보", fmt_int(len(fnb))],
            ["스폰서 asset inventory", fmt_int(len(sponsor_assets))],
            ["오붓 정산 추정 총액", fmt_money(settlement_total)],
        ],
    ))
    lines.append("")
    lines.append("## 8. Hype 지수: 순위가 아니라 반응 프로필")
    lines.append("")
    lines.append("Hype는 하나의 총점으로 요가원을 줄 세우기 위한 지표가 아니다. 예약 Hype, 리뷰 Hype, 만족 Hype, 재방문 Hype, 결제 Hype, 운영 안정성을 나누어 본다. 이렇게 해야 대형 수업의 규모감, 작은 수업의 깊이, 리뷰 밀도, 채움률, 취소 리스크가 서로 섞이지 않는다.")
    lines.append("")
    lines.append("### 예약 규모 신호")
    lines.append("")
    lines.append(md_table(
        ["요가원/장소", "예약", "리뷰", "평균 별점", "예약 Hype"],
        [
            [r.studio_key, fmt_int(r.reservation_count), fmt_int(r.review_count), fmt_score(r.avg_overall_rating), fmt_score(r.reservation_hype)]
            for r in reservation_top.itertuples()
        ],
    ))
    lines.append("")
    lines.append("예약 규모에서는 연남장, 마이트리, 마인드플로우, 시이작, 빅블루요가가 큰 축을 형성했다. 이 수치는 공간 수용력, 프로그램 수, 노출량, 시간표 배치가 함께 만든 결과이므로 단순한 브랜드 순위로 읽으면 안 된다.")
    lines.append("")
    lines.append("### 리뷰 밀도 신호")
    lines.append("")
    lines.append(md_table(
        ["요가원/장소", "예약", "리뷰", "리뷰율", "리뷰 Hype"],
        [
            [r.studio_key, fmt_int(r.reservation_count), fmt_int(r.review_count), fmt_pct(r.review_rate_per_reservation), fmt_score(r.review_hype)]
            for r in review_density_top.itertuples()
        ],
    ))
    lines.append("")
    lines.append("리뷰 밀도에서는 연희정음과 빅블루요가가 강하게 보인다. 특히 빅블루요가는 예약 규모 대비 리뷰 반응이 높아, 수업 경험이 참가자의 언어로 남을 가능성이 컸던 축으로 해석할 수 있다.")
    lines.append("")
    lines.append("### 만족 신호")
    lines.append("")
    lines.append(md_table(
        ["요가원/장소", "예약", "리뷰", "평균 별점", "만족 Hype"],
        [
            [r.studio_key, fmt_int(r.reservation_count), fmt_int(r.review_count), fmt_score(r.avg_overall_rating), fmt_score(r.satisfaction_hype)]
            for r in satisfaction_top.itertuples()
        ],
    ))
    lines.append("")
    lines.append("만족 신호는 소규모 표본일수록 과대 해석을 피해야 한다. 다만 리뷰 수가 일정하게 확보된 마인드플로우, 시이작, 마이트리, 빅블루요가의 높은 만족 신호는 차기 수업 반복 후보를 판단할 때 유효한 근거가 된다.")
    lines.append("")
    lines.append("## 9. 리뷰 분석: 참가자는 무엇을 기억했나")
    lines.append("")
    lines.append(md_table(
        ["항목", "값"],
        [
            ["전체 평균 별점", fmt_score(overall_review_avg)],
            ["수업 평균 별점", fmt_score(class_review_avg)],
            ["분위기 평균 별점", fmt_score(atmosphere_review_avg)],
            ["시설 평균 별점", fmt_score(facility_review_avg)],
            ["평균 방문 회차", fmt_score(avg_visit_count)],
        ],
    ))
    lines.append("")
    lines.append(md_table(
        ["AI 태그", "리뷰 건수"],
        [[label, fmt_int(count)] for label, count in review_tag_counts.items()],
    ))
    lines.append("")
    lines.append("리뷰 본문에서는 분위기, 공간, 강사, 회복감, 재참여 의향이 반복적으로 잡혔다. 즉 참가자는 단순히 운동량이나 난이도만 평가한 것이 아니라, 수업이 열린 공간, 선생님의 안내, 몸의 회복감, 축제 분위기를 함께 기억했다.")
    lines.append("")
    lines.append("리뷰가 많이 작성된 수업은 다음과 같다.")
    lines.append("")
    lines.append(md_table(
        ["요가원/장소", "수업", "리뷰"],
        [[r.studio_key, r.class_title_base, fmt_int(r.review_count)] for r in review_class_top.itertuples()],
    ))
    lines.append("")
    lines.append("## 10. 정원과 채움률: 무엇을 반복하거나 확장할 수 있나")
    lines.append("")
    lines.append("정원 분석은 Google Drive 기획표보다 ON STUDIO 캘린더 복사 자료를 우선했다. 이유는 Google Drive 자료가 기획 중간 산출물일 수 있는 반면, ON STUDIO 캘린더는 실제 운영 화면의 예약수/정원 상태를 반영하기 때문이다.")
    lines.append("")
    lines.append(md_table(
        ["구분", "수업 수"],
        [
            ["확장 또는 반복 후보", fmt_int(cap_segments.get("expand_or_repeat_candidate", 0))],
            ["소규모 정원 또는 틈새 강점 후보", fmt_int(cap_segments.get("small_capacity_or_niche_strength", 0))],
            ["안정적 중간층", fmt_int(cap_segments.get("steady_middle", 0))],
            ["수요 개발 후보", fmt_int(cap_segments.get("demand_development_candidate", 0))],
            ["메시지/시간표 재검토 후보", fmt_int(cap_segments.get("message_or_schedule_review", 0))],
        ],
    ))
    lines.append("")
    lines.append("요가원/장소별 채움률 상위 신호는 다음과 같다.")
    lines.append("")
    lines.append(md_table(
        ["요가원/장소", "예약", "리뷰", "가중 채움률", "만석 세션", "세션 수", "확장 후보"],
        [
            [
                r.studio_key,
                fmt_int(r.reservation_count),
                fmt_int(r.review_count),
                fmt_pct(r.weighted_fill_rate),
                fmt_int(r.sold_out_session_count),
                fmt_int(r.capacity_session_count),
                fmt_int(r.expand_or_repeat_candidate_count),
            ]
            for r in capacity_top.itertuples()
        ],
    ))
    lines.append("")
    lines.append("채움률은 차기 회차에서 바로 운영 의사결정으로 연결된다. 만석이 반복된 수업은 정원 확대, 회차 추가, 더 큰 공간 배치, 보조 강사 투입을 검토할 수 있다. 반대로 좋은 리뷰가 있는데 예약이 낮은 수업은 제목, 설명, 시간대, 위치 안내를 다시 다듬는 쪽이 적합하다.")
    lines.append("")
    lines.append("## 11. GIS 분석: 걸어서 이어지는 축제인가")
    lines.append("")
    lines.append("GIS 분석은 참가자의 실제 GPS를 추적한 것이 아니다. 예약 시간표와 장소 위치를 기준으로, 같은 참여자가 같은 날 여러 수업을 예약했을 때 시간표상 이동이 가능한지를 본 분석이다.")
    lines.append("")
    lines.append(md_table(
        ["항목", "값"],
        [
            ["행사 장소 노드", fmt_int(len(location_nodes))],
            ["장소 간 거리 matrix", fmt_int(len(distance))],
            ["평균 장소 간 도보시간", f"{fmt_score(avg_walk_minutes)}분"],
            ["가장 먼 장소쌍", max_walk_desc],
            ["same-day 수업 이동 후보", fmt_int(len(transitions))],
            ["여유 있음", fmt_int(comfortable_count)],
            ["빠듯함", fmt_int(tight_count)],
            ["시간표상 어려움", fmt_int(difficult_count)],
            ["시간 겹침/간격 없음", fmt_int(no_gap_count)],
        ],
    ))
    lines.append("")
    lines.append("대부분의 이동 후보는 시간표상 가능했지만, 일부는 빠듯하거나 어려운 것으로 나타났다. 차기 회차에서는 같은 권역의 수업은 30분 간격으로 묶고, 먼 장소로 이어지는 수업은 45분에서 60분 이상 여유를 두는 편이 안전하다. 연남장 같은 허브 공간은 대형 프로그램, 대기, F&B, 굿즈 배포, 파트너 콘텐츠 노출의 거점으로 설계할 수 있다.")
    lines.append("")
    lines.append("지도는 GitHub 파일 화면이 아니라 GitHub Pages 링크로 열어야 실제 지도로 볼 수 있다.")
    lines.append("")
    lines.append(md_table(
        ["지도", "용도", "바로 보기"],
        [
            ["GIS 기본 지도", "행사 장소와 Hype 신호를 지도 위에서 확인", "[열기](https://mow-coding.github.io/YH-yogaweek/years/2026/reports/analysis/yeonhui_yoga_week_gis_map.html)"],
            ["시간 흐름 지도", "시간 슬라이더로 수업이 언제 어디서 열렸는지 확인", "[열기](https://mow-coding.github.io/YH-yogaweek/years/2026/reports/analysis/yeonhui_yoga_week_time_slider_map.html)"],
            ["동선 가능성 지도", "같은 날 수업 간 이동 가능성 확인", "[열기](https://mow-coding.github.io/YH-yogaweek/years/2026/reports/analysis/yeonhui_yoga_week_transition_map.html)"],
            ["시간-공간 큐브", "장소와 시간을 3D로 겹쳐 보는 고급/보조 시각화", "[열기](https://mow-coding.github.io/YH-yogaweek/years/2026/reports/analysis/yeonhui_yoga_week_space_time_cube.html)"],
        ],
    ))
    lines.append("")
    lines.append("장소쌍 이동 집계 상위는 다음과 같다.")
    lines.append("")
    top_location_transitions = top_rows(
        location_transitions,
        "transition_count",
        [
            "origin_display_name",
            "destination_display_name",
            "feasibility_label",
            "transition_count",
            "avg_gap_minutes",
            "avg_walk_minutes",
        ],
        8,
    )
    lines.append(md_table(
        ["출발", "도착", "판정", "이동 후보", "평균 여유", "평균 도보"],
        [
            [
                r.origin_display_name,
                r.destination_display_name,
                r.feasibility_label,
                fmt_int(r.transition_count),
                f"{fmt_score(r.avg_gap_minutes)}분",
                f"{fmt_score(r.avg_walk_minutes)}분",
            ]
            for r in top_location_transitions.itertuples()
        ],
    ))
    lines.append("")
    lines.append("## 12. Viral 분석: 외부 웹에서는 어떻게 보였나")
    lines.append("")
    lines.append("외부 확산 지표는 Hype에 합산하지 않았다. Hype가 행사 내부의 예약, 리뷰, 만족, 결제 반응이라면, 외부 확산은 네이버 블로그와 유튜브 같은 공개 웹에서 축제가 어떻게 언급되었는지를 보는 별도 축이다.")
    lines.append("")
    lines.append(md_table(
        ["항목", "값"],
        [
            ["직접 확인된 외부 언급", fmt_int(viral_row.get("confirmed_mention_count"))],
            ["플랫폼 수", fmt_int(viral_row.get("platform_count"))],
            ["네이버 블로그 언급", fmt_int(viral_row.get("naver_blog_mention_count"))],
            ["유튜브 영상", fmt_int(viral_row.get("youtube_video_count"))],
            ["유튜브 조회수", fmt_int(viral_row.get("youtube_view_count"))],
            ["기간", f"{viral_row.get('first_published_date', '-')} ~ {viral_row.get('last_published_date', '-')}"],
        ],
    ))
    lines.append("")
    lines.append(md_table(
        ["요가원/장소", "직접 확인 언급", "외부 확산 신호", "첫 게시일", "마지막 게시일"],
        [
            [
                r.matched_studio_term,
                fmt_int(r.confirmed_mention_count),
                fmt_score(r.viral_signal_score),
                r.first_published_date,
                r.last_published_date,
            ]
            for r in viral_top.itertuples()
        ],
    ))
    lines.append("")
    lines.append("외부 확산은 네이버 블로그 중심으로 발생했고, 연희정음, 마인드플로우, 시이작, 숨명상센터, 연남장, 빅블루요가 등이 반복적으로 언급되었다. 차기에는 공식 해시태그, 자발 리뷰 제출 이벤트, 플랫폼별 리뷰 수집 동의 절차를 미리 설계하면 훨씬 더 신뢰도 높은 외부 확산 분석이 가능하다.")
    lines.append("")
    lines.append("## 13. F&B와 스폰서십: 물품 제공을 넘어 동선 설계로")
    lines.append("")
    lines.append(md_table(
        ["항목", "값"],
        [
            ["F&B 협업 브랜드 후보", fmt_int(len(fnb))],
            ["스폰서 asset inventory", fmt_int(len(sponsor_assets))],
            ["Google Drive 분석 기회 축", fmt_int(len(drive_opportunities))],
        ],
    ))
    lines.append("")
    lines.append("F&B와 스폰서십은 단순히 과자나 음료를 제공했다는 사실보다, 참가자가 수업 전후로 어디를 걷고 어떤 브랜드를 만났는지와 연결될 때 가치가 커진다. 다음 회차에서는 쿠폰 코드, QR 인증, 수업 테마별 브랜드 매칭, F&B 루트 안내를 미리 설계해 스폰서에게 측정 가능한 결과를 제공하는 것이 좋다.")
    lines.append("")
    lines.append("Google Drive 자료에서 확인된 추가 분석 기회는 다음과 같다.")
    lines.append("")
    lines.append(md_table(
        ["분석 축", "자료 영역", "핵심 질문", "공유 수준"],
        [
            [r.analysis_axis, r.source_area, r.question, r.privacy_level]
            for r in drive_opportunities.itertuples()
        ],
    ))
    lines.append("")
    lines.append("## 14. 오붓 정산 추정치: 회계 확정값이 아니라 의사결정용 참고값")
    lines.append("")
    lines.append("정산 분석은 유동환 대표가 전달한 기준을 반영했다. 1회권은 이용일 기준 영업일 3일 후 5% 수수료를 제외하고 정산되는 것으로 기록했다. 패스권은 구매한 패키지 종류가 아니라 소비자별 월간 이용완료 건수 구간에 따라 1~9회 75%, 10~99회 65%, 100회 이상 55% 정산률을 적용하는 것으로 해석했다.")
    lines.append("")
    lines.append("다만 현재 프로젝트는 해당 소비자의 오붓 플랫폼 전체 월간 이용내역을 갖고 있지 않고, 연희 요가 위크 ON STUDIO 관측치만 갖고 있다. 따라서 패스권 정산액은 최종 회계값이 아니라 추정치이며, 오붓 최종 정산서와 대조해야 한다.")
    lines.append("")
    lines.append(md_table(
        ["항목", "값"],
        [
            ["완료 기준 1회권", fmt_int(settlement_one_time)],
            ["완료 기준 패스권", fmt_int(settlement_pass)],
            ["정산 추정 총액", fmt_money(settlement_total)],
        ],
    ))
    lines.append("")
    lines.append(md_table(
        ["월", "요가원/장소", "1회권 완료", "패스 완료", "패스 가중 정산률", "정산 추정액"],
        [
            [
                r.service_month,
                r.studio_key,
                fmt_int(r.one_time_completed_count),
                fmt_int(r.pass_completed_count),
                fmt_pct(r.pass_settlement_rate_weighted_avg),
                fmt_money(r.estimated_total_settlement_krw),
            ]
            for r in settlement_top.itertuples()
        ],
    ))
    lines.append("")
    lines.append("## 15. 이해관계자별 제안")
    lines.append("")
    lines.append(md_table(
        ["대상", "바로 쓸 수 있는 제안"],
        [
            ["2026 참여 요가원", "각 요가원별 수업 카드 형태로 예약, 취소, 리뷰, 채움률, 반복 후보를 돌려준다. 숫자는 순위가 아니라 운영 개선 근거로 설명한다."],
            ["어반플레이/오붓 등 공식 파트너", "예약, 리뷰, GIS, 외부 확산을 연결한 파트너용 대시보드나 CSV 내보내기 구조를 제안한다. 플랫폼이 가진 원자료와 본 프로젝트의 현장 맥락을 결합하면 더 강한 분석이 가능하다."],
            ["2026 스폰서", "올해는 물품/콘텐츠 제공 중심이었다면, 다음에는 쿠폰 코드, QR, 후기 제출, F&B 루트로 측정 가능한 스폰서십 패키지를 설계한다."],
            ["2026 참가자", "개인정보를 보호한 상태에서 참가자 리뷰가 다음 시간표, 정원, 동선 개선에 반영되었다는 회고 콘텐츠를 공개한다."],
            ["차기 참여 희망 요가원", "대형 수업만 모집하지 말고 입문, 심화, 회복, 음악/명상, 공간형 경험처럼 역할을 나누어 참여 제안을 만든다."],
            ["차기 공식 파트너 후보", "예약/리뷰/공간/콘텐츠 확산을 함께 측정할 수 있는 파트너십 구조를 제시한다."],
            ["차기 공식 스폰서 후보", "수업 테마와 브랜드 메시지가 맞는 스폰서십 메뉴를 만들고, 노출보다 참가자 접점과 기억을 측정하는 방식으로 제안한다."],
            ["차기 일반 참가자", "수업 추천뿐 아니라 걷는 동선, F&B, 굿즈, 휴식 포인트까지 포함한 하루 루트 안내를 제공한다."],
            ["공공기관", "민간 주도 지역 건강문화 축제로서 생활권 문화, 지역상권, 로컬 협업, 웰니스 접근성 관점의 시범사업 자료로 제안한다."],
        ],
    ))
    lines.append("")
    lines.append("## 16. 한계와 다음 수집 과제")
    lines.append("")
    lines.append("- 예약/취소 데이터는 ON STUDIO 화면 수동 수집 기반이다. 최종 정산이나 플랫폼 원장과 차이가 있을 수 있다.")
    lines.append("- 리뷰는 오붓 화면 스크린샷 기반 OCR이다. Gemini Vision 검수로 1차 품질을 높였지만, 원문 플랫폼 export가 제공되면 더 안전하다.")
    lines.append("- 정산 추정치는 최종 회계값이 아니다. 오붓의 최종 정산서와 소비자별 월간 전체 이용완료 건수 확인이 필요하다.")
    lines.append("- GIS는 실제 GPS 이동 기록이 아니라 예약 시간표상 이동 가능성 분석이다.")
    lines.append("- Viral은 공개 웹 검색 기반이다. 인스타그램 비공개 계정, 스토리, DM, 카카오톡 공유처럼 닫힌 확산은 포함하지 않는다.")
    lines.append("- Google Drive와 Notion 원문에는 운영상 민감한 내용이 있을 수 있어 공개 보고서에는 요약과 집계만 쓴다.")
    lines.append("")
    lines.append("차기 회차에는 사전 동의 기반 후기 수집, 공식 해시태그, 수업별 정원 확정표, 스폰서 쿠폰 코드, 참가자 사후 설문, 플랫폼별 export 기능을 미리 설계하는 것이 좋다.")
    lines.append("")
    lines.append("## 17. 재현 가능한 산출물 위치")
    lines.append("")
    lines.append(md_table(
        ["목적", "파일"],
        [
            ["방법론과 데이터 계보", "`years/2026/reports/analysis/methodology_and_data_lineage.md`"],
            ["전체 현황판", "`years/2026/docs/project-current-status.md`"],
            ["작업 일지", "`years/2026/docs/work-log.md`"],
            ["전체 재분석 로그", "`years/2026/docs/full-reanalysis-work-log.md`"],
            ["수업별 Hype", "`years/2026/data/processed/analysis/public/class_hype_metrics.csv`"],
            ["요가원별 Hype", "`years/2026/data/processed/analysis/public/studio_hype_metrics.csv`"],
            ["정원+Hype", "`years/2026/data/processed/analysis/public/class_capacity_hype_metrics.csv`"],
            ["GIS 심화 리포트", "`years/2026/reports/analysis/gis_deep_analysis_report.md`"],
            ["외부 확산 분석 리포트", "`years/2026/reports/external_web/yeonhui_yoga_week_viral_analysis_report.md`"],
            ["오붓 정산 추정", "`years/2026/reports/analysis/obud_settlement_analysis_report.md`"],
            ["공개 전 감사", "`years/2026/docs/public-github-release-audit.md`"],
        ],
    ))
    lines.append("")
    lines.append("## 18. 최종 판단")
    lines.append("")
    lines.append("현재 확보한 데이터만으로도 2026 연희 요가 위크의 1차 분석은 제출 가능한 수준으로 정리되었다. 핵심은 특정 요가원을 한 줄 순위로 세우는 것이 아니라, 예약 규모, 리뷰 밀도, 만족도, 정원 포화, 동선 가능성, 외부 확산, 스폰서 접점을 서로 다른 신호로 분리해 읽는 것이다. 이 구조를 유지하면 다음 회차부터는 훨씬 더 적은 시행착오로 수집, 분석, 보고, 제안까지 이어갈 수 있다.")
    lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
