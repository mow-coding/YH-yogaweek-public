# 방법론 및 데이터 계보

작성일: 2026-05-16

현재 프로젝트 전체 현황판은 `docs/project-current-status.md`에 따로 정리되어 있다.

## 1. 처리 원칙
모든 데이터는 `원천자료 수집 -> 전처리 -> OCR -> 구조화 -> 비식별/내부 매칭 -> 분석 -> 리포트`
순서로 처리했다. public 산출물에는 전화번호, 실명, API key, 원본 스크린샷을 포함하지 않는다.

## 2. 원천자료와 접근 권한
| 자료 | 위치 | 접근/권한 | 사용 범위 |
|---|---|---|---|
| ON STUDIO 예약/취소/수업/강사 | `data/raw/onstudio/` | 축제 참여 요가원별 ON STUDIO 계정 접근 가능 | 예약/취소/수업 분석 |
| 오붓 리뷰 스크린샷 | `data/raw/obud_reviews/screenshots/` | 오붓 리뷰 화면이 마우스 드래그/텍스트 복사를 허용하지 않아 사용자가 최신순으로 직접 화면 캡처. 원본은 private/raw | OCR 및 리뷰 분석 |
| Google Vision OCR 텍스트 | `data/raw/obud_reviews/ocr_text/` | OCR API key는 로컬 파일/환경변수, 결과 원문은 raw | OCR 구조화 |
| Gemini Vision 검수 결과 | `data/processed/obud_reviews/private/obud_reviews_ai_checked_private.csv` | Gemini API key는 로컬 전용. 원본 이미지와 OCR 텍스트를 함께 사용해 JSON 구조화 검수 | 리뷰 구조화 품질 검수 |
| 티켓 가격표 | `references/obud-ticket-pricing.md` | 사용자 제공 이미지 기반 기록 | 가격 추정 기준 |
| 오붓 정산 기준 | `references/obud-settlement-rules.md`, `data/raw/settlement/obud/` | 빅블루 요가 유동환 대표 전달 카카오톡 메시지와 오붓 화면 스크린샷 기반 전사. 2026-05-16 공개 오붓 사이트/FAQ/오붓패스/입점문의/sitemap 확인 결과 공개 정산표는 미확인 | 1회권/패스권 정산 추정 |
| 요가원/행사 장소 주소 | `data/external/studio_locations_public.csv` | ON STUDIO 수업 설명과 공개 웹 검색으로 수집. 최종 예약/시간표에 남은 active 장소만 GIS seed로 사용하며, 초기 기획안에만 남은 궁동산 행은 active GIS에서 제외 | GIS 1차 분석 |
| 수업별 실제 장소 증거 | `data/processed/analysis/public/class_location_evidence_public.csv` | 수업 설명의 `📍 장소`, `집합 장소`, `장소:` 문구를 파싱해 `organizer_studio_key`와 `actual_location_key`를 분리 | GIS 동선 분석 |
| Google Drive 공유 프로그램/운영 문서 | `data/raw/google_drive_shared/rightnow_yogi/files/`, `data/raw/google_drive_shared/rightnow_yogi/full_archive/` | `bigblue.yoga@gmail.com` 계정에서 `rightnow.yogi@gmail.com`으로부터 공유받은 2026년 이후 연희 요가 축제 관련 자료의 로컬 사본. raw는 GitHub 공유 제외 | 수업 정원, 운영 문구, F&B/스폰서/기획 맥락 |
| 공유용 Notion 커뮤니케이션 문서 | `data/raw/notion_shared/` | 사용자가 제공한 공유용 Notion URL 2건을 읽기 전용으로 수집. 원문 JSON/텍스트와 블록별 원문 inventory는 raw/private로만 보관하고 GitHub 공유 제외 | 행사 기획 의도, 대외 메시지, 크루 운영 철학, 참여자 경험 설계 맥락 |
| Google Drive 수업 정원 후보표 | `data/processed/analysis/public/google_drive_program_capacity_reference.csv` | `program_obud_delivery.xlsx`에서 날짜/시간/장소/수업명/정원 후보를 추출한 public 파생표 | 정원 대비 예약률/운영 분석 후보 |
| ON STUDIO 캘린더 정원/예약현황 | `data/raw/onstudio/calendar_capacity/onstudio_calendar_capacity_2026_yeonhui_yoga_week_2026-05-16.txt` | 사용자가 ON STUDIO 캘린더 화면에서 직접 복사한 원본. raw는 GitHub 공유 제외 | 실제 운영 기준 정원/점유율 분석 |
| ON STUDIO 캘린더 public 파생표 | `data/processed/analysis/public/onstudio_calendar_capacity_reference.csv` | 캘린더 원본에서 수업별 `예약수&#124;정원`을 추출한 public 파생표 | 정원 대비 채움률/운영 포화도 분석 |
| 네이버 블로그 검색 결과 | `data/raw/external_web/naver_blog_mentions_raw.csv` | 네이버 검색 API. raw는 GitHub 공유 제외 | 외부 Viral 후보 수집 |
| 네이버 블로그 본문 | `data/raw/external_web/naver_blog_bodies_raw.csv` | confirmed 네이버 블로그 공개 페이지. 로그인/비공개 접근 없음. raw는 GitHub 공유 제외 | 본문 기반 노이즈 검수와 질적 요약 |
| 유튜브 검색 결과 | `data/raw/external_web/youtube_mentions_raw.csv` | YouTube Data API v3. raw는 GitHub 공유 제외 | 외부 Viral 후보 수집 |

