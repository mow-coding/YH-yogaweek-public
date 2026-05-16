# 프로젝트 운영 표준

작성일: 2026-05-16

이 문서는 2026 연희 요가 위크 분석 프로젝트를 앞으로 어떻게 진행할지 정한 운영 규칙이다.

목표는 단순하다. 분석을 전문적으로 보이게 만드는 것이 아니라, 실제로도 재현 가능하고 설명 가능한 방식으로 진행하는 것이다.

## 1. 절대 원칙

1. 새 분석 방법을 쓰기 전에는 먼저 조사한다.
2. 모든 작업은 정형화된 작업일지에 남긴다.
3. 파일, 폴더, 변수, 스크립트 이름은 규칙에 맞게 만든다.
4. 원본 데이터는 수정하지 않는다.
5. public/private 경계를 항상 먼저 생각한다.
6. 분석 결과에는 근거 파일, 생성 스크립트, 검증 결과, 한계를 함께 남긴다.

## 2. 방법론 조사 원칙

새로운 분석 방법이나 시각화 방법을 적용하기 전에는 `방법론 조사 메모`를 남긴다.

예시는 다음과 같다.

```markdown
## 방법론 조사 메모

- 분석 질문:
- 후보 방법:
- 참고한 자료:
- 이 방법을 선택한 이유:
- 이 방법을 쓰지 않기로 한 대안:
- 필요한 입력 데이터:
- 생성할 출력 데이터:
- 개인정보/민감정보 위험:
- 검증 방법:
- 해석할 때 주의할 한계:
```

적어도 다음 경우에는 반드시 조사 메모를 남긴다.

- 새로운 지표를 만든다.
- 새로운 모델이나 알고리즘을 쓴다.
- 지도, 네트워크, 토픽 모델링, 감정 분석처럼 해석이 강한 분석을 한다.
- 외부 기관에 제출할 리포트의 핵심 근거가 되는 분석을 한다.
- API, 크롤링, OCR, LLM 등 외부 도구를 쓴다.

## 3. 작업일지 원칙

작업일지는 `docs/work-log.md`에 남긴다.

모든 작업 기록은 다음 형식을 따른다.

```markdown
## YYYY-MM-DD HH:MM KST - 작업 제목

### 요청/배경
- 사용자가 요청한 내용:
- 이 작업이 필요한 이유:

### 범위
- 포함:
- 제외:

### 선행 조사
- 참고 자료:
- 적용하기로 한 기준:

### 실행
- 수정/생성한 파일:
- 실행한 주요 명령:
- 사용한 입력:
- 생성한 출력:

### 검증
- 행 수/파일 수:
- 개인정보/API key 점검:
- 실패/재시도:

### 판단과 한계
- 이번 작업에서 내린 판단:
- 아직 조심해야 할 점:

### 다음 작업
- 다음에 이어서 할 일:
```

이 형식은 귀찮아 보여도 중요하다. 나중에 기관이나 파트너에게 “어떻게 수집했고, 어떻게 전처리했고, 어떤 기준으로 해석했는지” 설명할 때 이 작업일지가 그대로 근거가 된다.

## 4. 파일과 폴더 규칙

### 폴더

현재 프로젝트는 다음 구조를 기준으로 관리한다.

```text
data/raw/                 원본. 수정하지 않음. GitHub 공유 제외.
data/interim/             중간 산출물. 검수/파싱/매칭용. GitHub 공유 제외.
data/processed/**/public/ 외부 공유 후보 분석표.
data/processed/**/private/ 내부 검증용 민감 데이터. GitHub 공유 제외.
data/external/            공개 외부 기준표.
data/database/            DuckDB 등 생성 DB. GitHub 공유 제외.
docs/                     계획, 원칙, 방법론, 작업일지.
reports/                  분석 리포트와 검증 리포트.
scripts/                  재현 가능한 처리 스크립트.
references/               가격표, 검색어, 참고 기준표.
notebooks/                탐색용 노트북. 핵심 파이프라인은 scripts로 승격.
```

