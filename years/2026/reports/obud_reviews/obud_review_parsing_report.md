# 오붓 리뷰 OCR 1차 파싱 리포트

## 입력
- 원천 OCR 표: `years\2026\data\interim\obud_reviews\google_vision_ocr_raw.csv`
- 입력 행 수: 96

## 출력
- private 구조화 표: `years\2026\data\processed\obud_reviews\private\obud_reviews_extracted_private.csv`
- 출력 행 수: 96

## 추출률
- 작성자/날짜/방문회차: 96 / 96
- 전체 별점: 96 / 96
- 수업 별점: 96 / 96
- 분위기 별점: 96 / 96
- 편의시설 별점: 96 / 96
- OCR 수업명: 96 / 96
- 리뷰 본문: 96 / 96
- 티켓 종류: 51 / 96

## 검수 필요
- `parse_needs_review=true`: 0건

이 스크립트는 Google Vision OCR 결과 텍스트에서 리뷰 필드를 기계적으로 추출한다.  
개인 식별 가능성이 있는 `masked_reviewer`, 원문 OCR 텍스트는 private 산출물에만 저장한다.