## 3. 실행 스크립트 계보
| 단계 | 스크립트 | 입력 | 출력 | 현재 상태 |
|---|---|---|---|---|
| ON STUDIO 전처리 | `scripts/preprocess_onstudio.py` | `data/raw/onstudio/` | processed ON STUDIO CSV | 완료 |
| 예약/취소 비식별 | `scripts/deidentify_reservation_cancel.py` | private 예약/취소 CSV | public 비식별 CSV | 완료 |
| public DuckDB 생성 | `scripts/build_public_duckdb.py` | public CSV | `data/database/yogaweek_public.duckdb` | 완료/재실행 가능 |
| Google Vision OCR | `scripts/ocr_obud_reviews_google_vision.py` | 리뷰 스크린샷 | OCR txt/json, manifest | 완료 |
| OCR 통합표 | `scripts/build_obud_google_ocr_raw_table.py` | OCR txt | `data/interim/obud_reviews/google_vision_ocr_raw.csv` | 완료 |
| 리뷰 필드 파싱 | `scripts/parse_obud_reviews.py` | OCR raw CSV | `data/processed/obud_reviews/private/obud_reviews_extracted_private.csv` | 완료 |
| 수업명 매칭 | `scripts/match_review_classes.py` | 리뷰 파싱표, ON STUDIO 수업명 | 같은 private 리뷰표에 매칭 컬럼 추가 | 완료 |
| AI/규칙 검수 | `scripts/ai_review_quality_check.py` | 수업명 매칭 private 리뷰표 | `data/processed/obud_reviews/private/obud_reviews_ai_checked_private.csv` | 완료 |
| 리뷰 작성자 내부 매칭 | `scripts/match_reviewers_private.py` | 리뷰 private, 예약 private | `data/processed/obud_reviews/private/review_reviewer_match_private.csv` | 완료 |
| 분석 테이블/리포트 | `scripts/build_analysis_tables.py` | 예약/취소/review/가격 | public 리뷰, Hype metrics, 리포트 | 완료 |
| 오붓 정산 기준/추정 | `scripts/build_obud_settlement_analysis.py` | 예약/취소 공개용 CSV, 오붓 정산표 전사값, 유동환 대표의 `소비자 기준`/`이용완료된 기준` 후속 확인 | 정산 규칙 CSV, 패스 정산표, 수업/요가원-월별 정산 추정치, 패스권 회차 추정 요약 | 완료/최종 정산서 확인 필요 |
| GIS 좌표화 | `scripts/geocode_studio_locations_arcgis.py` | `data/external/studio_locations_public.csv` | 좌표가 채워진 장소 테이블, 지오코딩 리포트 | 완료 |
| GIS 분석 | `scripts/build_gis_tables.py` | 장소 좌표, Hype metrics | GIS CSV, GeoJSON, HTML 지도, GIS 리포트 | 완료 |
| GIS 거리 행렬 | `scripts/build_gis_distance_matrix.py` | 행사 위치 카탈로그 | location nodes, distance matrix | 완료/재실행 가능 |
| GIS 시간표/동선 | `scripts/build_gis_schedule_flows.py` | 예약/취소, 거리 행렬, Hype GIS, 수업별 장소 증거 | class location evidence, class schedule, transition feasibility | 완료/재실행 가능 |
| GIS 심화 리포트 | `scripts/build_gis_deep_report.py` | GIS 심화 public tables | 심화 리포트, 이동 지도, 시간-공간 큐브 | 완료/재실행 가능 |
| Google Drive 정원 후보 추출 | `scripts/extract_google_drive_program_capacity_reference.py` | `program_obud_delivery.xlsx` | `google_drive_program_capacity_reference.csv` | 완료/재실행 가능 |
| ON STUDIO 캘린더 정원 파싱 | `scripts/parse_onstudio_calendar_capacity.py` | ON STUDIO 캘린더 raw txt | `onstudio_calendar_capacity_reference.csv` | 완료/재실행 가능 |
| 정원표 대조 | `scripts/compare_capacity_references.py` | Google Drive 정원표, ON STUDIO 캘린더 정원표 | `capacity_reference_comparison.csv`, 대조 리포트 | 완료/재실행 가능 |
| Google Drive 전량 아카이브 | `scripts/archive_google_drive_shared_files.py` | `bigblue.yoga@gmail.com` 접근 계정, `rightnow.yogi@gmail.com` 공유 원천, Drive 공유 폴더 | raw full archive, 로컬 manifest/report | 완료/재실행 가능. raw/manifest는 GitHub 공유 제외 |
| Google Drive 아카이브 분석 | `scripts/build_drive_archive_analysis.py` | full archive manifest | Drive 영역 요약, asset type 요약, 분석 기회 matrix | 완료/재실행 가능 |
| 정원+Hype 결합 | `scripts/build_capacity_hype_analysis.py` | ON STUDIO 캘린더 정원표, Hype metrics | 수업별/요가원별 정원+Hype metrics, 리포트 | 완료/재실행 가능 |
| F&B/스폰서 GIS 분석 | `scripts/build_fnb_sponsor_gis_analysis.py` | F&B 협업표, Drive manifest, location nodes | F&B public/GIS 표, F&B GeoJSON, 스폰서 asset inventory, 리포트 | 완료/재실행 가능 |
| Notion 공유 커뮤니케이션 자료 요약 | `scripts/archive_notion_shared_pages.py` | 사용자가 제공한 공유용 Notion URL 2건 | raw/private 원문 보관본, public 페이지 요약, public 테마 요약, 커뮤니케이션 검토 리포트 | 완료/재실행 가능 |
| 네이버 블로그 수집 | `scripts/collect_naver_blog_mentions.py` | 네이버 검색 API, 확장 검색어 | 블로그 검색 raw CSV, 수집 리포트 | 완료/재실행 가능 |
| 유튜브 수집 | `scripts/collect_youtube_mentions.py` | YouTube Data API v3, core 검색어 | 유튜브 검색 raw CSV, 수집 리포트 | 완료/재실행 가능 |
| Viral 검수 큐 | `scripts/build_viral_mentions_review_queue.py` | 네이버/유튜브 raw CSV | 내부 검수 큐 CSV, 리포트 | 완료/재실행 가능 |
| 연희요가위크 언급 필터 | `scripts/filter_yeonhui_yoga_week_mentions.py` | Viral 검수 큐 | confirmed internal/public 표, 플랫폼/요가원 요약 | 완료/재실행 가능 |
| 네이버 블로그 본문 수집 | `scripts/collect_naver_blog_bodies.py` | confirmed 네이버 블로그 링크 | 공개 본문 raw CSV, 본문 수집 리포트 | 완료/재실행 가능 |
| 네이버 블로그 본문 특징 | `scripts/build_naver_blog_body_features.py` | 네이버 블로그 본문 raw | 내부 본문 특징, public 테마/요가원 요약 | 완료/재실행 가능 |
| 네이버 블로그 본문 심층 특징 | `scripts/build_naver_blog_body_deep_features.py` | 네이버 블로그 본문 raw, 기본 본문 특징 | 관련성 신뢰도, 후기 깊이, 감정 강도, 혼합글 위험도, 게시물 유형 요약 | 완료/재실행 가능 |
| Viral 지표 | `scripts/build_viral_metrics.py` | public confirmed Viral 표 | 별도 Viral metrics, 분석 리포트 | 완료/재실행 가능 |

