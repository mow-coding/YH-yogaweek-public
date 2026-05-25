# 2026 연희 요가 위크 데이터 분석 프로젝트

이 폴더는 `YH-yogaweek` 허브 레포지토리 안의 2026년 분석 단위입니다.

문서와 스크립트에서 쓰는 `data/...`, `reports/...`, `scripts/...` 같은 상대 경로는 이 `years/2026/` 폴더를 기준으로 합니다.

2026 연희 요가 위크의 예약, 취소, 수업, 강사, 오붓 리뷰, 티켓 가격표를 정리하고 분석하기 위한 프로젝트입니다.

## 먼저 볼 문서

현재 프로젝트 전체 현황은 `docs/project-current-status.md`에 정리되어 있습니다.

처음 보는 사람은 이 순서로 보면 됩니다.

1. `docs/project-current-status.md`: 전체 현황판
2. `docs/project-operating-standards.md`: 방법론 조사, 작업일지, 파일명/변수명/스크립트명 운영 규칙
3. `docs/work-log.md`: 정형 작업일지
4. `docs/retrospective-work-audit.md`: 지금까지 수행한 작업의 소급 감사
5. `reports/analysis/methodology_and_data_lineage.md`: 원천자료 수집부터 분석까지의 방법론과 데이터 계보
6. `reports/stakeholders/yeonhui_yoga_week_integrated_stakeholder_report.md`: 9가지 독자 관점을 묶은 통합 제출용 보고서
7. `reports/analysis/yeonhui_yoga_week_analysis_report.md`: 1차 분석 리포트
8. `scripts/README.md`: 분석을 재현할 때 실행할 스크립트 순서

현재 1차 범위는 **ON STUDIO 예약/취소 + 오붓 리뷰 96건 OCR/Gemini 검수 + 티켓 가격표 + Hype 지수 + GIS 분석 + 네이버/유튜브 외부 확산(Viral) 분석 + Google Drive 기획자료/정원표/전량 아카이브 + Notion 커뮤니케이션 요약 + 오붓 정산 기준 + 통합 이해관계자 보고서**입니다.
메신저, 인스타그램 데이터는 다음 단계 후보로 남겨두었습니다.

## 책임과 담당

- 책임자/관리자: 유동환, 빅블루 요가 소속 (`bigblue.yoga@gmail.com`)
- 분석담당자: 김성균, 빅블루 요가 소속 (`mow.coding@gmail.com`)
- Google Drive 수집 범위: `bigblue.yoga@gmail.com` 계정에서 `rightnow.yogi@gmail.com`으로부터 공유받은 2026년 이후 연희 요가 축제 관련 자료

## 현재 완료된 작업

- ON STUDIO 원본 txt를 수업/강사/예약/취소 CSV로 전처리했습니다.
- 예약/취소 데이터의 예약자 이름과 전화번호를 비식별 처리한 public CSV를 만들었습니다.
- 오붓 리뷰 스크린샷 96개를 Google Vision OCR로 처리했습니다.
- OCR 결과에서 작성자 마스킹명, 작성일, 방문회차, 별점, 수업명, 리뷰 본문, 티켓 정보를 구조화했습니다.
- OCR 수업명을 ON STUDIO 수업 DB와 `RapidFuzz`로 매칭했습니다.
- Gemini Vision API로 오붓 리뷰 96건을 전건 구조화 검수했고, 결과를 Pydantic 스키마로 검증했습니다.
- 리뷰 작성자와 예약자 후보를 private 내부 표로만 매칭했습니다.
- public 리뷰표, 수업별 Hype metrics, 요가원별 Hype metrics, 분석 리포트, 데이터 계보 문서를 생성했습니다.
- ON STUDIO 수업 설명과 공개 웹 검색을 바탕으로 요가원/행사 장소 좌표를 만들고 GIS 1차 분석 산출물을 생성했습니다.
- 행사 장소 간 거리 matrix, 수업 시간표 기반 이동 가능성 표, 장소별 이동 허브성 지표, 이동 지도, 시간 흐름 지도, 시간-공간 큐브를 생성하는 GIS 심화 분석 흐름을 추가했습니다.
- 네이버 블로그와 유튜브 공개 검색 결과를 공식 API로 수집하고, `연희요가위크` 직접 언급과 2026-02-01 이후 게시일 기준으로 confirmed 외부 언급을 분리했습니다.
- confirmed 네이버 블로그 56건의 공개 본문을 수집하고, 본문 기준 행사명 확인/노이즈 위험/테마/후기 깊이/감정 강도/혼합글 위험도를 생성했습니다.
- Viral은 Hype에 합산하지 않고 별도 외부 확산 지표로 관리합니다.
- Google Drive 공유 프로그램표에서 정원 후보를 추출했고, ON STUDIO 캘린더 화면 복사본에서 실제 운영 기준 `예약수|정원`을 파싱했습니다.
- ON STUDIO 캘린더 정원표와 Google Drive 기획 정원표를 대조해 정원 변경/검토 후보를 표시했습니다.
- Google Drive 전량 아카이브는 승인 계정/공유 원천 계정 검증 후 완료했고, 원본 사본은 GitHub 공유 제외 위치에 보존했습니다.
- 공유용 Notion 문서 2건을 public 요약표로 정리했습니다.
- 9가지 독자 관점을 반영한 통합 이해관계자 보고서를 재생성했습니다.
- private 작업 레포와 별도로 sanitized public 레포 `mow-coding/YH-yogaweek`을 만들었습니다.
- public CSV 기반의 로컬 DuckDB 분석 데이터베이스를 만들었습니다.

