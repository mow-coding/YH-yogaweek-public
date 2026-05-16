# 2026 연희 요가 위크 프로젝트 현재 현황판

작성일: 2026-05-16

이 문서는 지금 프로젝트 폴더에 무엇이 들어 있고, 어디까지 끝났고, 다음에 무엇을 하면 되는지 한눈에 보기 위한 안내문이다.

초보 바이브코더 관점에서 말하면, 이 파일은 프로젝트의 `메인 지도`다. 자세한 근거와 실행 로그는 각 리포트에 있고, 여기서는 전체 흐름만 잡는다.

## 1. 한 줄 요약

현재 프로젝트는 `ON STUDIO 예약/취소`, `오붓 리뷰 OCR`, `Gemini 리뷰 검수`, `Hype 지표`, `GIS 분석`, `네이버/유튜브 외부 확산(Viral) 분석`, `Google Drive 기획자료 전량 아카이브`, `ON STUDIO 캘린더 정원/예약현황`, `공유용 Notion 커뮤니케이션 자료 요약`까지 1차 데이터 파이프라인이 대부분 구축된 상태다.

현재 핵심 분석 축은 `Hype`, `GIS`, `외부 확산(Viral)`, `정원/채움률`, `Google Drive 기획자료`, `Notion 커뮤니케이션`, `오붓 정산 추정치`까지 1차 통합 보고서에 반영된 상태다. 다음 작업은 사람이 읽는 최종 문장 검토, PDF/DOCX 변환, 기관/파트너별 커버레터 작성이다.

## 1-1. 책임과 담당

| 역할 | 조직/소속 | 이름 | 계정 |
|---|---|---|---|
| 책임자/관리자 | 빅블루 요가 | 유동환 | `bigblue.yoga@gmail.com` |
| 분석담당자 | 빅블루 요가 | 김성균 | `mow.coding@gmail.com` |
| Google Drive 공유 원천 | rightnow.yogi | 공유 원천 계정 | `rightnow.yogi@gmail.com` |

Google Drive 자료는 `bigblue.yoga@gmail.com` 계정에서 `rightnow.yogi@gmail.com`으로부터 공유받은 2026년 이후 연희 요가 축제 관련 자료만 수집 대상으로 둔다.

## 2. 현재 분석 축

| 축 | 핵심 질문 | 현재 상태 | 주요 산출물 |
|---|---|---|---|
| ON STUDIO 예약/취소 | 누가 어떤 수업을 예약/취소했나 | 전처리/비식별 완료 | `data/processed/onstudio/public` |
| 오붓 리뷰 | 어떤 수업에 어떤 후기가 달렸나 | OCR/Gemini 검수/수업 매칭 완료 | `data/processed/obud_reviews/public/obud_reviews_deidentified.csv` |
| Hype | 수업/요가원별 내부 반응은 어떤가 | 수업/요가원 지표 생성 완료 | `class_hype_metrics.csv`, `studio_hype_metrics.csv` |
| GIS | 장소 구조와 동선 가능성은 어떤가 | 좌표/거리/동선/지도 생성 완료 | `gis_deep_analysis_report.md`, 지도 HTML |
| Viral | 외부 공개 웹에서 얼마나 퍼졌나 | 네이버/유튜브 수집과 본문 기반 검수 완료 | `yeonhui_yoga_week_viral_analysis_report.md` |
| Google Drive 기획자료 | 준비 과정의 기획 맥락과 정원 후보는 무엇인가 | 승인 계정/공유 원천 계정 검증 후 전량 아카이브 완료, 정원표 추출 완료 | `reports/google_drive`, `google_drive_program_capacity_reference.csv`, `docs/google-drive-source-collection-governance.md` |
| ON STUDIO 캘린더 정원 | 실제 운영 화면 기준 정원/채움률은 어떤가 | 263행 파싱, Google Drive 표와 대조 완료 | `onstudio_calendar_capacity_reference.csv`, `capacity_reference_comparison.csv` |
| Notion 커뮤니케이션 자료 | 공유용 기획/운영 문서가 보고서 메시지에 쓸만한가 | 공유 URL 2건 확인, raw/private 보관, public 요약 완료 | `notion_shared_page_summary_public.csv`, `notion_shared_communication_theme_summary_public.csv` |
| Public DuckDB | 여러 CSV를 SQL처럼 조회할 수 있나 | 생성 완료 | `data/database/yogaweek_public.duckdb` |
| 통합 이해관계자 보고서 | 9가지 독자에게 하나의 보고서로 메시지를 전달할 수 있나 | 최종 1차 분석 기반 재작성 완료 | `reports/stakeholders/yeonhui_yoga_week_integrated_stakeholder_report.md` |
| Public GitHub 레포 | 민감정보 제외 공개 패키지를 따로 둘 수 있나 | 별도 public 레포 생성/푸시 완료 | <https://github.com/mow-coding/YH-yogaweek-public> |

