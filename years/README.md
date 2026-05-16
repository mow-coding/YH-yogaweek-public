# years

연도별 연희 요가 위크 분석 프로젝트를 모아두는 폴더입니다.

각 연도 폴더는 독립적으로 실행 가능한 분석 프로젝트가 되도록 구성합니다.

```text
years/
  2026/
    data/
    docs/
    reports/
    scripts/
    references/
    notebooks/
```

새 연도 데이터를 추가할 때는 `years/<year>/` 폴더를 만들고, 해당 연도 안에서 `raw -> interim -> processed -> reports` 흐름을 유지합니다.
