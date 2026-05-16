# Google Drive Archive Analysis Methodology

작성일: 2026-05-16

이 문서는 Google Drive 전량 아카이브를 분석에 어떻게 사용할지 정리한다.

## 책임과 범위

- 책임자/관리자: 유동환, 빅블루 요가 소속 (`bigblue.yoga@gmail.com`)
- 분석담당자: 김성균, 빅블루 요가 소속 (`mow.coding@gmail.com`)
- Drive 접근 계정: `bigblue.yoga@gmail.com`
- Drive 공유 원천 계정: `rightnow.yogi@gmail.com`
- 분석 대상: `rightnow.yogi@gmail.com`으로부터 공유받은 2026년 이후 연희 요가 축제 관련 자료의 로컬 raw 사본과 manifest

## 방법론 기준

이 분석은 “행사 결과를 멋대로 평가하는 것”이 아니라, 이해관계자에게 설명 가능한 근거를 만드는 평가 작업으로 본다.

1. 프로그램 평가 관점
   - CDC Program Evaluation Framework의 흐름처럼 맥락, 이해관계자, 평가 질문, 신뢰 가능한 근거, 결론과 활용을 분리한다.
   - 이 프로젝트에서는 예약/취소, 리뷰, GIS, Viral, Drive 기획자료를 서로 다른 근거로 두고 결론에서 조합한다.

2. 이벤트 영향 평가 관점
   - GOV.UK major events toolkit과 eventIMPACTS toolkit처럼 attendance, social, economic/local, media/promotional evidence를 분리해 본다.
   - 연희 요가 위크는 대형 공공행사가 아니므로 경제 효과를 과장하지 않고, 지역 F&B/스폰서/공간 협업의 구조적 가능성만 본다.

3. 데이터 계보 관점
   - 원천 파일, 수집 계정, 수집 스크립트, manifest, public 파생표, 리포트를 연결해 추적 가능하게 둔다.
   - raw 원본은 GitHub 공유 대상에서 제외하고, public 분석에는 집계표와 요약만 사용한다.

4. GIS/공간 분석 관점
   - 장소와 F&B/스폰서 자료는 위치 기반 결합 후보로 남긴다.
   - 실제 보행 네트워크 분석은 OSMnx나 GeoPandas 같은 표준 도구를 사용할 수 있지만, 주소/좌표가 확인되지 않은 자료는 먼저 검수 대상으로 둔다.

## 이번 단계에서 실행하는 분석

1. Drive 아카이브 인벤토리 분석
   - 입력: `reports/google_drive/rightnow_yogi_full_archive_manifest.csv`
   - 출력:
     - `data/processed/analysis/public/google_drive_archive_area_summary.csv`
     - `data/processed/analysis/public/google_drive_archive_asset_type_summary.csv`
     - `data/processed/analysis/public/google_drive_archive_analysis_opportunity_matrix.csv`
     - `reports/google_drive/google_drive_archive_analysis_report.md`
   - 목적: 프로그램, 디자인, 스폰서, F&B, 운영 응답 자료가 각각 어떤 분석 축으로 확장될 수 있는지 정리한다.

2. Capacity + Hype 결합 분석
   - 입력:
     - `data/processed/analysis/public/onstudio_calendar_capacity_reference.csv`
     - `data/processed/analysis/public/class_hype_metrics.csv`
     - `data/processed/analysis/public/studio_hype_metrics.csv`
   - 출력:
     - `data/processed/analysis/public/class_capacity_hype_metrics.csv`
     - `data/processed/analysis/public/studio_capacity_hype_metrics.csv`
     - `reports/analysis/capacity_hype_analysis_report.md`
   - 목적: 예약 반응, 리뷰 반응, 실제 정원 대비 채움률을 분리해 내년 운영 개선 질문을 만든다.

## 해석 원칙

- “순위”보다 “반응 프로필”을 우선한다.
- 정원 대비 채움률이 높다고 무조건 좋은 수업이라고 단정하지 않는다. 정원이 작으면 sold out이 쉽게 발생할 수 있다.
- Hype가 높고 채움률도 높은 수업은 추가 회차/확장 후보로 본다.
- Hype는 높지만 채움률이 낮은 수업은 홍보 타이밍, 시간대, 장소 접근성, 설명 문구를 점검한다.
- 채움률은 높지만 리뷰/외부 확산이 낮은 수업은 만족도 수집과 후기 유도 설계를 검토한다.

## 참고 자료

- CDC Program Evaluation Framework: https://www.cdc.gov/evaluation/site.html
- CDC Program Evaluation Framework 2024 MMWR: https://www.cdc.gov/mmwr/volumes/73/rr/rr7306a1.htm
- GOV.UK Measuring the legacy and impact of major events toolkit: https://www.gov.uk/government/publications/measuring-the-legacy-and-impact-of-major-events-a-toolkit/measuring-the-legacy-and-impact-of-major-events-a-toolkit
- eventIMPACTS Toolkit: https://www.eventimpacts.com/impact-types
- Google Cloud Dataplex data lineage overview: https://cloud.google.com/dataplex/docs/lineage-views
- UW-Madison data documentation guide: https://data.wisc.edu/data-literacy/document/
- GeoPandas spatial joins: https://docs.geopandas.org/en/latest/gallery/spatial_joins.html
- OSMnx JOSS paper: https://joss.theoj.org/papers/10.21105/joss.00215