### 파일명

- 문서: `kebab-case.md`
  - 예: `project-current-status.md`
- 파이썬 스크립트: `lower_snake_case.py`
  - 예: `build_viral_metrics.py`
- CSV/데이터: `lower_snake_case.csv`
  - 예: `onstudio_calendar_capacity_reference.csv`
- 날짜가 필요한 파일: `YYYY-MM-DD`를 쓴다.
  - 예: `onstudio_manual_supplement_2026-05-09.md`

새 파일 이름은 다음 질문을 통과해야 한다.

- 이 파일이 무엇인지 이름만 보고 알 수 있는가?
- raw/interim/processed/reports/docs/scripts 중 어디에 속하는지 명확한가?
- public/private 성격이 이름이나 경로로 드러나는가?
- 같은 유형의 기존 파일명과 스타일이 맞는가?

## 5. 변수와 컬럼 이름 규칙

CSV 컬럼과 파이썬 변수는 `lower_snake_case`를 쓴다.

권장 컬럼:

- 출처 추적: `source_file`, `source_sheet`, `source_line`, `source_url`, `source_image`
- 표준 키: `studio_key`, `class_base_key`, `class_session_key`, `location_key`
- 시간: `class_date`, `start_time`, `end_time`, `start_datetime_iso`
- 검수: `match_score`, `match_status`, `confidence`, `needs_review`
- 비식별: `participant_public_id`, `reviewer_public_id`, `external_source_id`

금지 또는 주의:

- public 파일에 `name`, `phone`, `email`, `source_url` 같은 식별 가능 컬럼을 그대로 두지 않는다.
- `result1`, `final_final`, `new_data`, `test2` 같은 의미 없는 이름을 쓰지 않는다.
- 사람이름이나 전화번호를 파일명에 넣지 않는다.

## 6. 스크립트 작성 규칙

스크립트는 한 가지 일을 명확하게 해야 한다.

권장 구조:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "..."
OUTPUT_PATH = ROOT / "data" / "..."

def main() -> None:
    ...

if __name__ == "__main__":
    main()
