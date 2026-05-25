from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd


YEAR_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PUBLIC_ROOT = PROJECT_ROOT.parent / "YH-yogaweek"
REPORT_DIR = YEAR_ROOT / "reports" / "public_release"
REPORT_MD = REPORT_DIR / "release_quality_gate_report.md"
REPORT_JSON = REPORT_DIR / "release_quality_gate_report.json"

PUBLIC_ANALYSIS = YEAR_ROOT / "data" / "processed" / "analysis" / "public"
ONSTUDIO_PUBLIC = YEAR_ROOT / "data" / "processed" / "onstudio" / "public"
OBUD_PUBLIC = YEAR_ROOT / "data" / "processed" / "obud_reviews" / "public"
OBUD_PRIVATE = YEAR_ROOT / "data" / "processed" / "obud_reviews" / "private"

FORBIDDEN_PUBLIC_PATTERNS = {
    "forbidden_account_private_work_email": re.compile("si" + "cp" + "se" + "oul", re.IGNORECASE),
    "forbidden_account_private_work_handle": re.compile("ye" + "s" + r"[-_ ]?u[-_ ]?can|" + "si" + "cp", re.IGNORECASE),
    "korean_phone_number": re.compile(r"010[-\s]?\d{4}[-\s]?\d{4}"),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_\-]{10,}"),
}

BAD_STUDIO_KEYS = {"대저택 프라이빗", "숨 명상센터", "비전스트롤"}
GENERIC_CLASS_BODY_KEYS = {"요가", "명상", "수업", "필라테스"}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def check(condition: bool, message: str, blockers: list[str], passes: list[str]) -> None:
    if condition:
        passes.append(message)
    else:
        blockers.append(message)


def count_rows(path: Path, expected: int, blockers: list[str], passes: list[str]) -> pd.DataFrame:
    frame = read_csv(path)
    check(len(frame) == expected, f"{path.relative_to(YEAR_ROOT)} rows == {expected} (actual {len(frame)})", blockers, passes)
    return frame


def assert_no_bad_keys(frame: pd.DataFrame, column: str, label: str, blockers: list[str], passes: list[str]) -> None:
    if column not in frame.columns:
        blockers.append(f"{label}: missing column {column}")
        return
    bad = sorted(set(frame[column]) & BAD_STUDIO_KEYS)
    check(not bad, f"{label}.{column} has no non-canonical keys {sorted(BAD_STUDIO_KEYS)}", blockers, passes)