## 3. 현재 숫자 요약

| 항목 | 행/건수 |
|---|---:|
| ON STUDIO 수업 | 125건 |
| ON STUDIO 예약 | 1611건 |
| ON STUDIO 취소 | 1048건 |
| 오붓 리뷰 | 96건 |
| Gemini Vision 리뷰 구조화 검수 | 96건 |
| 수업별 Hype metrics | 83행 |
| 요가원별 Hype metrics | 12행 |
| GIS 위치 카탈로그 | 13행 |
| GIS 장소 간 거리 matrix | 169행 |
| GIS 수업별 장소 증거표 | 83행 |
| GIS 수업 시간표 | 261행 |
| GIS same-day 이동 가능성 public 집계 | 167행 |
| 네이버 블로그 검색 raw | 2415행 |
| 유튜브 검색 raw | 85행 |
| 연희요가위크 confirmed 외부 언급 | 60건 |
| confirmed 네이버 블로그 본문 수집 | 58건 |
| Google Drive 핵심 로컬 사본 | 10개 |
| Google Drive 전량 아카이브 manifest | 490행 |
| Google Drive 로컬 보존 원본 사본 | 384개 |
| Google Drive 폴더 기록 | 82행 |
| Google Drive 2026 이전 제외 | 24개 |
| Google Drive 아카이브 실패 | 0건 |
| Google Drive 아카이브 분석 축 요약 | 14행 |
| Google Drive 아카이브 asset type 요약 | 26행 |
| Google Drive 추가 분석 기회 matrix | 5행 |
| Google Drive 정원 후보표 | 248행 |
| ON STUDIO 캘린더 정원/예약현황표 | 263행 |
| 정원표 대조표 | 263행 |
| 정원+Hype 수업별 결합표 | 83행 |
| 정원+Hype 요가원별 결합표 | 12행 |
| F&B 협업 브랜드 public/GIS 후보 | 16행 |
| F&B 좌표 확보 | 16행 |
| 행사 장소 300m 이내 F&B 후보 | 14행 |
| 스폰서 asset inventory | 15행 |
| Notion 공유 페이지 요약 | 2행 |
| Notion 공유 커뮤니케이션 테마 요약 | 13행 |

## 4. 지금 가장 중요한 해석 원칙

Hype와 Viral은 합치지 않는다.

- Hype: 예약, 취소, 리뷰, 만족도, 재방문, 결제 같은 행사 내부 참여 신호다.
- Viral: 네이버 블로그, 유튜브 같은 외부 공개 웹 확산 신호다.

정원 정보는 ON STUDIO 캘린더를 우선 기준으로 본다.

- ON STUDIO 캘린더: 실제 플랫폼 운영 화면에서 복사한 `예약수|정원` 자료다.
- Google Drive 프로그램표: 기획/전달용 문서라서 정원 변경 전후가 섞였을 수 있다.
- 따라서 채움률과 운영 포화도는 ON STUDIO 캘린더를 기준으로 분석하고, Google Drive 표는 변경 이력 확인용으로 쓴다.

GIS 동선은 주관 요가원이 아니라 실제 수업 시작/종료 위치를 기준으로 본다.

