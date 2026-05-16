# Public GitHub Release Audit

작성일: 2026-05-16

## 결론

기존 private 작업 레포지토리 `mow-coding/YH-yogaweek`는 그대로 private으로 유지한다.

대신 외부 공유를 위해 별도 public 레포지토리 `mow-coding/YH-yogaweek-public`을 만들었다.

- public URL: <https://github.com/mow-coding/YH-yogaweek-public>
- 로컬 public staging 폴더: `C:\Users\mylifeisbusy\Documents\dev\YH-yogaweek-public`
- public package 생성 스크립트: `years/2026/scripts/prepare_public_repository.py`
- public package 파일 수: 150개
- 금지 패턴 검사: 전화번호/API key/금지 계정 0건
- raw/interim/private/database 경로 검사: 0건

이 방식은 private 레포 전체를 public으로 전환하지 않고, 외부 공개 가능한 파생 데이터와 보고서만 별도 레포로 분리하는 방식이다.

## 책임과 담당

- 책임자/관리자: 유동환, 빅블루 요가 소속 (`bigblue.yoga@gmail.com`)
- 분석담당자: 김성균, 빅블루 요가 소속 (`mow.coding@gmail.com`)
- Google Drive 공유 원천 계정: `rightnow.yogi@gmail.com`

위 세 계정 표기는 프로젝트 책임/출처 설명을 위해 문서에 남긴다. 그 외 개인 이메일, 전화번호, API key는 public 산출물에 남기지 않는다.

## 공개 조건과 충족 여부

1. `data/raw/**`, `data/interim/**`, `data/processed/**/private/**`, `data/database/**`, `.secrets/**`는 public 레포에 포함하지 않는다. 완료.
2. Google Drive full archive manifest는 public repository에 올리지 않는다. 완료.
3. reports 안에 전화번호, API key, 개인 URL, 불필요한 개인 식별자가 없어야 한다. 검사 완료.
4. Google Drive 자료에서 만든 public 분석표는 manifest 원문이 아니라 집계/분류/요약 파생표만 사용한다. 완료.
5. 리뷰와 바이럴 데이터는 원문/URL/계정 식별자를 public으로 내보내지 않고, 익명 ID와 요약 feature만 사용한다. 완료.
6. public package 생성 직후 민감 패턴 검색과 raw/private 경로 검색을 실행한다. 완료.

## 현재 점검 결과

- private 작업 레포지토리에는 원본/raw/private 자료가 남아 있을 수 있으므로 계속 private로 둔다.
- public 레포지토리는 `prepare_public_repository.py`로 별도 생성한 sanitized package만 포함한다.
- public package audit 결과 금지 패턴은 0건이다.
- public package audit 결과 raw/interim/private/database 경로는 0건이다.
- 공개용 분석표와 리포트에는 책임자/분석담당자/공유 원천 계정 외의 이메일을 남기지 않는다.
- public package의 상세 파일 목록은 `years/2026/reports/public_release/public_repository_manifest.csv`와 public 레포의 `PUBLIC_RELEASE_MANIFEST.csv`에 남겼다.

## 권장 운영

- private 작업 레포지토리 `mow-coding/YH-yogaweek`는 계속 private로 유지한다.
- 외부 공유는 `mow-coding/YH-yogaweek-public`을 사용한다.
- public 레포를 갱신할 때에는 private 레포에서 `python years\2026\scripts\prepare_public_repository.py`를 먼저 실행하고, audit 결과가 0건인지 확인한 뒤 public 레포에 커밋/푸시한다.
- 공개 링크를 기관/파트너에게 보내기 전에는 통합 보고서 문장과 public package audit을 사람이 한 번 더 읽는다.
