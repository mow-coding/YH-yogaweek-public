from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "data" / "processed" / "analysis" / "public"
REPORT_DIR = ROOT / "reports" / "google_drive"
MANIFEST = REPORT_DIR / "rightnow_yogi_full_archive_manifest.csv"
AREA_SUMMARY = PUBLIC_DIR / "google_drive_archive_area_summary.csv"
ASSET_TYPE_SUMMARY = PUBLIC_DIR / "google_drive_archive_asset_type_summary.csv"
OPPORTUNITY_MATRIX = PUBLIC_DIR / "google_drive_archive_analysis_opportunity_matrix.csv"
REPORT = REPORT_DIR / "google_drive_archive_analysis_report.md"

LOCAL_COPY_STATUSES = {"downloaded", "downloaded_export_fallback", "existing_local_copy"}


def path_part(source_path: str, index: int, fallback: str = "") -> str:
    parts = [part for part in str(source_path).split("/") if part]
    if len(parts) > index:
        return parts[index]
    return fallback


def classify_area(source_path: str) -> str:
    second = path_part(source_path, 1, "unknown")
    if second.startswith("1프로그램"):
        return "program"
    if second.startswith("2디자인"):
        return "design"
    if second.startswith("3스폰서"):
        return "sponsor"
    if second.startswith("4F&B"):
        return "fnb"
    if "리커버리" in source_path:
        return "recovery"
    if "크루" in source_path or "응답" in source_path:
        return "operations_response"
    return "other"


def classify_asset_type(row: pd.Series) -> str:
    mime = str(row.get("source_mime_type", ""))
    local_path = str(row.get("local_path", ""))
    suffix = Path(local_path).suffix.lower()
    if "folder" in mime:
        return "folder"
    if "spreadsheet" in mime or suffix in {".xlsx", ".csv"}:
        return "spreadsheet"
    if "document" in mime or suffix in {".docx", ".txt", ".pdf"}:
        return "document"
    if "presentation" in mime or suffix == ".pptx":
        return "presentation"
    if mime.startswith("image/") or suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return "image"
    if suffix in {".ai", ".psd", ".svg"}:
        return "design_source"
    if suffix in {".zip"}:
        return "archive"
    if mime.startswith("video/") or suffix in {".mp4", ".mov"}:
        return "video"
    return "other"


def normalize_label(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    return cleaned or "unknown"


def build_opportunity_matrix(area_summary: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "analysis_axis": "program_design",
            "source_area": "program",
            "question": "어떤 수업/외부연사/공간 구성이 행사 반응을 만들었는가?",
            "evidence_available": "프로그램표, 수업 설명, 강사/공간 소개, 사진 자료",
            "method": "문서 인벤토리, 수업 카테고리 태깅, Hype/Capacity/GIS 결합",
            "public_output_candidate": "수업 유형별 반응표, 내년 프로그램 확장 후보",
            "privacy_level": "public derivative only",
            "current_record_count": int(area_summary.loc[area_summary["area_key"] == "program", "local_copy_count"].sum()),
        },
        {
            "analysis_axis": "sponsor_network",
            "source_area": "sponsor",
            "question": "어떤 스폰서가 어떤 형태의 지원/노출/콘텐츠로 연결되었는가?",
            "evidence_available": "스폰서 폴더, 로고/카드뉴스/브랜드 이미지",
            "method": "스폰서 asset inventory, 후원 유형 분류, 노출자료 집계",
            "public_output_candidate": "스폰서십 구조 요약, 후원사별 활용 가능 asset 현황",
            "privacy_level": "internal review before sharing",
            "current_record_count": int(area_summary.loc[area_summary["area_key"] == "sponsor", "local_copy_count"].sum()),
        },
        {
            "analysis_axis": "local_consumption_route",
            "source_area": "fnb",
            "question": "요가원 방문 동선이 주변 F&B 협업과 어떻게 이어질 수 있는가?",
            "evidence_available": "F&B 브랜드 목록, 쿠폰/브랜드 자료, GIS 장소 노드",
            "method": "F&B inventory, 주소/좌표 보강, 요가원-상점 거리/동선 분석",
            "public_output_candidate": "지역 소비 동선 지도, 협업 브랜드 후보군",
            "privacy_level": "public derivative after address verification",
            "current_record_count": int(area_summary.loc[area_summary["area_key"] == "fnb", "local_copy_count"].sum()),
        },
        {
            "analysis_axis": "promotion_asset_archive",
            "source_area": "design",
            "question": "어떤 홍보물/디자인 asset이 다음 회차에 재사용 가능한가?",
            "evidence_available": "포스터, 디자인 원본, 카드뉴스, 이미지 자료",
            "method": "asset type summary, 재사용 가능 asset 구분, public/private 구분",
            "public_output_candidate": "홍보물 아카이브 목록과 다음 회차 제작 체크리스트",
            "privacy_level": "internal raw, public summary only",
            "current_record_count": int(area_summary.loc[area_summary["area_key"] == "design", "local_copy_count"].sum()),
        },
        {
            "analysis_axis": "operations_and_recovery",
            "source_area": "operations_response",
            "question": "크루/리커버리 운영 참여 데이터에서 다음 운영 개선점은 무엇인가?",
            "evidence_available": "응답 시트, 리커버리 트랙 자료",
            "method": "private-only 응답 집계, 개인정보 제거 후 운영 지표화",
            "public_output_candidate": "운영 개선 요약. 원문/개인응답 외부 공유 금지",
            "privacy_level": "private only unless fully aggregated",
            "current_record_count": int(
                area_summary.loc[area_summary["area_key"].isin(["operations_response", "recovery"]), "local_copy_count"].sum()
            ),
        },
    ]
    return pd.DataFrame(rows)


