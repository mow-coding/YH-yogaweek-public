# 데이터 접근 권한, 동의, 수집 계획

작성일: 2026-05-15

이 문서는 2026 연희 요가 위크 분석에서 다루는 데이터별 접근 권한과 공유 주의사항을 정리한다.

## 기본 원칙

- 접근 권한이 있는 데이터만 수집한다.
- 실명, 전화번호, 개인 연락, 원본 스크린샷, API key는 public 산출물에 넣지 않는다.
- 외부 공유용 데이터와 내부 검증용 private 데이터를 분리한다.
- 수집 경로, 수집일, 처리 스크립트, 입력/출력 파일을 리포트에 남긴다.

## 데이터별 접근 권한

| 데이터 | 위치 | 접근 권한 | 현재 상태 | 주의사항 |
|---|---|---|---|---|
| ON STUDIO 예약 | `data/raw/onstudio/reservations` | 행사 참여 요가원별 ON STUDIO 계정 | 수집/전처리 완료 | 실명/전화번호 포함. public은 비식별만 공유 |
| ON STUDIO 취소 | `data/raw/onstudio/cancellations` | 행사 참여 요가원별 ON STUDIO 계정 | 수집/전처리 완료 | 실명/전화번호 포함. public은 비식별만 공유 |
| ON STUDIO 수업 | `data/raw/onstudio/classes` | 행사 참여 요가원별 ON STUDIO 계정 | 수집/전처리 완료 | 수업명/설명은 분석 기준표로 사용 |
| ON STUDIO 강사 | `data/raw/onstudio/teachers` | 행사 참여 요가원별 ON STUDIO 계정 | 수집/전처리 완료 | 강사 연락처가 있어 private 처리 |
| ON STUDIO 캘린더 정원/예약현황 | `data/raw/onstudio/calendar_capacity` | 행사 참여 요가원별 ON STUDIO 계정 화면에서 사용자 직접 복사 | raw 보존/파생표 생성 완료 | 원본은 운영 화면 복사본이므로 raw/private. public에는 수업별 예약수, 정원, 채움률만 사용 |
| 오붓 리뷰 스크린샷 | `data/raw/obud_reviews/screenshots` | 오붓 플랫폼 리뷰 화면 접근 권한 | 96건 수집/OCR 완료 | 원본 이미지는 raw/private 성격. 외부 공유 제외 |
| 오붓 리뷰 OCR 텍스트 | `data/raw/obud_reviews/ocr_text` | Google Vision OCR 결과 | 96건 완료 | OCR 원문은 private/interim 성격 |
| 오붓 리뷰 public 표 | `data/processed/obud_reviews/public/obud_reviews_deidentified.csv` | 비식별 처리 후 공유 가능 후보 | 생성 완료 | 외부 공유 전 리뷰 본문 민감 표현 재검토 필요 |
| 구글 드라이브 공유 문서 | `data/raw/google_drive_shared/rightnow_yogi/files`, `data/raw/google_drive_shared/rightnow_yogi/full_archive` | `bigblue.yoga@gmail.com` 계정에서 `rightnow.yogi@gmail.com`으로부터 공유받은 2026년 이후 연희 요가 축제 관련 자료 | 핵심 문서 10개 로컬 사본 수집 완료. 전량 아카이브 384개 원본 사본 보존, 2026 이전 24개 제외, 실패 0건 | 원본 파일은 수정하지 않음. 쿠폰/신청/운영 시트는 private, 정원/F&B처럼 민감정보 제거 가능한 파생표만 public 후보. 세부 규칙은 `docs/google-drive-source-collection-governance.md` 참고 |
| 메신저/개인 연락 | `data/raw/messenger` 예정 | 각 대화 참여자 동의 필요 | 1차 분석 제외 | 반드시 사전 동의 필요 |
| 스폰서십 연락 | `data/raw/sponsorship` 예정 | 연락 당사자 동의 필요 | 1차 분석 제외 | 민감한 협상/금액/연락처 검토 필요 |
| SNS/블로그 후기 | `data/raw/external_web` | 공개 게시물 또는 자발 제출 | 네이버 블로그/유튜브 1차 수집 완료, 인스타그램 자동 수집 제외 | raw/interim에는 공개 출처 확인용 식별자를 보존하되 public 산출물에서는 익명화 또는 집계 |