## 4. 행 수 검증
- ON STUDIO 수업: 125건
- ON STUDIO 예약: 1611건
- ON STUDIO 취소: 1048건
- 오붓 리뷰 public: 96건
- 수업별 Hype metrics: 83행
- 요가원별 Hype metrics: 12행
- GIS 위치 seed: 16행
- GIS 위치 카탈로그: 13행
- GIS 위치 카탈로그 중 수동 확인 필요: 0행
- GIS 장소 간 거리 matrix: 169행
- GIS 수업별 실제 장소 증거: 83행
- GIS 수업 시간표: 261행
- GIS public same-day 이동 가능성: 167행
- 네이버 블로그 검색 raw: 2415행, 고유 링크 1075개
- 유튜브 검색 raw: 85행, 고유 영상 68개, 고유 채널 32개
- Viral 통합 후보 mention: 1143행
- `연희요가위크` confirmed 외부 언급: 60행
- Viral platform metrics: 2행
- Viral studio/place metrics: 10행
- Viral unmatched public mentions: 17행
- confirmed 네이버 블로그 본문 수집: 58행
- 본문 내 `연희요가위크` 직접 확인: 56행
- 본문 기준 노이즈 위험 후보: 2행
- 네이버 블로그 본문 테마 요약: 6행
- 네이버 블로그 본문 요가원/장소 요약: 13행
- 본문 기준 strong/basic confirmed 블로그: 56행
- 본문 기준 수동 확인 권장 블로그: 5행
- 본문 기준 high-depth 후기/맥락 글: 30행
- 본문 기준 positive/very positive 톤 글: 47행
- 네이버 블로그 본문 게시물 유형 요약: 7행
- 네이버 블로그 본문 품질 요약: 20행
- Google Drive 핵심 로컬 원본 사본: 10개
- Google Drive 전량 아카이브 manifest: 490행
- Google Drive 전량 아카이브 로컬 원본 사본: 384개
- Google Drive 전량 아카이브 2026 이전 제외: 24개
- Google Drive 전량 아카이브 실패: 0건
- Google Drive 아카이브 영역 요약: 14행
- Google Drive 아카이브 asset type 요약: 26행
- Google Drive 추가 분석 기회 matrix: 5행
- Google Drive 수업 정원 후보표: 248행, 정원 자동 추출 필요 검수 5행
- ON STUDIO 캘린더 정원/예약현황표: 263행, 날짜 범위 2026-04-20~2026-05-09
- 정원표 대조 결과: 일치 132행, 정원 불일치 58행, 낮은 신뢰도 후보 41행, 같은 시각 Google Drive 후보 없음 31행, Drive 정원 누락 1행
- 정원+Hype 수업별 결합표: 86행
- 정원+Hype 요가원별 결합표: 12행
- F&B 협업 브랜드 public/GIS 후보: 16행
- F&B 좌표 확보: 16행
- 행사 장소 300m 이내 F&B 후보: 14행
- 스폰서 asset inventory: 15행
- Notion 공유 페이지 요약: 2행
- Notion 공유 커뮤니케이션 테마 요약: 13행
- Notion raw/private 블록 inventory: 180행

