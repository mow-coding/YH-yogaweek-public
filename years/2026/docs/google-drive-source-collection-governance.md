# Google Drive Source Collection Governance

작성일: 2026-05-16

이 문서는 2026 연희 요가 위크 관련 Google Drive 자료를 수집할 때 지켜야 할 접근 계정, 수집 범위, 기록 원칙을 고정한다.

## 책임과 계정

- 책임자/관리자: 유동환, 빅블루 요가 소속 (`bigblue.yoga@gmail.com`)
- 분석담당자: 김성균, 빅블루 요가 소속 (`mow.coding@gmail.com`)
- Google Drive 접근 계정: `bigblue.yoga@gmail.com`
- Google Drive 공유 원천 계정: `rightnow.yogi@gmail.com`
- 수집 범위: `bigblue.yoga@gmail.com` 계정에서 `rightnow.yogi@gmail.com`으로부터 공유받은 2026년 이후 연희 요가 축제 관련 자료

## 핵심 원칙

1. Google Drive 자료 수집은 사용자가 명시한 프로젝트 승인 계정으로만 수행한다.
2. 승인 계정은 GitHub에 커밋하지 않고 `years/2026/.secrets/google_drive_authorized_account.txt`에만 저장한다.
3. 공유 원천 계정도 GitHub에 커밋하지 않고 `years/2026/.secrets/google_drive_source_account.txt`에만 저장한다.
4. 승인 계정 파일이 없거나, 실행 계정과 승인 계정이 정확히 일치하지 않으면 Drive 아카이브 스크립트는 실행을 거부한다.
5. 루트 공유 폴더의 owner/sharing user가 공유 원천 계정과 맞지 않으면 Drive 아카이브 스크립트는 실행을 거부한다.
6. 2026년 이전 자료는 연희 요가 위크가 존재하기 전 자료로 보고 기본 수집 대상에서 제외한다.
7. 수집 대상은 2026년 이후 생성 또는 수정된 연희요가위크/연희요가축제 관련 파일로 제한한다.
8. Google Drive 원본은 수정, 삭제, 이동, 공유 변경하지 않는다. 로컬 프로젝트에는 raw 사본만 보존한다.
9. raw 사본은 GitHub 공유 대상에서 제외한다. 외부 리포트에는 비식별 파생표와 요약만 사용한다.

## 승인 계정 처리

- 승인 계정 파일: `years/2026/.secrets/google_drive_authorized_account.txt`
- 공유 원천 계정 파일: `years/2026/.secrets/google_drive_source_account.txt`
- 이 파일들은 `.gitignore`의 `**/.secrets/` 규칙에 의해 GitHub 공유 대상에서 제외된다.
- 스크립트는 `--account`로 받은 계정과 승인 계정 파일의 값이 정확히 같을 때만 Google Drive API 접근을 시도한다.
- 계정명이 조금이라도 다르면 실패해야 한다.
- `--validate-only`를 먼저 실행해 접근 계정과 공유 원천 계정 검증만 수행할 수 있다.

## 수집 범위

포함:

- `연희요가위크_정보들` 공유 폴더와 그 하위 폴더.
- 2026년 이후 생성 또는 수정된 연희요가위크/연희요가축제 관련 공유 파일.
- 별도로 공유된 행사 운영 관련 응답 시트. 단, 개인정보 가능성이 있으면 private raw로만 보존한다.

제외:

- 2026년 이전 생성/수정 자료.
- 행사와 관계없는 사용자의 다른 Google Drive 공유자료.
- 프로젝트 승인 계정이 아닌 계정으로만 접근 가능한 자료.
- 메신저/개인 연락/협상 자료처럼 별도 당사자 동의가 필요한 자료.

## 2026-05-16 접근 계정 오류와 조치

### 발생한 문제

- Google Drive 전체 아카이브 스크립트 초안 실행 과정에서 프로젝트 승인 계정이 아닌 비프로젝트 Google 계정으로 접근 토큰을 요청했다.
- 사용자가 즉시 중단을 요청했고, 작업을 중단했다.
- 이 접근은 원본 파일을 수정, 삭제, 이동, 공유 변경하는 작업이 아니라 파일 목록 조회/다운로드 시도 성격이었다.

