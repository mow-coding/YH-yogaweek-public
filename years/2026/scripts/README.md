# scripts

반복 실행 가능한 전처리/분석 스크립트를 모아둔 폴더입니다.

## 1차 분석 재현 순서

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
python scripts\extract_google_drive_program_capacity_reference.py
python scripts\parse_onstudio_calendar_capacity.py
python scripts\compare_capacity_references.py
python scripts\build_drive_archive_analysis.py
python scripts\build_capacity_hype_analysis.py
python scripts\build_fnb_sponsor_gis_analysis.py
python scripts\archive_notion_shared_pages.py
python scripts\build_integrated_stakeholder_report.py
python scripts\build_public_duckdb.py
```

Google Drive 원본 전량 아카이브는 일반 재현 순서에 넣지 않습니다. 승인 계정과 접근 권한을 사람이 먼저 확인해야 하는 별도 보안 작업입니다.

## 외부 바이럴/SNS 수집 후보

```powershell
python scripts\collect_naver_blog_mentions.py
python scripts\collect_youtube_mentions.py
python scripts\build_viral_mentions_review_queue.py
python scripts\filter_yeonhui_yoga_week_mentions.py
python scripts\collect_naver_blog_bodies.py
python scripts\build_naver_blog_body_features.py
python scripts\build_naver_blog_body_deep_features.py
python scripts\build_viral_metrics.py
```

확장 수집 시에는 다음 검색어 파일을 사용합니다.

```powershell
python scripts\collect_naver_blog_mentions.py --queries-file references\naver-blog-viral-queries-expanded.txt
python scripts\collect_youtube_mentions.py --queries-file references\external-web-viral-queries-core.txt
python scripts\build_viral_mentions_review_queue.py
python scripts\filter_yeonhui_yoga_week_mentions.py
python scripts\collect_naver_blog_bodies.py
python scripts\build_naver_blog_body_features.py
python scripts\build_naver_blog_body_deep_features.py
python scripts\build_viral_metrics.py
```

## 역할

- `preprocess_onstudio.py`: ON STUDIO 수업/강사/예약/취소 원문을 CSV로 변환합니다.
- `deidentify_reservation_cancel.py`: 예약/취소 데이터에서 이름과 전화번호를 public 공유용으로 비식별화합니다.
- `ocr_obud_reviews_google_vision.py`: 오붓 리뷰 스크린샷을 Google Cloud Vision OCR로 읽습니다.
- `build_obud_google_ocr_raw_table.py`: OCR 텍스트 파일 96개를 하나의 raw CSV로 합칩니다.
- `parse_obud_reviews.py`: OCR 텍스트에서 리뷰 작성일, 방문회차, 별점, 수업명, 본문, 티켓 정보를 1차 추출합니다.
- `match_review_classes.py`: OCR 수업명을 ON STUDIO 수업 DB와 `RapidFuzz`로 매칭합니다.
- `ai_review_quality_check.py`: Gemini Vision API를 사용할 수 있으면 전건 구조화 검수를 시도하고, API 제한 시 규칙 기반 fallback 결과를 Pydantic으로 검증합니다.
- `match_reviewers_private.py`: private 예약자 데이터와 리뷰 작성자를 내부 후보 매칭합니다. 이 출력은 외부 공유 금지입니다.
- `build_analysis_tables.py`: public 리뷰표, 수업별/요가원별 Hype metrics, 1차 분석 리포트, core 분석 계보 생성본을 만듭니다. 통합 계보 문서 `methodology_and_data_lineage.md`는 Google Drive/Notion/Viral/정산 내용이 합쳐진 수동 관리 문서이므로 덮어쓰지 않습니다.
- `geocode_studio_locations_arcgis.py`: ON STUDIO 수업 설명에서 정리한 장소 주소를 ArcGIS World Geocoding Service로 좌표화합니다.
- `build_gis_tables.py`: 좌표와 Hype metrics를 결합해 GIS CSV, GeoJSON, HTML 지도를 생성합니다.
- `build_gis_distance_matrix.py`: active 행사 장소의 위치 노드와 장소 간 거리/예상 도보시간 matrix를 생성합니다.
- `build_gis_schedule_flows.py`: 수업 시간표와 거리 matrix를 결합해 비식별 참여자 동선 후보와 public 이동 가능성 집계를 생성합니다.
- `build_gis_deep_report.py`: GIS 심화 리포트, 이동 가능성 지도, 시간-공간 큐브 HTML을 생성합니다.
- `build_public_duckdb.py`: public CSV를 DuckDB 파일로 묶어 쿼리할 수 있게 만듭니다.
- `collect_naver_blog_mentions.py`: 네이버 검색 API로 연희요가위크 관련 블로그 검색 결과를 수집해 `data/raw/external_web/naver_blog_mentions_raw.csv`와 수집 리포트를 생성합니다.
- `collect_youtube_mentions.py`: YouTube Data API v3로 연희요가위크 관련 영상 검색 결과와 기본 조회/반응 메타데이터를 수집해 `data/raw/external_web/youtube_mentions_raw.csv`와 수집 리포트를 생성합니다.
- `build_viral_mentions_review_queue.py`: 네이버와 유튜브 raw 수집본을 중복 링크 기준으로 합쳐 내부 검수용 `data/interim/external_web/viral_mentions_review_queue.csv`를 생성합니다.
- `filter_yeonhui_yoga_week_mentions.py`: 통합 검수 큐에서 제목/요약/설명에 `연희요가위크`가 직접 확인되고 2026-02-01 이후 게시된 후보만 1차 confirmed로 분리하고, public 익명화 표와 요약표를 생성합니다.
- `collect_naver_blog_bodies.py`: confirmed 네이버 블로그 링크의 공개 본문을 수집해 `data/raw/external_web/naver_blog_bodies_raw.csv`와 본문 수집 리포트를 생성합니다.
- `build_naver_blog_body_features.py`: 수집된 네이버 블로그 본문에서 행사명 확인, 노이즈 위험, 본문 테마, 요가원/장소 언급 요약을 생성합니다.
- `build_naver_blog_body_deep_features.py`: 본문 기반 관련성 신뢰도, 후기 깊이, 감정 강도, 혼합글 위험도, 해석용 게시물 유형을 생성합니다.
- `build_viral_metrics.py`: confirmed 외부 언급을 Hype와 합치지 않고 별도 Viral 지표로 요약해 overall/platform/studio metrics와 분석 리포트를 생성합니다.
- `archive_google_drive_shared_files.py`: 2026년 이후 연희요가위크 관련 Google Drive 공유자료를 raw archive로 보존하는 별도 보안 작업용 스크립트입니다. 실행하려면 `.secrets/google_drive_authorized_account.txt`와 `--account` 값이 정확히 일치해야 하며, 루트 공유 폴더의 owner/sharing user가 `.secrets/google_drive_source_account.txt`와 맞아야 합니다.
- `summarize_google_drive_partial_archive.py`: 중간 중지된 Google Drive 아카이브의 부분 수집 상태를 점검하기 위해 만든 보조 스크립트입니다. 최종 전량 아카이브 완료 후에는 `archive_google_drive_shared_files.py`의 manifest/report를 우선합니다.
- `extract_google_drive_program_capacity_reference.py`: Google Drive 공유 프로그램표 사본에서 날짜, 시간, 장소, 수업명, 정원 후보를 추출해 public 분석 후보 CSV를 만듭니다.
- `parse_onstudio_calendar_capacity.py`: ON STUDIO 캘린더 화면 복사본에서 수업별 `예약수|정원`을 추출해 public 정원/점유율 참고표를 만듭니다.
- `compare_capacity_references.py`: ON STUDIO 캘린더 정원표와 Google Drive 기획 정원표를 날짜/시각/수업명 기준으로 대조하고 검토 후보를 표시합니다.
- `build_drive_archive_analysis.py`: Google Drive 전량 아카이브 manifest를 프로그램/스폰서/F&B/디자인/운영 분석 축으로 요약한 public 파생표와 리포트를 만듭니다.
- `build_capacity_hype_analysis.py`: ON STUDIO 캘린더 정원/채움률과 Hype metrics를 결합해 수업별/요가원별 운영 반응 프로필을 만듭니다.
- `build_fnb_sponsor_gis_analysis.py`: Google Drive F&B 협업표와 스폰서 asset 폴더를 public 파생표로 만들고, F&B 주소를 지오코딩해 행사 장소와의 거리 후보를 계산합니다.
- `archive_notion_shared_pages.py`: 사용자가 제공한 공유용 Notion URL을 읽어 raw/private 원문 보관본과 public 커뮤니케이션 요약표, 검토 리포트를 생성합니다. 원문 블록 inventory는 `data/raw/notion_shared/` 아래에만 보관하고 GitHub 공유 대상에서 제외합니다.
- `build_integrated_stakeholder_report.py`: 최종 public 분석표를 다시 읽어 9가지 독자 페르소나를 함께 고려한 통합 이해관계자 보고서를 재생성합니다.
- `prepare_public_repository.py`: private 작업 레포를 public으로 전환하지 않고, 외부 공유 가능한 파일만 `..\YH-yogaweek` 폴더로 복사해 별도 public 레포 패키지를 만듭니다. 실행 후 `PUBLIC_RELEASE_AUDIT.md`에서 금지 패턴 0건인지 확인해야 합니다.

## API key 파일

- Google Vision OCR용 키: `.secrets/google-api.txt`
- Gemini 검수용 키: `.secrets/gemini-api.txt`
- 네이버 블로그 검색용 키: `.secrets/naver-client-id.txt`, `.secrets/naver-client-secret.txt`
- YouTube 검색용 키: `.secrets/youtube-api-key.txt`
- Google Drive 아카이브 승인 계정: `.secrets/google_drive_authorized_account.txt`
- Google Drive 공유 원천 계정: `.secrets/google_drive_source_account.txt`

Google Cloud 콘솔에서 Gemini API 제한이 다른 API와 함께 선택되지 않는 경우가 있으므로, Vision OCR용 키와 Gemini용 키를 분리해서 쓰는 방식을 권장합니다.
