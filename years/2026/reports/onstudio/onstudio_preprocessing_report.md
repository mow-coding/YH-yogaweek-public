# ON STUDIO 전처리 리포트

이 리포트는 분석 결과가 아니라, CSV 전처리 결과가 원본 수집 현황과 맞는지 확인하기 위한 검증 기록이다.

## 생성 파일

- `data\processed\onstudio\public\onstudio_classes_2026_yeonhui_yoga_week.csv`
- `data\processed\onstudio\private\onstudio_teachers_2026_yeonhui_yoga_week.csv`
- `data\processed\onstudio\private\onstudio_reservation_2026_yeonhui_yoga_week.csv`
- `data\processed\onstudio\private\onstudio_cancel_2026_yeonhui_yoga_week.csv`

## 건수 검증

- 수업 정보: 125건 / 기대값 125건
- 강사 정보: 47건 / 기대값 47명
- 예약건 정보: 1611건 / 기대값 1611건
- 취소건 정보: 1048건 / 기대값 1048건
- 예약 + 취소 합계: 2659건 / 기대값 2659건

## 원본 페이지 파일 수

- `classes`: 13개
- `teachers`: 5개
- `reservations`: 82개
- `cancellations`: 54개

## 주의 또는 확인 필요

- 없음

## 보존 원칙

- 원본 txt 파일은 수정하지 않았다.
- 각 CSV 행에는 `source_file`, `source_page`, `source_line_start`, `source_line_end`를 남겼다.
- 각 CSV 행에는 원본 행 묶음을 담은 `raw_record_text`를 남겼다.
- 예약 상태는 원본 행에서 복사되지 않으므로 폴더명을 기준으로 `status`와 `status_source`를 부여했다.
