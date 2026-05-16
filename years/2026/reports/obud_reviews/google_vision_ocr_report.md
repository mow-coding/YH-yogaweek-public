# 오붓 리뷰 Google Vision OCR 실행 리포트

작성일: 2026-05-15

## 실행 목적

오붓 리뷰 스크린샷 96개를 Google Cloud Vision `DOCUMENT_TEXT_DETECTION`으로 OCR 처리했다.

로컬 EasyOCR 테스트보다 Google Vision OCR 결과가 수업명, 리뷰 본문, 별점, 방문 회차를 더 안정적으로 읽는 것으로 확인되어 Google Vision을 기본 OCR 엔진으로 사용한다.

## 입력

- 입력 폴더: `data\raw\obud_reviews\screenshots`
- 이미지 수: 96개
- 사용자가 설명한 정렬 기준: 가장 최근 리뷰부터 촬영

## 출력

- 개별 OCR 텍스트: `data\raw\obud_reviews\ocr_text\*.google_vision.txt`
- 개별 OCR 원본 응답 JSON: `data\raw\obud_reviews\ocr_text\*.google_vision.response.json`
- 실행 manifest: `data\interim\obud_reviews\google_vision_ocr_manifest.csv`
- 통합 raw OCR CSV: `data\interim\obud_reviews\google_vision_ocr_raw.csv`

## 결과

| 항목 | 값 |
|---|---:|
| 스크린샷 수 | 96 |
| OCR 텍스트 파일 수 | 96 |
| 통합 raw OCR CSV 행 수 | 96 |
| OCR 텍스트 총 글자 수 | 18179 |
| 누락 OCR 텍스트 파일 | 0 |

## 실행 메모

초기에는 Google Cloud Vision API가 비활성화되어 403 오류가 발생했다.

이후 Cloud Vision API를 활성화했고, API key 제한에 Cloud Vision API를 허용한 뒤 OCR 호출이 성공했다.

일부 요청은 API key 제한 변경 전파 지연으로 일시적인 403 오류가 발생했으나, 재시도 후 모두 성공했다.

API key 값은 코드와 문서에 기록하지 않았고, 로컬 `Downloads\google-api.txt`에서만 읽었다.

## 다음 단계

1. OCR 텍스트에서 작성자 마스킹명, 날짜, 방문 회차, 별점, 수업명, 리뷰 본문, 이용권을 파싱한다.
2. OCR 수업명을 ON STUDIO 수업 DB와 유사도 매칭해 표준 수업명으로 보정한다.
3. 검수 필요 행을 표시한 리뷰 검수용 CSV를 만든다.
4. 예약/취소 데이터와 결합해 수업별 리뷰 수, 리뷰 작성률, Hype 지수 후보를 계산한다.
