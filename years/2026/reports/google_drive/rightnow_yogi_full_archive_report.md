# rightnow.yogi Google Drive Full Archive Report

작성일: 2026-05-16

## 책임과 계정

- 책임자/관리자: 유동환, 빅블루 요가 소속
- Drive 접근 계정: bigblue.yoga@gmail.com
- 분석담당자: 김성균
- 분석담당자 연락 계정: mow.coding@gmail.com
- 공유 원천 계정: rightnow.yogi@gmail.com

## 수집 기준

- 대상은 2026년 이후 생성 또는 수정된 2026 연희요가위크/연희요가축제 관련 자료다.
- 기본 수집 범위는 `연희요가위크_정보들` 공유 폴더 전체 하위 구조다.
- 별도로 공유된 `2026연희요가위크 크루 모집(응답)`은 행사 운영 자료 후보로 추가했다.
- 원본 Google Drive 파일은 수정/삭제하지 않고, 로컬 `data/raw` 아래에 사본만 보존했다.
- `data/raw`는 GitHub 공유 대상이 아니며, public 분석에는 별도 비식별 파생표만 사용한다.

## 수집 결과

- manifest: `reports\google_drive\rightnow_yogi_full_archive_manifest.csv`
- archive root: `data\raw\google_drive_shared\rightnow_yogi\full_archive`
- 전체 기록 행: 490
- 로컬 보존 원본 사본: 384
- 이번 실행의 표준 export/download: 0
- 이번 실행의 fallback export/download: 0
- 이전 실행에서 이미 보존된 사본: 384
- 폴더 행: 82
- 2026 이전 생성/수정으로 제외: 24
- 실패: 0

## 상태별 건수

- existing_local_copy: 384
- folder: 82
- skipped_pre_2026: 24

## 민감도별 건수

- internal_review_raw: 250
- private_or_sensitive_raw: 4
- public_derivative_candidate: 236

## 실패 기록

- 없음

## 분석 활용 메모

- 프로그램/수업 자료: 정원, 일정, 장소, 클래스 설계 맥락을 ON STUDIO 예약/취소와 결합한다.
- F&B 자료: 브랜드 위치와 쿠폰 조건을 GIS 동선 및 지역 소비 확장 분석에 결합한다.
- 스폰서/디자인 자료: 파트너십 구조, 후원사 노출, 발표자료/아카이브 보강에 사용한다.
- 크루/리커버리 응답 자료: 개인정보 가능성이 높으므로 private 분석 후보로만 두고 외부 리포트에는 집계/비식별 결과만 사용한다.
