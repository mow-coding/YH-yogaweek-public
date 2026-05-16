# 오붓 리뷰 OCR 및 매칭 기록

작성일: 2026-05-15

## 현재 상태

오붓 플랫폼 리뷰 화면은 마우스 드래그 복사가 되지 않아 스크린샷 기반 OCR로 처리했다.

- 원본 스크린샷 위치: `data/raw/obud_reviews/screenshots`
- 스크린샷 수: 96개
- 촬영 순서: 최신순, `review_capture_order=1`이 가장 최근 리뷰
- 기본 OCR 엔진: Google Cloud Vision `DOCUMENT_TEXT_DETECTION`
- OCR 텍스트 위치: `data/raw/obud_reviews/ocr_text`
- OCR raw 통합표: `data/interim/obud_reviews/google_vision_ocr_raw.csv`

## 구조화 필드

`scripts/parse_obud_reviews.py`는 OCR 텍스트에서 다음 필드를 추출한다.

- `review_id`
- `review_capture_order`
- `source_image`
- `masked_reviewer`
- `review_date_iso`
- `visit_count`
- `overall_rating`
- `class_rating`
- `atmosphere_rating`
- `facility_rating`
- `class_title_ocr`
- `review_text_ocr`
- `ticket_type_ocr`
- `ticket_count`
- `parse_needs_review`

현재 추출 결과는 96건 모두 작성자/날짜/방문회차/별점/수업명/본문이 추출되었다.

## 수업명 매칭

`scripts/match_review_classes.py`는 OCR 수업명을 ON STUDIO 수업 DB와 매칭한다.

참조 데이터는 다음 세 곳을 함께 사용한다.

- `data/processed/onstudio/public/onstudio_classes_2026_yeonhui_yoga_week.csv`
- `data/processed/onstudio/public/onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv`
- `data/processed/onstudio/public/onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv`

방식은 다음과 같다.

1. OCR 수업명에서 공백, 특수문자, 괄호 차이를 줄인다.
2. 영어로 OCR된 일부 표현을 한국어 표준 수업명 후보로 보정한다.
3. `RapidFuzz`의 WRatio/token set score로 유사도를 계산한다.
4. 90점 이상은 자동 승인, 90점 미만은 `class_match_needs_review=true`로 표시한다.

현재 결과는 96건 모두 90점 이상으로 매칭되었다.

## AI 구조화 검수

`scripts/ai_review_quality_check.py`는 Gemini Vision API를 사용해 원본 이미지와 Google Vision OCR 텍스트를 함께 보고 JSON 구조화 검수를 수행한다.

현재 최종 실행 결과는 다음과 같다.

- 검수 행 수: 96건
- Gemini Vision 구조화 검수 성공: 96건
- 규칙 기반 fallback: 0건
- Pydantic 검증 실패: 0건
- 검수 모드: `gemini_vision_structured_output`
- API 상태: `available`
- 모델 사용 내역: `gemini-2.5-flash` 29건, `gemini-3.1-flash-lite` 67건

처음 29건은 `gemini-2.5-flash`로 검수했고, 중간에 쿼터 제한이 발생해 성공한 29건은 보존한 뒤 남은 67건을 `gemini-3.1-flash-lite`로 이어서 검수했다.
두 모델 모두 같은 Pydantic 스키마로 검증했으며, 최종 public 분석표는 Gemini 검수 완료본을 기준으로 다시 생성했다.

API key는 용도별로 분리해 로컬 전용으로 보관한다.

- Google Vision OCR용: `.secrets/google-api.txt`
- Gemini 검수용: `.secrets/gemini-api.txt`

두 파일은 `.gitignore`로 GitHub 공유 대상에서 제외한다.

API key가 없거나 Gemini API 제한이 다시 발생하는 경우에도 전체 파이프라인은 멈추지 않고 Google Vision OCR 결과, RapidFuzz 수업명 매칭 결과, 규칙 기반 confidence/tag를 사용한 fallback 결과를 Pydantic으로 검증한다.

```powershell
python scripts\ai_review_quality_check.py --use-api
```

## 리뷰 작성자 내부 매칭

`scripts/match_reviewers_private.py`는 리뷰의 마스킹 작성자와 ON STUDIO 예약자 데이터를 내부 후보로 대조한다.

이 출력에는 실명과 전화번호 후보가 들어갈 수 있으므로 외부 공유 대상이 아니다.

- 출력: `data/processed/obud_reviews/private/review_reviewer_match_private.csv`
- public 리포트에는 실명, 전화번호, 확정 개인 식별자를 넣지 않는다.

현재 자동 매칭은 대부분 `multiple_candidates` 상태다. 즉, 수업명과 티켓 유형으로 후보를 좁힐 수는 있지만, 마스킹명만으로 개인을 확정하기에는 부족하다는 뜻이다.

## public 산출물

외부 공유용 리뷰 데이터는 다음 파일을 사용한다.

- `data/processed/obud_reviews/public/obud_reviews_deidentified.csv`

public 표에는 `masked_reviewer`를 직접 넣지 않고 `reviewer_####` 형태의 public ID만 넣었다.