## 현재 검증 결과

- ON STUDIO 수업: 125건
- ON STUDIO 예약: 1611건
- ON STUDIO 취소: 1048건
- 오붓 리뷰 OCR raw: 96건
- Google Vision OCR txt 파일: 96개
- 리뷰 작성자/날짜/방문회차/별점/수업명/본문 추출: 96건
- 수업명 매칭 90점 이상: 96건
- public 산출물 전화번호 패턴: 0건
- GIS 위치 seed 행: 17건
- 좌표화 완료 위치 행: 17건
- GIS 위치 카탈로그 행: 14건
- 수동 확인 필요 위치 행: 2건
- GIS 분석용 normalized studio/place 행: 12건
- GIS 심화 분석은 개인별 동선을 외부에 노출하지 않고 장소/수업 쌍 단위로만 public 집계합니다.
- 네이버 블로그 확장 검색 결과: 2415행, 고유 링크 1075개
- 유튜브 확장 검색 결과: 85행, 고유 영상 68개, 고유 채널 32개
- `연희요가위크` confirmed 외부 언급: 60건
- Viral 익명 출처: 34개
- Viral 플랫폼: 네이버 블로그 58건, 유튜브 2건
- confirmed 네이버 블로그 본문 수집 성공: 58건
- 본문에 `연희요가위크`가 직접 확인된 블로그: 56건
- 본문 기준 노이즈 위험 후보: 2건
- 본문 기준 strong/basic confirmed 블로그: 56건
- 본문 기준 수동 확인 권장 블로그: 5건
- 본문 기준 high-depth 후기/맥락 글: 30건
- 본문 기준 positive/very positive 톤 글: 47건
- Google Drive 수업 정원 후보표: 248행
- Google Drive 전량 아카이브 manifest: 490행
- Google Drive 로컬 보존 원본 사본: 384개
- Google Drive 2026 이전 제외: 24개
- Google Drive 아카이브 실패: 0건
- Google Drive 아카이브 분석 축 요약: 14행
- Google Drive 추가 분석 기회 matrix: 5행
- ON STUDIO 캘린더 정원/예약현황표: 263행
- 정원표 대조 결과: 일치 132행, 정원 불일치 58행, 낮은 신뢰도 후보 41행, 같은 시각 Google Drive 후보 없음 31행, Drive 정원 누락 1행
- 정원+Hype 수업별 결합표: 86행
- 정원+Hype 요가원별 결합표: 12행
- F&B 협업 브랜드 public/GIS 후보: 16행
- F&B 좌표 확보: 16행
- 행사 장소 300m 이내 F&B 후보: 14행
- 스폰서 asset inventory: 15행
- Notion 공유 페이지 요약: 2행
- Notion 커뮤니케이션 테마 요약: 13행
- 오붓 정산 기준 참여 수: 1회권 589명, 패스 1088명, 총 1677명
- public repo package 파일: 150개

## 주요 산출물

- `reports/analysis/yeonhui_yoga_week_analysis_report.md`
- `reports/stakeholders/yeonhui_yoga_week_integrated_stakeholder_report.md`
- `reports/analysis/methodology_and_data_lineage.md`
- `reports/analysis/gis_analysis_report.md`
- `reports/analysis/gis_geocoding_report.md`
- `reports/analysis/yeonhui_yoga_week_gis_map.html`
- `data/processed/obud_reviews/public/obud_reviews_deidentified.csv`
- `data/processed/analysis/public/class_hype_metrics.csv`
- `data/processed/analysis/public/studio_hype_metrics.csv`
- `data/processed/analysis/public/class_hype_gis.csv`
- `data/processed/analysis/public/studio_hype_gis.csv`
- `data/processed/analysis/public/studio_hype_gis.geojson`
- `data/processed/analysis/public/event_location_catalog_gis.csv`
- `data/processed/analysis/public/event_location_catalog_gis.geojson`
- `data/processed/analysis/public/location_nodes.csv`
- `data/processed/analysis/public/location_distance_matrix.csv`
- `data/processed/analysis/public/class_schedule_gis.csv`
- `data/processed/analysis/public/transition_feasibility_public.csv`
- `data/processed/analysis/public/location_transition_feasibility_public.csv`
- `reports/analysis/gis_deep_analysis_report.md`
- `reports/analysis/yeonhui_yoga_week_transition_map.html`
- `reports/analysis/yeonhui_yoga_week_time_slider_map.html`
- `reports/analysis/yeonhui_yoga_week_space_time_cube.html`
- `data/processed/analysis/public/location_mobility_role_metrics.csv`
- `docs/gis-method-references.md`
- `reports/external_web/yeonhui_yoga_week_viral_analysis_report.md`
- `reports/external_web/yeonhui_yoga_week_mention_filter_report.md`
- `data/processed/analysis/public/yeonhui_yoga_week_viral_mentions_public.csv`
- `data/processed/analysis/public/yeonhui_yoga_week_viral_overall_summary.csv`
- `data/processed/analysis/public/yeonhui_yoga_week_viral_platform_metrics.csv`
- `data/processed/analysis/public/yeonhui_yoga_week_viral_studio_metrics.csv`
- `data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_theme_summary.csv`
- `data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_studio_summary.csv`
- `reports/external_web/naver_blog_body_deep_feature_report.md`
- `data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_deep_features_public.csv`
- `data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_post_type_summary.csv`
- `data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_quality_summary.csv`
- `reports/google_drive/rightnow_yogi_manifest.md`
- `docs/google-drive-source-collection-governance.md`
- `reports/onstudio/onstudio_calendar_capacity_comparison_report.md`
- `data/processed/analysis/public/google_drive_program_capacity_reference.csv`
- `data/processed/analysis/public/onstudio_calendar_capacity_reference.csv`
- `data/processed/analysis/public/capacity_reference_comparison.csv`
- `data/database/yogaweek_public.duckdb`

