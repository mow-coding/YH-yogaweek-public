# 오붓 리뷰 AI 구조화 검수 리포트

## 입력
- 수업명 매칭 완료 private 표: `years\2026\data\processed\obud_reviews\private\obud_reviews_extracted_private.csv`
- 입력 리뷰: 96건

## 출력
- AI/규칙 검수 private 표: `years\2026\data\processed\obud_reviews\private\obud_reviews_ai_checked_private.csv`
- 출력 리뷰: 96건

## 실행 상태
- Gemini API 사용 시도: False
- Gemini 모델: `gemini-2.5-flash`
- Gemini 사전 확인 상태: `api_not_requested`
- 행별 Gemini 오류 후 fallback: 0건
- Pydantic 검증 실패: 0건

## 검수 결과
- 전건 Gemini Vision 검수 완료: True
- Gemini Vision 구조화 검수 성공: 96건
- 규칙 기반 fallback: 0건
- `needs_review=true`: 0건
- 평균 confidence: 0.989
- 검수 모드별 건수:
ai_validation_mode
gemini_vision_structured_output    96
- Gemini 모델별 건수:
ai_model
gemini-3.1-flash-lite    67
gemini-2.5-flash         29

주의: Gemini API가 제한 또는 비활성 상태이면 이 스크립트는 전체 파이프라인을 멈추지 않고
Google Vision OCR 결과, RapidFuzz 매칭 점수, 규칙 기반 태그를 사용해 검수 표를 만든다.
이 경우 리포트에는 `rule_based_fallback`으로 명시한다.