## 5. 비식별 정책
- public 예약/취소 표의 이름은 `participant_####`, 전화번호는 `PHONE_MASKED`로 대체했다.
- public 리뷰 표는 `masked_reviewer`를 직접 내보내지 않고 `reviewer_####` 형태의 내부 public ID만 사용한다.
- private 작성자 매칭표에는 실명/전화번호 후보가 포함될 수 있으므로 외부 공유 대상에서 제외한다.
- OCR API key는 `.secrets/google-api.txt`, Gemini API key는 `.secrets/gemini-api.txt`에 로컬 전용으로 보관하며, `.gitignore`에서 제외한다.
- 네이버/유튜브 raw와 interim 검수 큐에는 공개 출처명, 공개 출처 ID, 원문 URL이 남을 수 있으므로 GitHub 공유 대상에서 제외한다.
- 네이버 블로그 본문 raw는 개인 경험 서술이 포함될 수 있으므로 GitHub 공유 대상에서 제외한다.
- 네이버 블로그 본문 심층 public feature는 원문 본문과 URL을 제외하고, mention ID와 점수/라벨/요약 feature만 포함한다.
- Viral public 표는 출처명, 출처 ID, 프로필 URL, 정확한 원문 URL을 제거하고 `external_source_####` 익명 ID만 남긴다.
- Google Drive raw 사본에는 쿠폰 코드, 신청자 정보, 운영 세부사항이 포함될 수 있으므로 GitHub 공유 대상에서 제외한다. public 분석에는 민감정보가 제거된 파생표만 사용한다.
- Google Drive full archive manifest는 source id와 원본 경로가 있으므로 로컬 기록용으로 두고 GitHub 공유 대상에서 제외한다.
- ON STUDIO 캘린더 raw 사본은 운영 화면 복사본이므로 GitHub 공유 대상에서 제외한다. public 파생표에는 실명/전화번호 없이 수업별 정원, 예약수, 채움률만 포함한다.
- Notion 공유 문서 원문에는 운영 세부사항과 내부 커뮤니케이션 문구가 포함될 수 있으므로 원문 JSON, 추출 텍스트, 블록별 inventory는 `data/raw/notion_shared/`에만 보관하고 GitHub 공유 대상에서 제외한다. public 산출물은 페이지 단위 요약과 테마별 집계만 사용한다.

