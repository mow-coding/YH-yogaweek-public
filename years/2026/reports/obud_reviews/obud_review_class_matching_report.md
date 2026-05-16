# 오붓 리뷰 수업명 매칭 리포트

## 입력
- 리뷰 파싱 private 표: `years\2026\data\processed\obud_reviews\private\obud_reviews_extracted_private.csv`
- ON STUDIO 수업 카탈로그: `years\2026\data\processed\onstudio\public\onstudio_classes_2026_yeonhui_yoga_week.csv`
- ON STUDIO 예약/취소 수업명: `years\2026\data\processed\onstudio\public\onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv`, `years\2026\data\processed\onstudio\public\onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv`

## 방식
- Google Vision OCR에서 추출된 `class_title_ocr`을 ON STUDIO 표준 수업명 후보와 비교했다.
- 영어 OCR 표기와 일부 OCR 흔들림은 `QUERY_REPLACEMENTS` 규칙으로 먼저 보정했다.
- 이후 `RapidFuzz`의 WRatio/token set 유사도를 사용했다.
- 자동 승인 기준: 90점 이상.

## 결과
- 전체 리뷰: 96건
- 자동 승인 수업명 매칭: 96건
- 수업명 검수 필요: 0건

## 90점 미만 또는 수업명 누락 예시
- 90점 미만 자동 매칭 없음