## SNS/블로그 후기 수집 아이디어

참가자가 직접 자신의 후기 URL 또는 캡처를 제출하는 이벤트 방식이 가장 안전하다.

예시 문구:

```text
2026 연희 요가 위크에 대한 블로그, 인스타그램, SNS 후기를 작성하셨다면
게시물 링크 또는 캡처를 보내주세요.

보내주신 후기는 행사 회고와 향후 개선을 위한 분석에만 사용하며,
공개 리포트에는 개인 계정이 특정되지 않도록 요약 형태로 반영합니다.
```

## 외부 웹 자동 수집 기준

1차 자동 수집은 공식 API를 사용할 수 있는 네이버 블로그와 유튜브로 제한한다.

- 네이버 블로그: 네이버 검색 API의 블로그 검색 결과를 수집하고, confirmed 블로그에 한해 공개 페이지 본문을 별도로 수집한다.
- 유튜브: YouTube Data API v3의 `search.list`, `videos.list`, `channels.list` 결과를 수집한다.
- 인스타그램: 1차 자동 수집 범위에서 제외한다. 나중에 필요하면 참가자 자발 제출 링크 또는 사람이 확인한 공개 링크만 별도 표로 정리한다.

raw와 interim 단계에서는 출처 검증을 위해 공개 블로그명, 블로그 링크, 유튜브 채널명, 채널 ID를 보존할 수 있다.
네이버 블로그 본문 원문은 개인 경험 서술이 포함될 수 있으므로 raw/interim 내부 검수용으로 두고, public 산출물에는 원문 대신 익명 mention ID와 점수/라벨/요약 feature만 남긴다.

다만 다음 작업은 하지 않는다.

- 비공개 계정, 비공개 게시물, 스토리 자동 수집
- 로그인 우회 또는 플랫폼 정책을 우회하는 크롤링
- 공개 계정명으로 개인 실명을 추정하는 작업
- 네이버/유튜브/인스타그램 계정을 서로 연결해 동일인으로 추정하는 작업

public 산출물에는 개인 출처 식별자를 원칙적으로 직접 노출하지 않고, `external_source_####` 형태의 익명 ID 또는 요약 통계로 반영한다.

## 현재 공유 가능 후보

현재 외부 공유 후보는 다음 범위다.

- `data/processed/onstudio/public`
- `data/processed/obud_reviews/public`
- `data/processed/analysis/public`
- `reports/analysis`
- `reports/onstudio`
- `reports/obud_reviews`

구글 드라이브 원본 사본은 raw/private 성격이므로 현재 공유 가능 후보에 포함하지 않는다.
다만 `program_obud_delivery.xlsx`에서 추출한 수업 정원 후보표처럼 민감정보가 없는 파생 산출물은 검토 후 public 분석에 사용할 수 있다.

Google Drive 전량 아카이브는 별도 보안 작업으로 수행했다. 승인 계정 파일, 실제 실행 계정, 공유 원천 계정 파일, 루트 공유 폴더 owner/sharing user를 검증한 뒤 실행했다. 상세 manifest와 리포트는 `reports/google_drive/rightnow_yogi_full_archive_manifest.csv`, `reports/google_drive/rightnow_yogi_full_archive_report.md`에 둔다.

ON STUDIO 캘린더 원본 사본도 raw/private 성격이므로 공유 후보에 포함하지 않는다.
다만 `onstudio_calendar_capacity_reference.csv`처럼 실명/전화번호 없이 수업 단위로 집계된 파생표는 정원 대비 채움률 분석에 사용할 수 있다.

단, 리뷰 본문은 public 표에 있어도 자연어 문장 안에 개인 경험이나 민감 표현이 있을 수 있으므로 최종 제출 전 한 번 더 검토한다.
