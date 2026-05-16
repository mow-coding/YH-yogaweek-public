# rightnow.yogi Google Drive 수집 리포트

작성일: 2026-05-16

## 수집 목적

2026 연희 요가 위크 준비 과정에서 `rightnow.yogi` Google 계정으로 공유된 Google Drive 자료를 프로젝트 원천자료 아카이브에 보존했다. 목적은 예약/리뷰/Hype/GIS 분석만으로는 부족한 수업 정원, 운영 문구, 협업 구조, F&B 쿠폰, 스폰서/기획 맥락을 나중에 검증할 수 있게 만드는 것이다.

원본 Google Drive 파일은 수정하거나 삭제하지 않았다. 로컬 프로젝트 안에는 사본만 저장했다.

## 로컬 저장 위치

원본 사본은 아래 폴더에 있다.

```text
data/raw/google_drive_shared/rightnow_yogi/files/
```

이 폴더는 원천자료 보관용이며 `.gitignore` 규칙상 GitHub 공유 대상에서 제외된다.

## 수집한 핵심 파일

| 로컬 파일 | 원본 제목 | 용도 | 공유 등급 |
|---|---|---|---|
| `program_obud_delivery.xlsx` | 연희축제 프로그램 (오붓 전달) | 수업 일정, 장소, 정원 기준표 | public 파생 가능 |
| `program_working_sheet_private.xlsx` | 연희축제 프로그램 | 준비 과정용 운영 시트, 일부 민감정보 가능 | private |
| `special_class_planning.xlsx` | 스페셜 클래스 진행 | 야외/스페셜 클래스 기획 맥락 | 내부 검토 |
| `event_basic_text_and_operations.docx` | 연희요가위크 기본 텍스트 및 전달 부탁 사항 | 운영 문구, 안내 문구, 협업 요청 맥락 | 내부 검토 |
| `obud_open_final_revision_request.docx` | 3월 30일- 오붓 오픈 정말 마지막 부탁드려요 | 오붓 오픈 전 최종 수정 요청 | 내부 검토 |
| `early_proposal_feb_yoga_meditation.pdf` | 2월_연희요가위크_요가명상원(저용량).pdf | 초기 제안서, 행사 콘셉트, 이해관계자/협업 구조 | 내부 검토 |
| `fnb_partner_brands.xlsx` | 연희요가축제 함께하는 F&B 브랜드 | F&B 쿠폰 협업 브랜드, 주소, 혜택 조건 | public 파생 가능 |
| `coupon_yeonhui_week_obud_private.xlsx` | coupon_yeonhui_week_obud.xlsx | 쿠폰/초대권 관리 자료 | private |
| `recovery_track_knitlife_seejak_private.xlsx` | [니트생활자X시이작]연희요가위크_-리커버리트랙 | 별도 리커버리 트랙 신청/참여 관련 자료 | private |
| `interview_questionnaire_shared.docx` | 연희요가축제_인터뷰_공유2 | 요가원/강사 인터뷰 질문지 | 내부 검토 |

## 바로 얻은 추가 정보

- 수업별 정원 정보는 `program_obud_delivery.xlsx` 안에 들어 있다.
- 이 정원표는 단순 예약 수가 아니라 `예약 수 / 정원` 기준의 충원율, 과소/과밀 운영, 내년 공간 배치 개선 분석에 사용할 수 있다.
- F&B 협업 자료에는 쿠폰 사용 구조와 참여 브랜드 주소가 있어, GIS 축에서 요가원 이동 동선과 지역 소비 동선을 함께 보는 확장 분석에 쓸 수 있다.
- 초기 제안서에는 어반플레이, 오붓, 지역 브랜드 협업 구조와 행사 콘셉트가 들어 있어 외부 파트너 제출 리포트의 배경 설명 근거로 사용할 수 있다.

## 파생 산출물

`scripts/extract_google_drive_program_capacity_reference.py`로 `program_obud_delivery.xlsx`에서 수업 정원 후보표를 추출한다.

출력:

```text
data/processed/analysis/public/google_drive_program_capacity_reference.csv
```

현재 추출 결과는 248행이며, 정원이 자동 추출되지 않은 행은 5행이다. 이 표는 Google Drive 원본에서 온 정원 후보이므로, ON STUDIO 수업 DB와 매칭한 뒤 최종 분석에 반영한다.

public DuckDB에는 `google_drive_program_capacity_reference` 테이블명으로 함께 적재했다.

## 주의사항

- `coupon_yeonhui_week_obud_private.xlsx`, `program_working_sheet_private.xlsx`, `recovery_track_knitlife_seejak_private.xlsx`는 실명, 연락처, 신청 동기, 쿠폰 코드 등 민감정보가 포함될 수 있으므로 외부 공유 금지다.
- public 리포트에는 원본 Google Drive 문서 전문을 그대로 싣지 않고, 필요한 사실과 집계만 요약한다.
- 메신저/개인 연락 자료는 아직 수집하지 않았고, 당사자 동의 없이는 분석하지 않는다.

## 남은 원자료 복사 후보

이번 배치에서는 분석에 바로 필요한 문서/스프레드시트/PDF를 우선 복사했다.
Google Drive 안에는 스폰서 카드뉴스, F&B 브랜드별 로고/메뉴 사진, 디자인 소스 이미지 폴더도 남아 있다.
이 파일들은 정량 분석보다는 발표자료, 아카이브, 브랜드 협업 회고에 더 유용하므로 다음 원자료 복사 배치에서 별도로 전량 보관한다.
