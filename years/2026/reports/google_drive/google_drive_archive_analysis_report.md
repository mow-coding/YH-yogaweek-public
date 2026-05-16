# Google Drive Archive Analysis Report

작성일: 2026-05-16

## 요약

- manifest 전체 행: 490
- 로컬 보존 원본 사본: 384
- 2026 이전 제외: 24
- 실패: 0

## 분석 축별 원본 사본 수

- sponsor / 3스폰서: 원본 사본 174개, private/sensitive 후보 0개
- program / 1프로그램 리스트: 원본 사본 114개, private/sensitive 후보 0개
- fnb / 4F&B: 원본 사본 74개, private/sensitive 후보 0개
- design / 2디자인 (포스터): 원본 사본 7개, private/sensitive 후보 0개
- other / 도움이 되시길 바랍니다: 원본 사본 7개, private/sensitive 후보 0개
- recovery / 리커버리트랙: 원본 사본 1개, private/sensitive 후보 2개
- operations_response / 2026연희요가위크 크루 모집(응답): 원본 사본 1개, private/sensitive 후보 1개
- other / 2월_연희요가위크_요가명상원(저용량).pdf: 원본 사본 1개, private/sensitive 후보 0개
- other / 3월 30일- 오붓 오픈 정말 마지막 부탁드려요: 원본 사본 1개, private/sensitive 후보 0개
- other / coupon_yeonhui_week_obud.xlsx: 원본 사본 1개, private/sensitive 후보 1개
- other / 연희요가위크 기본 텍스트 및 전달 부탁 사항: 원본 사본 1개, private/sensitive 후보 0개
- other / 연희요가축제_인터뷰_공유2: 원본 사본 1개, private/sensitive 후보 0개
- other / 연희축제 프로그램: 원본 사본 1개, private/sensitive 후보 0개
- other / unknown: 원본 사본 0개, private/sensitive 후보 0개

## 다음 분석 기회

- program_design: 어떤 수업/외부연사/공간 구성이 행사 반응을 만들었는가?
  - 방법: 문서 인벤토리, 수업 카테고리 태깅, Hype/Capacity/GIS 결합
  - 공유 범위: public derivative only
- sponsor_network: 어떤 스폰서가 어떤 형태의 지원/노출/콘텐츠로 연결되었는가?
  - 방법: 스폰서 asset inventory, 후원 유형 분류, 노출자료 집계
  - 공유 범위: internal review before sharing
- local_consumption_route: 요가원 방문 동선이 주변 F&B 협업과 어떻게 이어질 수 있는가?
  - 방법: F&B inventory, 주소/좌표 보강, 요가원-상점 거리/동선 분석
  - 공유 범위: public derivative after address verification
- promotion_asset_archive: 어떤 홍보물/디자인 asset이 다음 회차에 재사용 가능한가?
  - 방법: asset type summary, 재사용 가능 asset 구분, public/private 구분
  - 공유 범위: internal raw, public summary only
- operations_and_recovery: 크루/리커버리 운영 참여 데이터에서 다음 운영 개선점은 무엇인가?
  - 방법: private-only 응답 집계, 개인정보 제거 후 운영 지표화
  - 공유 범위: private only unless fully aggregated

## 산출물

- `data\processed\analysis\public\google_drive_archive_area_summary.csv`
- `data\processed\analysis\public\google_drive_archive_asset_type_summary.csv`
- `data\processed\analysis\public\google_drive_archive_analysis_opportunity_matrix.csv`

## 한계

- 이 단계는 Drive 원문 내용을 전부 읽어 의미 분석한 것이 아니라, manifest와 폴더 구조를 기준으로 분석 기회를 정리한 것이다.
- 스폰서/F&B 자료는 public 공유 전 브랜드명, 계약 조건, 쿠폰 조건, 이미지 권리 검토가 필요하다.
- 크루/응답 시트는 개인정보 가능성이 있어 private-only 원칙을 적용한다.