## 6. AI 검수 상태
- 검수 모드별 건수:
```text
ai_validation_mode
gemini_vision_structured_output    96
```

- API 상태별 건수:
```text
ai_provider_status
available    96
```

- Gemini 모델별 건수:
```text
ai_model
gemini-3.1-flash-lite    67
gemini-2.5-flash         29
```

모델이 둘로 나뉜 이유는 검수 중 `gemini-2.5-flash` 호출에서 쿼터 제한이 발생했기 때문이다.
이미 성공한 29건은 보존했고, 남은 67건은 `gemini-3.1-flash-lite`로 재시도해 완료했다.
두 모델 모두 같은 Pydantic 스키마로 검증했고, 최종 public 분석표는 96건 전부 Gemini Vision 구조화 검수가 완료된 표를 기준으로 재생성했다.

## 7. 분석 지표 정의
- 순예약 수: `reservation_count - cancellation_count`
- 취소율: `cancellation_count / (reservation_count + cancellation_count)`
- 리뷰 작성률: `review_count / reservation_count`
- 예약 Hype: 순예약 수의 percentile 점수
- 리뷰 Hype: 리뷰 수 percentile과 리뷰 작성률 percentile의 평균
- 만족 Hype: 평균 전체 별점 / 5 * 100
- 재방문 Hype: 평균 방문회차 percentile
- 결제 Hype: 참가자 결제 반응 추정 지표의 percentile
- 정산 추정액: 오붓 정산 스크린샷 기준으로 1회권은 5% 수수료 차감. 패스권은 후속 확인에 따라 소비자 개인의 월간 이용완료 횟수 구간과 25,000원 기본 수업 단가를 적용한 추정액. 현재 자료는 오붓 전체 월간 이용내역이 아니라 연희 요가 위크 ON STUDIO 관측자료이므로 최종 회계 증빙에는 오붓 최종 정산서 또는 서면 확인 필요
- 운영 안정성: `(1 - cancellation_rate) * 100`

Viral 지표는 Hype와 별도 축으로 둔다.

- Hype: 예약/취소/리뷰/만족/재방문/결제 등 행사 내부 참여와 경험 신호
- Viral: 네이버 블로그/유튜브 같은 외부 공개 웹 확산 신호
- `viral_signal_score`: 직접 확인된 외부 언급 수, 익명 출처 수, 유튜브 조회수 추정 신호, 플랫폼 다양성을 조합한 설명용 점수
- Viral 지표는 기존 Hype 점수에 합산하지 않는다.

## 8. 재현 명령
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
python scripts\build_drive_archive_analysis.py
python scripts\build_capacity_hype_analysis.py
python scripts\build_fnb_sponsor_gis_analysis.py
python scripts\archive_notion_shared_pages.py
python scripts\build_public_duckdb.py
```

## 9. GIS 방법론 참고 자료
- GIS 1차 분석은 `ON STUDIO 수업 설명 주소 -> ArcGIS 지오코딩 -> 좌표/Hype 결합 -> Folium 지도/GeoJSON` 순서로 만들었다.
- 상세 참고 자료와 후속 분석 후보는 `docs/gis-method-references.md`에 기록했다.
- GIS 심화 분석은 `장소 노드 -> OSMnx 보행 거리 matrix -> 수업 시간표 -> same-day 이동 가능성 -> 이동 지도/시간-공간 큐브` 순서로 만들었다.
- 개인별 itinerary와 transition은 private 산출물로만 보관하고, public 리포트에는 장소/수업 쌍 단위 집계만 사용한다.