```

스크립트마다 지켜야 할 것:

- 입력과 출력 경로를 상단 상수로 둔다.
- API key나 비밀번호를 코드에 쓰지 않는다.
- 같은 스크립트를 다시 실행해도 결과가 재생성되게 만든다.
- 실행 후 행 수, 파일 수, 검수 필요 수를 출력한다.
- public 파일을 만들 때 개인정보 패턴을 점검한다.
- 실패 가능성이 있는 단계는 `needs_review`, `match_status`, `confidence` 같은 컬럼으로 남긴다.
- 복잡한 탐색은 노트북으로 해도 되지만, 재현 가능한 최종 처리는 `scripts/`로 옮긴다.

## 7. 분석 리포트 규칙

리포트에는 항상 다음 내용을 넣는다.

- 분석 질문
- 사용 데이터
- 사용 스크립트
- 주요 결과
- 검증 결과
- 한계
- 다음 작업

해석 문장은 단정하지 않는다.

나쁜 표현:

- “이 요가원이 제일 좋다.”
- “이 수업이 실패했다.”
- “이 지표가 브랜드 파워다.”

좋은 표현:

- “예약/리뷰/외부 언급 기준에서 강한 반응이 관찰됐다.”
- “정원 대비 채움률은 높지만, 취소율도 함께 확인할 필요가 있다.”
- “이 지표는 브랜드 서열이 아니라 행사 안에서의 반응 프로필이다.”

## 8. public/private 점검 규칙

외부 공유 전에 반드시 확인한다.

```powershell
rg -n "010-[0-9]{4}-[0-9]{4}|AIza[0-9A-Za-z_\-]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" data\processed reports docs
```

확인 기준:

- public CSV에 전화번호가 없어야 한다.
- public CSV에 API key가 없어야 한다.
- public CSV에 정확한 개인 URL이나 계정 식별자가 없어야 한다.
- raw, interim, private, database는 GitHub 공유 대상에서 제외한다.

## 9. 외부 계정/API 접근 규칙

외부 계정, API, 클라우드, Google Drive, GitHub, OCR, LLM API를 사용할 때는 실행 전 계정과 권한을 먼저 확인한다.

특히 Google Drive 자료는 다음 규칙을 따른다.

- 이 프로젝트의 Google Drive 접근 계정은 `bigblue.yoga@gmail.com`이다.
- 이 프로젝트의 분석담당자는 김성균이며, 작업 계정은 `mow.coding@gmail.com`이다.
- Google Drive 수집 대상은 `rightnow.yogi@gmail.com`으로부터 공유받은 2026년 이후 연희 요가 축제 관련 자료로 제한한다.
- 프로젝트 승인 계정이 아닌 Google 계정으로 Drive 자료를 열람하거나 다운로드하지 않는다.
- 승인 계정과 공유 원천 계정은 `.secrets` 아래 private 파일에도 저장해 스크립트가 실행 전 검증할 수 있게 한다.
- Drive 수집 스크립트는 승인 계정 파일과 실행 계정이 정확히 일치하지 않으면 실패해야 한다.
- Drive 수집 스크립트는 루트 공유 폴더의 owner/sharing user가 공유 원천 계정과 맞지 않으면 실패해야 한다.
- 2026년 이전 자료는 기본적으로 수집하지 않는다.
- Drive 원본은 수정, 삭제, 이동, 공유 변경하지 않는다.
- Drive 관련 사고나 중단은 `docs/google-drive-source-collection-governance.md`와 `docs/work-log.md`에 기록한다.

GitHub repository를 public으로 전환하기 전에는 다음을 추가로 확인한다.

- `.gitignore`가 `data/raw/**`, `data/interim/**`, `data/processed/**/private/**`, `data/database/**`, `.secrets/**`를 막고 있는가?
- reports 안에 원본 URL, API key, 전화번호, 불필요한 개인 식별자가 남아 있지 않은가?
- Google Drive manifest처럼 파일명과 source id가 남는 자료는 public 공유 대상에서 제외하거나 별도 비식별 요약본으로 대체했는가?

## 10. 현재 프로젝트에 적용한 기준

| 영역 | 적용 기준 |
|---|---|
| 전체 데이터 분석 절차 | CRISP-DM의 반복형 데이터 이해/준비/평가 흐름을 참고 |
| 재현성 | The Turing Way, Good Enough Practices의 재현 가능 연구 원칙 참고 |
| 폴더 구조 | Cookiecutter Data Science 계열의 raw/interim/processed 분리 참고 |
| 데이터 계보 | 모든 public 산출물에 원천 파일, 스크립트, 행 수, 검수 상태를 기록 |
| 민감정보 | raw/private와 public을 분리하고, public 산출물은 식별자 제거 |
| 텍스트 분석 | 원문 본문은 raw/interim에 두고 public에는 점수/라벨/요약 feature만 노출 |

## 11. 참고 자료

- [The Turing Way](https://book.the-turing-way.org/): 재현 가능하고 윤리적인 데이터 과학 프로젝트 운영 참고.
- [Good Enough Practices in Scientific Computing](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005510): 연구 컴퓨팅의 기본 프로젝트 구조, README, 데이터 관리, 협업 원칙 참고.
- [IBM CRISP-DM Help Overview](https://www.ibm.com/docs/en/spss-modeler/saas?topic=dm-crisp-help-overview): 데이터 마이닝 프로젝트의 반복형 생애주기 참고.
- [Cookiecutter Data Science @ Nesta](https://nestauk.github.io/ds-cookiecutter/structure/): 데이터 과학 프로젝트의 폴더 구조, 환경, secrets 관리, report 구조 참고.
