# ON STUDIO 2026-05-09 보강분 반영 기록

작성일: 2026-05-15

## 목적

초기 raw data 준비 시점은 2026-05-08이었으나, 이후 2026-05-09까지 신규 예약과 취소가 추가로 발생한 것으로 확인했다.

사용자가 제공한 예약/취소 보강 자료를 기존 원본 데이터와 대조한 뒤, 중복을 제외하고 누락분만 raw data에 추가했다.

## 대조 결과

| 구분 | 사용자가 제공한 건수 | 기존 원본에 이미 있던 건수 | 새로 추가한 건수 | 추가 파일 |
|---|---:|---:|---:|---|
| 예약 | 20 | 11 | 9 | `data\raw\onstudio\reservations\82p.txt` |
| 취소 | 6 | 4 | 2 | `data\raw\onstudio\cancellations\54p.txt` |

대조 기준은 다음 필드를 함께 본 것이다.

- 요청일
- 취소일
- 수업 일시
- 수업 정보
- 예약자 이름
- 전화번호
- 인원
- 예약 수단

## 재생성 결과

아래 스크립트를 다시 실행했다.

```powershell
python scripts\preprocess_onstudio.py
python scripts\deidentify_reservation_cancel.py
python scripts\build_public_duckdb.py
```

## 최종 건수

| 데이터 | 최종 건수 |
|---|---:|
| 수업 정보 | 125 |
| 강사 정보 | 47 |
| 예약 | 1611 |
| 취소 | 1048 |
| 예약 + 취소 | 2659 |
| 고유 비식별 참여자 ID | 762 |

## 검증 결과

- 전처리 경고: 0개
- 예약 비식별 public CSV 행 수: 1611
- 취소 비식별 public CSV 행 수: 1048
- 예약 비식별 public CSV 전화번호 패턴 잔존 횟수: 0
- 취소 비식별 public CSV 전화번호 패턴 잔존 횟수: 0
- 최종 private 예약/취소 CSV 기준 완전 동일 중복 키: 0개
- public DuckDB 반영: 완료

## 주의

이 보강분 raw 파일에는 개인정보가 포함되어 있으므로 GitHub 공유 대상이 아니다.

공유 가능한 분석에는 비식별 public CSV 또는 public DuckDB를 사용한다.