def assert_unique(frame: pd.DataFrame, columns: list[str], label: str, blockers: list[str], passes: list[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        blockers.append(f"{label}: missing unique-key columns {missing}")
        return
    duplicated = int(frame.duplicated(columns).sum())
    check(duplicated == 0, f"{label} unique on {columns} (duplicates {duplicated})", blockers, passes)


def class_body_key(value: object) -> str:
    text = re.sub(r"^\[[^\]]+\]\s*", "", str(value))
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", text).lower()


def scan_public_tree(public_root: Path) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    passes: list[str] = []
    if not public_root.exists():
        blockers.append(f"public root missing: {public_root}")
        return blockers, passes

    scanned_files = 0
    for path in public_root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".pdf", ".duckdb"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        scanned_files += 1
        relative = path.relative_to(public_root)
        for name, pattern in FORBIDDEN_PUBLIC_PATTERNS.items():
            if pattern.search(text):
                blockers.append(f"public forbidden pattern {name} found in {relative}")
    if not any(item.startswith("public forbidden pattern") for item in blockers):
        passes.append(f"public text scan found no forbidden patterns across {scanned_files} files")
    return blockers, passes


def validate_markdown_tables(public_root: Path) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    passes: list[str] = []
    checked_blocks = 0
    if not public_root.exists():
        return blockers, passes

    for path in public_root.rglob("*.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        in_code = False
        block: list[tuple[int, str]] = []
        for index, line in enumerate(lines, start=1):
            if line.strip().startswith("```"):
                in_code = not in_code
            is_table_line = (not in_code) and line.strip().startswith("|") and line.strip().endswith("|")
            if is_table_line:
                block.append((index, line))
                continue
            if len(block) >= 2:
                expected = block[0][1].count("|")
                for line_number, table_line in block[1:]:
                    if table_line.count("|") != expected:
                        blockers.append(f"markdown table pipe-count mismatch: {path.relative_to(public_root)}:{line_number}")
                checked_blocks += 1
            block = []
        if len(block) >= 2:
            expected = block[0][1].count("|")
            for line_number, table_line in block[1:]:
                if table_line.count("|") != expected:
                    blockers.append(f"markdown table pipe-count mismatch: {path.relative_to(public_root)}:{line_number}")
            checked_blocks += 1

    if not blockers:
        passes.append(f"markdown table structure checked ({checked_blocks} table blocks)")
    return blockers, passes


def validate_public_html(public_root: Path) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    passes: list[str] = []
    report = public_root / "years" / "2026" / "reports" / "stakeholders" / "yeonhui_yoga_week_integrated_stakeholder_report.html"
    if not report.exists():
        blockers.append(f"public report HTML missing: {report}")
        return blockers, passes
    text = report.read_text(encoding="utf-8")
    h1_count = len(re.findall(r"<h1\b", text, flags=re.IGNORECASE))
    check(h1_count == 1, f"public integrated report has exactly one H1 (actual {h1_count})", blockers, passes)
    return blockers, passes


def github_contributor_check(skip: bool) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    passes: list[str] = []
    if skip:
        passes.append("GitHub contributor check skipped by flag")
        return blockers, passes
    url = "https://api.github.com/repos/mow-coding/YH-yogaweek/contributors"
    request = Request(url, headers={"User-Agent": "codex-public-release-validator"})
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError) as exc:
        blockers.append(f"GitHub contributor API check failed: {type(exc).__name__}")
        return blockers, passes
    contributors = sorted(item.get("login", "") for item in payload if item.get("login"))
    check(contributors == ["mow-coding"], f"GitHub contributors == ['mow-coding'] (actual {contributors})", blockers, passes)
    return blockers, passes


def build_report(results: dict[str, Any]) -> str:
    status = "PASS" if results["passed"] else "FAIL"
    blocker_lines = "\n".join(f"- {item}" for item in results["blockers"]) or "- 없음"
    pass_lines = "\n".join(f"- {item}" for item in results["passes"]) or "- 없음"
    warning_lines = "\n".join(f"- {item}" for item in results["warnings"]) or "- 없음"
    return f"""# Public Release Quality Gate Report

- status: {status}
- generated_at: {results["generated_at"]}
- public_root: `{results["public_root"]}`

## Blockers
{blocker_lines}

## Warnings
{warning_lines}

## Passed Checks
{pass_lines}

## Notes
- 이 품질 게이트는 공개 레포에 올리기 전 표준화, 중복, 리뷰 매칭, 정원 매칭, 민감 문자열, HTML/Markdown 표시 품질을 확인한다.
- 이번 감사에서는 기존 계획상 예상했던 84개 수업 행 외에 OCR 별칭 문제까지 추가로 정정되어 최종 `class_hype_metrics`와 `class_capacity_hype_metrics`는 83행을 기준으로 검증한다.
- 이 검사는 보안 삭제 도구가 아니라 공개 패키지 품질 검사다. 실제 secret 노출이 발견되면 key 폐기/회전과 레포 재생성이 우선이다.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-root", type=Path, default=DEFAULT_PUBLIC_ROOT)
    parser.add_argument("--skip-github", action="store_true")
    args = parser.parse_args()

    blockers: list[str] = []
    warnings: list[str] = []
    passes: list[str] = []

    classes = count_rows(ONSTUDIO_PUBLIC / "onstudio_classes_2026_yeonhui_yoga_week.csv", 125, blockers, passes)
    reservations = count_rows(
        ONSTUDIO_PUBLIC / "onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv",
        1611,
        blockers,
        passes,
    )
    cancellations = count_rows(
        ONSTUDIO_PUBLIC / "onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv",
        1048,
        blockers,
        passes,
    )
    reviews = count_rows(OBUD_PUBLIC / "obud_reviews_deidentified.csv", 96, blockers, passes)
    extracted_reviews = count_rows(OBUD_PRIVATE / "obud_reviews_extracted_private.csv", 96, blockers, passes)
    studio_hype = count_rows(PUBLIC_ANALYSIS / "studio_hype_metrics.csv", 12, blockers, passes)
    class_hype = count_rows(PUBLIC_ANALYSIS / "class_hype_metrics.csv", 83, blockers, passes)
    studio_capacity = count_rows(PUBLIC_ANALYSIS / "studio_capacity_hype_metrics.csv", 12, blockers, passes)
    class_capacity = count_rows(PUBLIC_ANALYSIS / "class_capacity_hype_metrics.csv", 83, blockers, passes)
    settlement_class = count_rows(PUBLIC_ANALYSIS / "obud_settlement_estimate_by_class.csv", 110, blockers, passes)
    settlement_studio_month = count_rows(PUBLIC_ANALYSIS / "obud_settlement_estimate_by_studio_month.csv", 19, blockers, passes)
    location_nodes = count_rows(PUBLIC_ANALYSIS / "location_nodes.csv", 13, blockers, passes)
    location_distance = count_rows(PUBLIC_ANALYSIS / "location_distance_matrix.csv", 169, blockers, passes)
    class_location_evidence = count_rows(
        PUBLIC_ANALYSIS / "class_location_evidence_public.csv",
        83,
        blockers,
        passes,
    )

    _ = (
        classes,
        reservations,
        cancellations,
        studio_capacity,
        settlement_studio_month,
        location_nodes,
        location_distance,
        class_location_evidence,
    )

    for label, frame in [
        ("studio_hype_metrics", studio_hype),
        ("class_hype_metrics", class_hype),
        ("studio_capacity_hype_metrics", studio_capacity),
        ("class_capacity_hype_metrics", class_capacity),
        ("obud_settlement_estimate_by_class", settlement_class),
        ("obud_settlement_estimate_by_studio_month", settlement_studio_month),
    ]:
        if "studio_key" in frame.columns:
            assert_no_bad_keys(frame, "studio_key", label, blockers, passes)

    viral_studio = read_csv(PUBLIC_ANALYSIS / "yeonhui_yoga_week_viral_studio_metrics.csv")
    assert_no_bad_keys(viral_studio, "matched_studio_term", "viral_studio_metrics", blockers, passes)

    assert_unique(studio_hype, ["studio_key"], "studio_hype_metrics", blockers, passes)
    assert_unique(class_hype, ["studio_key", "class_base_key"], "class_hype_metrics", blockers, passes)
    assert_unique(class_capacity, ["studio_key", "class_base_key"], "class_capacity_hype_metrics", blockers, passes)
    assert_unique(settlement_class, ["service_month", "studio_key", "class_base_key"], "obud_settlement_estimate_by_class", blockers, passes)

    review_0044 = reviews[reviews["review_id"].eq("review_0044")]
    check(not review_0044.empty, "review_0044 exists in public review table", blockers, passes)
    if not review_0044.empty:
        row = review_0044.iloc[0]
        check(
            row.get("class_base_key") == "연희정음랜드마크빅블루의호흡회복요가",
            "review_0044 matched to [연희정음|랜드마크] 빅블루의 호흡 회복 요가",
            blockers,
            passes,
        )

    review_needs = int(reviews["needs_review"].astype(str).str.lower().eq("true").sum())
    extracted_class_needs = int(extracted_reviews["class_match_needs_review"].astype(str).str.lower().eq("true").sum())
    check(review_needs == 0, f"public review needs_review == 0 (actual {review_needs})", blockers, passes)
    check(extracted_class_needs == 0, f"private class_match_needs_review == 0 (actual {extracted_class_needs})", blockers, passes)

    suspicious_generic = []
    for row in reviews.itertuples(index=False):
        query_body = class_body_key(getattr(row, "class_title_ocr", ""))
        matched_body = class_body_key(getattr(row, "class_title_base", ""))
        match_score = pd.to_numeric(pd.Series([getattr(row, "class_match_score", "")]), errors="coerce").fillna(0).iloc[0]
        if float(match_score) >= 95:
            continue
        if len(query_body) >= 8 and (
            matched_body in GENERIC_CLASS_BODY_KEYS
            or (matched_body and len(matched_body) / max(len(query_body), 1) < 0.45)
        ):
            suspicious_generic.append(getattr(row, "review_id", "unknown"))
    check(
        not suspicious_generic,
        f"no long OCR title was under-matched to a short generic class candidate ({suspicious_generic[:5]})",
        blockers,
        passes,
    )

    capacity_needs = int(class_capacity["capacity_match_status"].eq("needs_review").sum())
    check(capacity_needs == 0, f"capacity_match_status needs_review == 0 (actual {capacity_needs})", blockers, passes)

    active_gis_text = "\n".join(
        [
            (PUBLIC_ANALYSIS / "location_nodes.csv").read_text(encoding="utf-8-sig"),
            (PUBLIC_ANALYSIS / "class_schedule_gis.csv").read_text(encoding="utf-8-sig"),
        ]
    )
    check(
        "궁둥산" not in active_gis_text and "궁동산" not in active_gis_text,
        "active GIS tables do not contain obsolete Gungdongsan location rows",
        blockers,
        passes,
    )

    public_blockers, public_passes = scan_public_tree(args.public_root)
    blockers.extend(public_blockers)
    passes.extend(public_passes)
    markdown_blockers, markdown_passes = validate_markdown_tables(args.public_root)
    blockers.extend(markdown_blockers)
    passes.extend(markdown_passes)
    html_blockers, html_passes = validate_public_html(args.public_root)
    blockers.extend(html_blockers)
    passes.extend(html_passes)
    github_blockers, github_passes = github_contributor_check(args.skip_github)
    blockers.extend(github_blockers)
    passes.extend(github_passes)

    results = {
        "passed": not blockers,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "public_root": str(args.public_root),
        "blockers": blockers,
        "warnings": warnings,
        "passes": passes,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(build_report(results), encoding="utf-8")

    print(f"Quality gate {'PASS' if results['passed'] else 'FAIL'}")
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    if blockers:
        for blocker in blockers:
            print(f"BLOCKER: {blocker}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
