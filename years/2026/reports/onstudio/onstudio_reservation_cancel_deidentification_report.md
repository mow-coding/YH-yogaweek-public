# ON STUDIO 예약/취소 비식별 사본 생성 리포트

이 리포트는 예약/취소 CSV의 개인정보 비식별 사본 생성 결과를 기록한다.

## 처리 원칙

- 원본 CSV 파일은 수정하지 않았다.
- 예약/취소 비식별 사본은 원본과 같은 21개 컬럼 구조를 유지한다.
- `reserver_name`에는 실제 이름 대신 `participant_0001` 형식의 비식별 ID를 넣었다.
- `phone`에는 실제 전화번호 대신 `PHONE_MASKED`를 넣었다.
- `raw_record_text` 안의 고객 이름과 전화번호도 같은 방식으로 교체했다.
- 비식별 ID는 예약/취소 두 파일 전체에서 같은 `전화번호 + 이름` 조합에 같은 값이 부여되도록 만들었다.
- 기존 비식별 사본이 있으면 기존 participant ID를 최대한 유지하고, 새 고객에게만 다음 번호를 부여했다.
- 원본 개인정보와 비식별 ID를 연결하는 별도 매핑 파일은 만들지 않았다.

## 생성 파일

- `data\processed\onstudio\public\onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv`
- `data\processed\onstudio\public\onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv`

## 검증 결과

- 고유 비식별 참여자 ID 수: 762
- `onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv`
  - 행 수: 1611 / 기대값 1611
  - `reserver_name`이 participant ID 형식이 아닌 행: 0
  - `phone`이 `PHONE_MASKED`가 아닌 행: 0
  - 파일 전체 전화번호 패턴 잔존 횟수: 0
- `onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv`
  - 행 수: 1048 / 기대값 1048
  - `reserver_name`이 participant ID 형식이 아닌 행: 0
  - `phone`이 `PHONE_MASKED`가 아닌 행: 0
  - 파일 전체 전화번호 패턴 잔존 횟수: 0
