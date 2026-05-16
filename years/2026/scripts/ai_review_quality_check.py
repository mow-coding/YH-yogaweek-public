from __future__ import annotations

import argparse
import base64
import json
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from pydantic import BaseModel, Field, ValidationError

from review_processing_utils import (
    OBUD_AI_CHECKED_PRIVATE,
    OBUD_EXTRACTED_PRIVATE,
    REPORT_OBUD_DIR,
    ROOT,
    compact_spaces,
    safe_float,
    safe_int,
    write_csv,
    write_text,
)


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_ENDPOINT_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
)


class ReviewQualityRecord(BaseModel):
    review_id: str
    review_capture_order: int
    source_image: str
    masked_reviewer: str | None = None
    review_date_iso: str | None = None
    visit_count: int | None = None
    overall_rating: float | None = Field(default=None, ge=0, le=5)
    class_rating: float | None = Field(default=None, ge=0, le=5)
    atmosphere_rating: float | None = Field(default=None, ge=0, le=5)
    facility_rating: float | None = Field(default=None, ge=0, le=5)
    class_title_ocr: str | None = None
    class_title_matched: str | None = None
    class_title_base: str | None = None
    class_key: str | None = None
    class_base_key: str | None = None
    studio_key: str | None = None
    review_text: str | None = None
    ticket_type: str | None = None
    ticket_count: int | None = None
    class_match_score: float | None = Field(default=None, ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    needs_review: bool
    ai_provider: str
    ai_model: str | None = None
    ai_provider_status: str
    ai_validation_mode: str
    ai_tags_json: str
    representative_sentence: str | None = None
    ai_notes: str | None = None


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def read_google_api_key() -> str:
    import os

    env_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if env_key:
        return env_key

    candidates = [ROOT / ".secrets" / "gemini-api.txt"]
    env_file = os.environ.get("GOOGLE_API_KEY_FILE", "").strip()
    gemini_env_file = os.environ.get("GEMINI_API_KEY_FILE", "").strip()
    gemini_env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_env_key:
        return gemini_env_key
    if gemini_env_file:
        candidates.append(Path(gemini_env_file))
    if env_file:
        candidates.append(Path(env_file))
    candidates.extend(
        [
            ROOT / ".secrets" / "google-api.txt",
            Path.home() / "Downloads" / "google-api.txt",
            Path.home() / "Downloads" / "gemini-api.txt",
            Path.home() / "다운로드" / "google-api.txt",
            Path.home() / "다운로드" / "gemini-api.txt",
        ]
    )

    for key_path in candidates:
        if key_path.exists():
            return key_path.read_text(encoding="utf-8-sig").strip()
    return ""


def gemini_endpoint(api_key: str, model: str) -> str:
    return GEMINI_ENDPOINT_TEMPLATE.format(model=model, api_key=api_key)


def check_gemini_available(api_key: str, model: str) -> tuple[bool, str]:
    if not api_key:
        return False, "api_key_missing"

    body = {
        "contents": [{"parts": [{"text": 'Return only {"ok": true} as JSON.'}]}],
        "generationConfig": {"temperature": 0, "response_mime_type": "application/json"},
    }
    try:
        response = requests.post(gemini_endpoint(api_key, model), json=body, timeout=30)
    except requests.RequestException as exc:
        return False, f"request_error:{type(exc).__name__}"

    if response.status_code == 200:
        return True, "available"

    status = f"http_{response.status_code}"
    try:
        payload = response.json()
        message = payload.get("error", {}).get("message", "")
        reason = (
            payload.get("error", {})
            .get("details", [{}])[0]
            .get("reason", "")
        )
        detail = reason or message
        if detail:
            status = f"{status}:{detail[:120]}"
    except ValueError:
        status = f"{status}:{response.text[:120]}"
    return False, status


def extract_json_object(text: str) -> dict[str, Any]:
    clean = text.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?", "", clean).strip()
        clean = re.sub(r"```$", "", clean).strip()
    first = clean.find("{")
    last = clean.rfind("}")
    if first >= 0 and last >= first:
        clean = clean[first : last + 1]
    return json.loads(clean)


def call_gemini_for_row(row: pd.Series, api_key: str, model: str) -> dict[str, Any]:
    image_path = ROOT / "data" / "raw" / "obud_reviews" / "screenshots" / str(row["source_image"])
    image_bytes = image_path.read_bytes()
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    prompt = f"""
You are checking one Korean yoga festival review screenshot.
Use both the image and OCR text. Return one JSON object only.

Required fields:
- review_date_iso: YYYY-MM-DD or null
- visit_count: integer or null
- overall_rating, class_rating, atmosphere_rating, facility_rating: number 0-5 or null
- class_title_ocr: string or null
- review_text: string or null
- ticket_type: string or null
- confidence: number 0-1
- needs_review: boolean
- representative_sentence: string or null
- ai_notes: short Korean note
- ai_tags: object with boolean keys instructor, space, atmosphere, difficulty, recovery, revisit_intent

Existing OCR/parsed values:
{row.to_json(force_ascii=False)}
"""
    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": encoded_image}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0, "response_mime_type": "application/json"},
    }
    response = requests.post(gemini_endpoint(api_key, model), json=body, timeout=60)
    response.raise_for_status()
    payload = response.json()
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    return extract_json_object(text)