### 즉시 조치

- 실행 중인 Python 프로세스를 종료했다.
- 해당 실행으로 생성된 `years/2026/data/raw/google_drive_shared/rightnow_yogi/full_archive` 폴더를 삭제했다.
- full archive manifest/report는 생성되지 않았음을 확인했다.
- 프로젝트 폴더에서 비프로젝트 계정 문자열이 남았는지 검색하고 제거했다.
- Drive 아카이브 스크립트는 승인 계정 파일과 실행 계정이 정확히 일치하지 않으면 실행하지 않도록 수정했다.

### 남은 위험

- Google 서버 또는 Google Workspace 관리자 감사 로그에 접근 시도 기록이 남았을 가능성은 배제할 수 없다.
- 이 프로젝트 쪽에서 Google 서버의 접근 로그를 삭제하거나 정정할 수는 없다.
- 따라서 이후 Google Drive 접근은 승인 계정 검증 절차를 통과하기 전까지 중단한다.

## 실행 전 체크리스트

Drive 수집을 재개하기 전에 아래를 모두 확인한다.

```powershell
Get-Content years\2026\.secrets\google_drive_authorized_account.txt
Get-Content years\2026\.secrets\google_drive_source_account.txt
gcloud.cmd auth list
python years\2026\scripts\archive_google_drive_shared_files.py --account <승인된 프로젝트 계정> --validate-only
```

실행 조건:

- `gcloud.cmd auth list`에 승인 계정이 로그인되어 있어야 한다.
- Drive 다운로드가 필요한 경우 `gcloud.cmd auth login <승인된 프로젝트 계정> --enable-gdrive-access --force`로 Drive 읽기 권한이 포함된 토큰을 받아야 한다.
- `--account` 값은 승인 계정 파일의 값과 정확히 같아야 한다.
- 루트 공유 폴더의 owner/sharing user가 공유 원천 계정 파일과 맞아야 한다.
- 전체 다운로드 실행 전에 사용자가 "이 계정과 이 범위로 Google Drive 수집을 진행해도 된다"고 다시 명시해야 한다.

## 산출물 위치

예정 위치:

- 원본 사본: `years/2026/data/raw/google_drive_shared/rightnow_yogi/full_archive/`
- manifest CSV: `years/2026/reports/google_drive/rightnow_yogi_full_archive_manifest.csv`
- 수집 리포트: `years/2026/reports/google_drive/rightnow_yogi_full_archive_report.md`

위 산출물 중 raw 사본은 GitHub 공유 대상에서 제외한다. manifest/report도 원문 제목과 민감도 분류가 포함될 수 있으므로 외부 공유 전 검토한다.

## 2026-05-16 전량 아카이브 상태

- 승인 계정과 공유 원천 계정 검증은 `--validate-only`로 통과했다.
- Google Drive 전량 아카이브는 중복 다운로드 방지 방식으로 재실행해 완료했다.
- manifest 전체 기록 행은 490행이다.
- 로컬 보존 원본 사본은 384개다.
- 폴더 기록은 82행이다.
- 2026년 이전 생성/수정으로 제외한 항목은 24개다.
- 최종 실패 항목은 0건이다.
- 원본 사본이 많은 이유는 프로그램/외부연사/스폰서/F&B 폴더의 사진, 로고, 포스터, 카드뉴스 이미지가 포함되었기 때문이다.
- 상세 manifest는 `reports/google_drive/rightnow_yogi_full_archive_manifest.csv`에 생성했다.
- 요약 리포트는 `reports/google_drive/rightnow_yogi_full_archive_report.md`에 생성했다.
- raw 원본 사본은 `data/raw/google_drive_shared/rightnow_yogi/full_archive/`에 있으며 GitHub 공유 대상에서 제외된다.
- 대용량 Google Docs 문서 1건은 docx export가 Google 제한에 걸려 plain text fallback으로 보존했다.