## 폴더 구조

```text
data/
  raw/        원본 데이터. 개인정보/민감정보가 있을 수 있으므로 GitHub 공유 제외.
  interim/    OCR, 파싱, 중간 정리 파일.
  processed/  분석용 정리 데이터.
    onstudio/
      public/   비식별 또는 공유 가능한 ON STUDIO 데이터.
      private/  개인정보가 포함될 수 있는 내부 검증용 데이터.
    obud_reviews/
      public/   비식별 리뷰 데이터.
      private/  OCR 원문, 마스킹명, 내부 매칭표 등 민감 가능 데이터.
    analysis/
      public/   수업별/요가원별 분석 지표.
  database/   DuckDB 로컬 분석 DB. 생성물로 취급.
docs/        분석 계획, 수집 설계, 도구 설명.
reports/     전처리/분석/데이터 계보 리포트.
scripts/     반복 실행 가능한 전처리/분석 스크립트.
notebooks/   탐색 분석 노트북.
references/  티켓 가격표, 정산 공식, 참고자료.
```

## 재현 실행 순서

```powershell
python scripts\preprocess_onstudio.py
python scripts\deidentify_reservation_cancel.py
python scripts\ocr_obud_reviews_google_vision.py
python scripts\build_obud_google_ocr_raw_table.py
python scripts\parse_obud_reviews.py
python scripts\match_review_classes.py
python scripts\ai_review_quality_check.py --use-api
python scripts\match_reviewers_private.py
python scripts\build_analysis_tables.py
python scripts\geocode_studio_locations_arcgis.py
python scripts\build_gis_tables.py
python scripts\build_gis_distance_matrix.py
python scripts\build_gis_schedule_flows.py
python scripts\build_gis_deep_report.py
python scripts\collect_naver_blog_mentions.py --queries-file references\naver-blog-viral-queries-expanded.txt
python scripts\collect_youtube_mentions.py --queries-file references\external-web-viral-queries-core.txt
python scripts\build_viral_mentions_review_queue.py
python scripts\filter_yeonhui_yoga_week_mentions.py
python scripts\collect_naver_blog_bodies.py
python scripts\build_naver_blog_body_features.py
python scripts\build_naver_blog_body_deep_features.py
python scripts\build_viral_metrics.py
python scripts\extract_google_drive_program_capacity_reference.py
python scripts\parse_onstudio_calendar_capacity.py
python scripts\compare_capacity_references.py
python scripts\build_public_duckdb.py
```

`ai_review_quality_check.py --use-api`는 Gemini API key를 사용해 리뷰를 구조화 검수합니다. API key를 찾지 못하거나 API 제한이 있으면 멈추지 않고 `rule_based_fallback`으로 검수 표를 생성할 수 있게 설계했습니다.

Viral 분석은 Hype 분석과 별도 축으로 둡니다. Hype는 예약/리뷰/만족/재방문 등 행사 내부 신호이고, Viral은 네이버 블로그/유튜브 같은 외부 공개 웹 확산 신호입니다.

## 공유 주의

`data/raw`, `data/interim`, `data/processed/**/private`, `data/database`는 기본적으로 GitHub 공유 대상에서 제외합니다.

외부 공유용 결과물은 먼저 `data/processed/**/public`과 `reports`를 기준으로 검토합니다.

GitHub repository를 public으로 전환하려면 별도 공개 전 감사를 통과해야 합니다. private repository 안에서 안전해 보이는 상태와 public 공개 가능 상태는 다르므로, raw/private/database 제외 여부와 reports 안의 원본 링크, 민감 파일명, 이메일, API key, 전화번호 패턴을 다시 확인한 뒤 전환합니다.

Google Drive full archive manifest는 로컬 기록용이며 GitHub 공유 대상에서 제외합니다.