- `organizer_studio_key`: 수업을 운영하거나 제목에 표시된 요가원/협업 주체다.
- `actual_location_key`: 참가자가 실제로 모이는 장소다. 동선 계산은 이 값을 기준으로 한다.
- 러닝, 트레킹, 옥상, 랜드마크, 커뮤니티허브 수업은 수업 설명의 `📍 장소` 또는 `집합 장소` 문구를 먼저 확인해 좌표를 붙인다.
- 초기 기획안에만 남은 `궁동산/궁둥산` 행은 active GIS 장소에서 제외했고, 최종 예약 수업인 `몸으로 하는 선셋 자애 명상`은 마인드플로우 주소로 처리한다.

public/private는 끝까지 분리한다.

- public: 외부 공유 후보. 실명, 전화번호, 원문 URL, API key, 원본 스크린샷이 빠져야 한다.
- private/raw: 내부 검증용. 원본, 연락처, 스크린샷, 공개 출처 URL, API 응답 등이 남을 수 있다.

## 5. 먼저 열어볼 문서

| 목적 | 파일 |
|---|---|
| 전체 프로젝트 현황 | `docs/project-current-status.md` |
| 작업 운영 표준 | `docs/project-operating-standards.md` |
| 정형 작업일지 | `docs/work-log.md` |
| 과거 작업 소급 감사 | `docs/retrospective-work-audit.md` |
| 전체 방법론과 데이터 계보 | `reports/analysis/methodology_and_data_lineage.md` |
| 1차 분석 리포트 | `reports/analysis/yeonhui_yoga_week_analysis_report.md` |
| GIS 심화 분석 | `reports/analysis/gis_deep_analysis_report.md` |
| Viral 분석 | `reports/external_web/yeonhui_yoga_week_viral_analysis_report.md` |
| 네이버 블로그 본문 심층 분석 | `reports/external_web/naver_blog_body_deep_feature_report.md` |
| ON STUDIO 캘린더 정원 대조 | `reports/onstudio/onstudio_calendar_capacity_comparison_report.md` |
| 정원+Hype 결합 분석 | `reports/analysis/capacity_hype_analysis_report.md` |
| Google Drive 핵심 수집 목록 | `reports/google_drive/rightnow_yogi_manifest.md` |
| Google Drive 전량 아카이브 리포트 | `reports/google_drive/rightnow_yogi_full_archive_report.md` |
| Google Drive 전량 아카이브 manifest | `reports/google_drive/rightnow_yogi_full_archive_manifest.csv` 로컬 전용, GitHub 공유 제외 |
| Google Drive 아카이브 분석 | `reports/google_drive/google_drive_archive_analysis_report.md` |
| F&B/스폰서 GIS 분석 | `reports/google_drive/fnb_sponsor_gis_analysis_report.md` |
| Google Drive 접근/수집 거버넌스 | `docs/google-drive-source-collection-governance.md` |
| Google Drive 분석 방법론 | `docs/google-drive-archive-analysis-methodology.md` |
| GitHub public 공개 전 감사 | `docs/public-github-release-audit.md` |
| 리뷰 OCR/Gemini 검수 | `reports/obud_reviews/obud_review_ai_quality_check_report.md` |
| 스크립트 실행 순서 | `scripts/README.md` |
| 데이터 접근/동의 원칙 | `docs/data-access-consent-and-collection-plan.md` |

## 6. 주요 public 데이터 위치