def call_gemini_for_row_with_retry(
    row: pd.Series,
    api_key: str,
    model: str,
    max_retries: int,
    sleep_seconds: float,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return call_gemini_for_row(row, api_key, model)
        except requests.HTTPError as exc:
            last_error = exc
            status_code = exc.response.status_code if exc.response is not None else 0
            if status_code not in {429, 500, 502, 503, 504} or attempt >= max_retries:
                raise
        except requests.RequestException as exc:
            last_error = exc
            if attempt >= max_retries:
                raise

        wait = sleep_seconds * (attempt + 1)
        time.sleep(wait)

    if last_error:
        raise last_error
    raise RuntimeError("Gemini retry loop failed without an exception.")


def first_sentence(text: str) -> str:
    clean = compact_spaces(text)
    if not clean:
        return ""
    match = re.match(r"(.{1,180}?(?:[.!?。]|요\.|다\.|요!|요\?))", clean)
    if match:
        return match.group(1)[:180]
    return clean[:180]


def infer_tags(text: str) -> dict[str, bool]:
    clean = str(text)
    return {
        "instructor": bool(re.search(r"쌤|선생|강사|요가소년|모나|준형|유미|환", clean)),
        "space": bool(re.search(r"공간|장소|연남장|옥상|야외|바람|날씨|커뮤니티허브", clean)),
        "atmosphere": bool(re.search(r"분위기|따스|편안|좋았|새로웠|연결|따뜻", clean)),
        "difficulty": bool(re.search(r"어렵|쉬운|초보|비기너|난이도|도전", clean)),
        "recovery": bool(re.search(r"회복|이완|힐링|상쾌|쉼|편안|내려놓", clean)),
        "revisit_intent": bool(re.search(r"또|다시|다음|무한|재방문|해줘", clean)),
    }


def fallback_confidence(row: pd.Series) -> float:
    confidence = 1.0
    if str(row.get("parse_needs_review", "")).lower() == "true":
        confidence -= 0.15
    if str(row.get("class_match_needs_review", "")).lower() == "true":
        confidence -= 0.15
    for field in ["overall_rating", "class_rating", "atmosphere_rating", "facility_rating"]:
        if safe_float(row.get(field, "")) is None:
            confidence -= 0.05
    if not compact_spaces(row.get("review_text_ocr", "")):
        confidence -= 0.1
    if not compact_spaces(row.get("ticket_type_ocr", "")):
        confidence -= 0.03
    return round(max(0.0, min(1.0, confidence)), 2)


def build_fallback_record(row: pd.Series, provider_status: str, model: str | None = None) -> ReviewQualityRecord:
    tags = infer_tags(str(row.get("review_text_ocr", "")))
    confidence = fallback_confidence(row)
    needs_review = (
        str(row.get("needs_review", "")).lower() == "true"
        or str(row.get("parse_needs_review", "")).lower() == "true"
        or str(row.get("class_match_needs_review", "")).lower() == "true"
        or confidence < 0.85
    )
    return ReviewQualityRecord(
        review_id=str(row["review_id"]),
        review_capture_order=int(row["review_capture_order"]),
        source_image=str(row.get("source_image", "")),
        masked_reviewer=str(row.get("masked_reviewer", "")) or None,
        review_date_iso=str(row.get("review_date_iso", "")) or None,
        visit_count=safe_int(row.get("visit_count", "")),
        overall_rating=safe_float(row.get("overall_rating", "")),
        class_rating=safe_float(row.get("class_rating", "")),
        atmosphere_rating=safe_float(row.get("atmosphere_rating", "")),
        facility_rating=safe_float(row.get("facility_rating", "")),
        class_title_ocr=str(row.get("class_title_ocr", "")) or None,
        class_title_matched=str(row.get("class_title_matched", "")) or None,
        class_title_base=str(row.get("class_title_base", "")) or None,
        class_key=str(row.get("class_key", "")) or None,
        class_base_key=str(row.get("class_base_key", "")) or None,
        studio_key=str(row.get("studio_key", "")) or None,
        review_text=str(row.get("review_text_ocr", "")) or None,
        ticket_type=str(row.get("ticket_type_ocr", "")) or None,
        ticket_count=safe_int(row.get("ticket_count", "")),
        class_match_score=safe_float(row.get("class_match_score", "")),
        confidence=confidence,
        needs_review=needs_review,
        ai_provider="gemini",
        ai_model=model,
        ai_provider_status=provider_status,
        ai_validation_mode="rule_based_fallback",
        ai_tags_json=json.dumps(tags, ensure_ascii=False, sort_keys=True),
        representative_sentence=first_sentence(str(row.get("review_text_ocr", ""))) or None,
        ai_notes="Gemini API를 사용할 수 없어 OCR/규칙 기반 검수값으로 대체함.",
    )


def build_gemini_record(row: pd.Series, gemini_result: dict[str, Any], model: str) -> ReviewQualityRecord:
    tags = gemini_result.get("ai_tags") or infer_tags(str(row.get("review_text_ocr", "")))
    confidence = float(gemini_result.get("confidence") or fallback_confidence(row))
    return ReviewQualityRecord(
        review_id=str(row["review_id"]),
        review_capture_order=int(row["review_capture_order"]),
        source_image=str(row.get("source_image", "")),
        masked_reviewer=str(row.get("masked_reviewer", "")) or None,
        review_date_iso=gemini_result.get("review_date_iso") or str(row.get("review_date_iso", "")) or None,
        visit_count=safe_int(gemini_result.get("visit_count") or row.get("visit_count", "")),
        overall_rating=safe_float(gemini_result.get("overall_rating") or row.get("overall_rating", "")),
        class_rating=safe_float(gemini_result.get("class_rating") or row.get("class_rating", "")),
        atmosphere_rating=safe_float(gemini_result.get("atmosphere_rating") or row.get("atmosphere_rating", "")),
        facility_rating=safe_float(gemini_result.get("facility_rating") or row.get("facility_rating", "")),
        class_title_ocr=gemini_result.get("class_title_ocr") or str(row.get("class_title_ocr", "")) or None,
        class_title_matched=str(row.get("class_title_matched", "")) or None,
        class_title_base=str(row.get("class_title_base", "")) or None,
        class_key=str(row.get("class_key", "")) or None,
        class_base_key=str(row.get("class_base_key", "")) or None,
        studio_key=str(row.get("studio_key", "")) or None,
        review_text=gemini_result.get("review_text") or str(row.get("review_text_ocr", "")) or None,
        ticket_type=gemini_result.get("ticket_type") or str(row.get("ticket_type_ocr", "")) or None,
        ticket_count=safe_int(row.get("ticket_count", "")),
        class_match_score=safe_float(row.get("class_match_score", "")),
        confidence=round(max(0.0, min(1.0, confidence)), 2),
        needs_review=bool(gemini_result.get("needs_review")) or str(row.get("needs_review", "")).lower() == "true",
        ai_provider="gemini",
        ai_model=model,
        ai_provider_status="available",
        ai_validation_mode="gemini_vision_structured_output",
        ai_tags_json=json.dumps(tags, ensure_ascii=False, sort_keys=True),
        representative_sentence=gemini_result.get("representative_sentence")
        or first_sentence(str(row.get("review_text_ocr", "")))
        or None,
        ai_notes=gemini_result.get("ai_notes") or "Gemini Vision structured output으로 검수함.",
    )


def sync_class_match_fields(existing_record: dict[str, Any], row: pd.Series) -> dict[str, Any]:
    """Keep Gemini text/rating/tag extraction, but refresh deterministic class matching fields."""
    synced = dict(existing_record)
    for field in [
        "class_title_matched",
        "class_title_base",
        "class_key",
        "class_base_key",
        "studio_key",
        "class_match_score",
    ]:
        synced[field] = str(row.get(field, "")) or None

    synced["needs_review"] = str(row.get("needs_review", "")).lower() == "true"
    if synced.get("ai_notes"):
        synced["ai_notes"] = (
            f"{synced['ai_notes']} / class match fields refreshed from latest deterministic matcher."
        )
    return synced


def true_count(series: pd.Series) -> int:
    return int(series.astype(str).str.lower().isin(["true", "1", "yes"]).sum())


def ordered_records(record_map: dict[str, dict[str, Any]], reviews: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for review_id in reviews["review_id"].astype(str):
        record = record_map.get(review_id)
        if record is not None:
            records.append(record)
    return records


def checkpoint_records(record_map: dict[str, dict[str, Any]], reviews: pd.DataFrame) -> None:
    checkpoint = pd.DataFrame(ordered_records(record_map, reviews))
    if not checkpoint.empty:
        write_csv(checkpoint, OBUD_AI_CHECKED_PRIVATE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-api", action="store_true", help="Try Gemini Vision structured extraction.")
    parser.add_argument("--model", default=DEFAULT_GEMINI_MODEL)
    parser.add_argument("--sleep", type=float, default=2.5, help="Seconds to wait between Gemini row calls.")
    parser.add_argument("--max-retries", type=int, default=4, help="Retry count for transient Gemini HTTP errors.")
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1,
        help="Write the private CSV after every N newly processed rows. Use 0 to disable.",
    )
    parser.add_argument(
        "--preserve-success",
        action="store_true",
        help="Keep existing Gemini-success rows and only retry rows that previously fell back.",
    )
    args = parser.parse_args()

    if not OBUD_EXTRACTED_PRIVATE.exists():
        raise FileNotFoundError(
            f"Missing class-matched review table. Run scripts/match_review_classes.py first: {OBUD_EXTRACTED_PRIVATE}"
        )

    reviews = pd.read_csv(OBUD_EXTRACTED_PRIVATE, dtype=str, keep_default_na=False)
    record_map: dict[str, dict[str, Any]] = {}
    if OBUD_AI_CHECKED_PRIVATE.exists():
        existing_all = pd.read_csv(OBUD_AI_CHECKED_PRIVATE, dtype=str, keep_default_na=False)
        record_map = {
            str(row["review_id"]): row.to_dict()
            for _, row in existing_all.iterrows()
        }

    existing_records: dict[str, dict[str, Any]] = {}
    if args.preserve_success and OBUD_AI_CHECKED_PRIVATE.exists():
        existing = pd.read_csv(OBUD_AI_CHECKED_PRIVATE, dtype=str, keep_default_na=False)
        success = existing[existing["ai_validation_mode"].eq("gemini_vision_structured_output")]
        existing_records = {
            str(row["review_id"]): {
                **row.to_dict(),
                "ai_model": row.to_dict().get("ai_model") or DEFAULT_GEMINI_MODEL,
            }
            for _, row in success.iterrows()
        }

    api_key = read_google_api_key() if args.use_api else ""
    api_available = False
    provider_status = "api_not_requested"

    if args.use_api:
        api_available, provider_status = check_gemini_available(api_key, args.model)

    validation_failures: list[str] = []
    gemini_row_errors = 0
    newly_processed = 0

    for _, row in reviews.iterrows():
        review_id = str(row["review_id"])
        existing_record = existing_records.get(review_id)
        if existing_record is not None:
            record_map[review_id] = sync_class_match_fields(existing_record, row)
            continue

        try:
            if api_available:
                try:
                    result = call_gemini_for_row_with_retry(
                        row=row,
                        api_key=api_key,
                        model=args.model,
                        max_retries=args.max_retries,
                        sleep_seconds=args.sleep,
                    )
                    record = build_gemini_record(row, result, args.model)
                    time.sleep(args.sleep)
                except Exception as exc:  # noqa: BLE001 - row-level fallback is intentional here.
                    gemini_row_errors += 1
                    record = build_fallback_record(row, f"row_fallback:{type(exc).__name__}", args.model)
            else:
                record = build_fallback_record(row, provider_status, args.model if args.use_api else None)
            record_map[review_id] = model_to_dict(record)
            newly_processed += 1
            if args.checkpoint_every and newly_processed % args.checkpoint_every == 0:
                checkpoint_records(record_map, reviews)
                print(f"Checkpoint saved after {newly_processed} newly processed rows")
        except ValidationError as exc:
            validation_failures.append(f"{row.get('review_id', 'unknown')}: {exc}")

    if validation_failures:
        raise RuntimeError("Pydantic validation failed:\n" + "\n".join(validation_failures[:10]))

    output = pd.DataFrame(ordered_records(record_map, reviews))
    write_csv(output, OBUD_AI_CHECKED_PRIVATE)

    report_path = REPORT_OBUD_DIR / "obud_review_ai_quality_check_report.md"
    mode_counts = output["ai_validation_mode"].value_counts()
    gemini_success_count = int(mode_counts.get("gemini_vision_structured_output", 0))
    fallback_count = int(mode_counts.get("rule_based_fallback", 0))
    full_gemini_complete = gemini_success_count == len(output)
    report = f"""# 오붓 리뷰 AI 구조화 검수 리포트

## 입력
- 수업명 매칭 완료 private 표: `{OBUD_EXTRACTED_PRIVATE.relative_to(Path.cwd())}`
- 입력 리뷰: {len(reviews)}건

## 출력
- AI/규칙 검수 private 표: `{OBUD_AI_CHECKED_PRIVATE.relative_to(Path.cwd())}`
- 출력 리뷰: {len(output)}건

## 실행 상태
- Gemini API 사용 시도: {args.use_api}
- Gemini 모델: `{args.model}`
- Gemini 사전 확인 상태: `{provider_status}`
- 행별 Gemini 오류 후 fallback: {gemini_row_errors}건
- Pydantic 검증 실패: {len(validation_failures)}건

## 검수 결과
- 전건 Gemini Vision 검수 완료: {full_gemini_complete}
- Gemini Vision 구조화 검수 성공: {gemini_success_count}건
- 규칙 기반 fallback: {fallback_count}건
- `needs_review=true`: {true_count(output['needs_review'])}건
- 평균 confidence: {round(output['confidence'].astype(float).mean(), 3) if len(output) else 0}
- 검수 모드별 건수:
{output['ai_validation_mode'].value_counts().to_string()}
- Gemini 모델별 건수:
{output['ai_model'].fillna('').replace('', 'unknown').value_counts().to_string() if 'ai_model' in output else 'ai_model column missing'}

주의: Gemini API가 제한 또는 비활성 상태이면 이 스크립트는 전체 파이프라인을 멈추지 않고
Google Vision OCR 결과, RapidFuzz 매칭 점수, 규칙 기반 태그를 사용해 검수 표를 만든다.
이 경우 리포트에는 `rule_based_fallback`으로 명시한다.
"""
    write_text(report_path, report)

    print(f"Quality-checked {len(output)} review rows")
    print(f"Gemini success rows: {gemini_success_count}")
    print(f"Fallback rows: {fallback_count}")
    print(f"Provider status: {provider_status}")
    print(f"Pydantic validation failures: {len(validation_failures)}")
    print(f"Wrote {OBUD_AI_CHECKED_PRIVATE}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