def main() -> int:
    if not MANIFEST.exists():
        raise SystemExit(f"Missing manifest: {MANIFEST}")
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(MANIFEST)
    df["area_key"] = df["source_path"].map(classify_area)
    df["top_folder"] = df["source_path"].map(lambda value: normalize_label(path_part(value, 1, "unknown")))
    df["sub_folder"] = df["source_path"].map(lambda value: normalize_label(path_part(value, 2, "")))
    df["asset_type"] = df.apply(classify_asset_type, axis=1)
    df["has_local_copy"] = df["status"].isin(LOCAL_COPY_STATUSES)

    area_summary = (
        df.groupby(["area_key", "top_folder"], dropna=False)
        .agg(
            total_manifest_rows=("source_id", "count"),
            local_copy_count=("has_local_copy", "sum"),
            folder_count=("status", lambda s: int((s == "folder").sum())),
            skipped_pre_2026_count=("status", lambda s: int((s == "skipped_pre_2026").sum())),
            error_count=("status", lambda s: int((s == "error").sum())),
            private_or_sensitive_count=("sensitivity", lambda s: int((s == "private_or_sensitive_raw").sum())),
            public_derivative_candidate_count=("sensitivity", lambda s: int((s == "public_derivative_candidate").sum())),
        )
        .reset_index()
        .sort_values(["local_copy_count", "total_manifest_rows"], ascending=False)
    )
    area_summary.to_csv(AREA_SUMMARY, index=False, encoding="utf-8-sig")

    asset_type_summary = (
        df.groupby(["area_key", "asset_type"], dropna=False)
        .agg(
            total_manifest_rows=("source_id", "count"),
            local_copy_count=("has_local_copy", "sum"),
            private_or_sensitive_count=("sensitivity", lambda s: int((s == "private_or_sensitive_raw").sum())),
        )
        .reset_index()
        .sort_values(["area_key", "local_copy_count"], ascending=[True, False])
    )
    asset_type_summary.to_csv(ASSET_TYPE_SUMMARY, index=False, encoding="utf-8-sig")

    opportunity_matrix = build_opportunity_matrix(area_summary)
    opportunity_matrix.to_csv(OPPORTUNITY_MATRIX, index=False, encoding="utf-8-sig")

    lines = [
        "# Google Drive Archive Analysis Report",
        "",
        f"작성일: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## 요약",
        "",
        f"- manifest 전체 행: {len(df)}",
        f"- 로컬 보존 원본 사본: {int(df['has_local_copy'].sum())}",
        f"- 2026 이전 제외: {int((df['status'] == 'skipped_pre_2026').sum())}",
        f"- 실패: {int((df['status'] == 'error').sum())}",
        "",
        "## 분석 축별 원본 사본 수",
        "",
    ]
    for row in area_summary.itertuples(index=False):
        lines.append(
            f"- {row.area_key} / {row.top_folder}: 원본 사본 {int(row.local_copy_count)}개, "
            f"private/sensitive 후보 {int(row.private_or_sensitive_count)}개"
        )
    lines.extend(["", "## 다음 분석 기회", ""])
    for row in opportunity_matrix.itertuples(index=False):
        lines.append(f"- {row.analysis_axis}: {row.question}")
        lines.append(f"  - 방법: {row.method}")
        lines.append(f"  - 공유 범위: {row.privacy_level}")
    lines.extend(
        [
            "",
            "## 산출물",
            "",
            f"- `{AREA_SUMMARY.relative_to(ROOT)}`",
            f"- `{ASSET_TYPE_SUMMARY.relative_to(ROOT)}`",
            f"- `{OPPORTUNITY_MATRIX.relative_to(ROOT)}`",
            "",
            "## 한계",
            "",
            "- 이 단계는 Drive 원문 내용을 전부 읽어 의미 분석한 것이 아니라, manifest와 폴더 구조를 기준으로 분석 기회를 정리한 것이다.",
            "- 스폰서/F&B 자료는 public 공유 전 브랜드명, 계약 조건, 쿠폰 조건, 이미지 권리 검토가 필요하다.",
            "- 크루/응답 시트는 개인정보 가능성이 있어 private-only 원칙을 적용한다.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Area summary rows: {len(area_summary)}")
    print(f"Asset type summary rows: {len(asset_type_summary)}")
    print(f"Opportunity rows: {len(opportunity_matrix)}")
    print(f"Report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