| 데이터 | 위치 |
|---|---|
| 수업별 Hype | `data/processed/analysis/public/class_hype_metrics.csv` |
| 요가원별 Hype | `data/processed/analysis/public/studio_hype_metrics.csv` |
| 오붓 리뷰 비식별 표 | `data/processed/obud_reviews/public/obud_reviews_deidentified.csv` |
| GIS 수업 시간표 | `data/processed/analysis/public/class_schedule_gis.csv` |
| GIS 이동 가능성 | `data/processed/analysis/public/transition_feasibility_public.csv` |
| 외부 확산 직접 확인 mention | `data/processed/analysis/public/yeonhui_yoga_week_viral_mentions_public.csv` |
| Viral 요가원/장소 지표 | `data/processed/analysis/public/yeonhui_yoga_week_viral_studio_metrics.csv` |
| 네이버 블로그 본문 심층 feature | `data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_deep_features_public.csv` |
| Google Drive 정원 후보 | `data/processed/analysis/public/google_drive_program_capacity_reference.csv` |
| ON STUDIO 캘린더 정원/예약현황 | `data/processed/analysis/public/onstudio_calendar_capacity_reference.csv` |
| 정원표 대조 | `data/processed/analysis/public/capacity_reference_comparison.csv` |
| 정원+Hype 수업별 결합 | `data/processed/analysis/public/class_capacity_hype_metrics.csv` |
| 정원+Hype 요가원별 결합 | `data/processed/analysis/public/studio_capacity_hype_metrics.csv` |
| Google Drive 아카이브 영역 요약 | `data/processed/analysis/public/google_drive_archive_area_summary.csv` |
| Google Drive 아카이브 asset type 요약 | `data/processed/analysis/public/google_drive_archive_asset_type_summary.csv` |
| Google Drive 추가 분석 기회 | `data/processed/analysis/public/google_drive_archive_analysis_opportunity_matrix.csv` |
| F&B 협업 브랜드/GIS 후보 | `data/processed/analysis/public/fnb_partner_brands_public.csv` |
| F&B 협업 브랜드 GeoJSON | `data/processed/analysis/public/fnb_partner_brands_gis.geojson` |
| 스폰서 asset inventory | `data/processed/analysis/public/sponsor_asset_inventory_public.csv` |

## 7. 현재 남은 작업

### 바로 다음에 하면 좋은 작업

1. 통합 보고서를 사람이 한 번 읽고 기관/파트너 제출용 톤을 최종 다듬는다.
2. F&B 좌표 1건 수동 검토 후보를 확인하고, 실제 영업 여부/주소 변경 여부를 확인한다.
3. F&B 직선거리 분석을 OSMnx 보행 네트워크 거리로 확장할지 결정한다.
4. public 산출물에 전화번호, API key, 원본 URL, 개인 식별자가 없는지 재검사한다.
5. GitHub 커밋/푸시 전에 `.gitignore`가 raw/private 파일을 막고 있는지 다시 확인한다.
6. public 레포를 갱신할 때에는 `prepare_public_repository.py`를 다시 실행한 뒤 public 레포에서 audit 결과 0건을 확인하고 커밋한다.

### 그 다음 단계 후보

1. 발표자료 또는 기관 제출용 PDF/DOCX를 만든다.
2. `Hype`, `Viral`, `GIS`, `Capacity`를 결합한 종합 요약표를 만든다.
3. 이해관계자별 요약본을 분리한다.
   - 요가원용: 수업 운영/정원/재방문/리뷰
   - 어반플레이용: 장소/동선/지역 확산/운영 개선
   - 오붓 플랫폼용: 예약/취소/패스/리뷰 전환
   - 참가자용: 행사 회고와 다음 회차 개선
4. SNS 자발 제출 이벤트를 설계한다.
5. 메신저/스폰서십 데이터는 동의와 민감정보 검토 후 별도 단계로 진행한다.

## 8. 재현 명령 위치

전체 실행 순서는 `scripts/README.md`와 `reports/analysis/methodology_and_data_lineage.md`에 기록되어 있다.

중요한 점은 모든 분석을 한 번에 외우려 하지 않는 것이다. 이 프로젝트는 이제 다음 구조로 보면 된다.

```text
raw 원본
  -> scripts 전처리
  -> processed/public 분석표
  -> reports 리포트
  -> DuckDB 조회
```

즉, 파일을 어디서 가져왔는지 보고 싶으면 `raw`와 수집 리포트를 보고, 어떻게 만들었는지 보고 싶으면 `scripts`와 방법론 문서를 보고, 결과만 보고 싶으면 `reports`와 `processed/public`을 보면 된다.
