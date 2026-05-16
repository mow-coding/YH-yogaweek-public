# 오붓 리뷰 Gemini Vision 검수 실행 로그

작성일: 2026-05-16

## 목적

오붓 리뷰 스크린샷 96건이 Google Vision OCR로 제대로 구조화되었는지 원본 이미지와 OCR 텍스트를 함께 기준으로 AI 검수했다.

## 최종 상태

- 대상 리뷰: 96건
- Gemini Vision 구조화 검수 완료: 96건
- 규칙 기반 fallback: 0건
- Pydantic 검증 실패: 0건
- public 리뷰 전화번호 패턴: 0건

## 실행 이력

1. Gemini API 키를 OCR용 키와 분리했다.
   - Vision OCR용: `.secrets/google-api.txt`
   - Gemini 검수용: `.secrets/gemini-api.txt`
   - 두 파일은 `.gitignore`의 `.secrets/` 규칙으로 GitHub 공유 대상에서 제외된다.

2. 첫 Gemini 검수는 `gemini-2.5-flash`로 실행했다.
   - 29건은 Gemini Vision 구조화 검수에 성공했다.
   - 이후 Google API가 quota exceeded를 반환해 나머지 67건은 일시적으로 `rule_based_fallback` 상태로 남았다.

3. 중간 중단에 대비해 `scripts/ai_review_quality_check.py`를 수정했다.
   - 성공한 Gemini 검수 행은 `--preserve-success`로 보존한다.
   - 새로 성공한 행은 `--checkpoint-every 1` 옵션으로 1건마다 CSV에 저장한다.
   - 각 행에 사용 모델을 남기기 위해 `ai_model` 컬럼을 추가했다.

4. 남은 67건은 `gemini-3.1-flash-lite`로 재시도했다.
   - 모델 사용 가능 여부를 먼저 확인한 뒤 실행했다.
   - 67건 전부 Gemini Vision 구조화 검수에 성공했다.
   - 최종적으로 96건 모두 `gemini_vision_structured_output` 상태가 되었다.

## 최종 모델 분포

| 모델 | 건수 | 사유 |
|---|---:|---|
| `gemini-2.5-flash` | 29 | 최초 실행 성공분 |
| `gemini-3.1-flash-lite` | 67 | 쿼터 이슈 이후 남은 건 재시도 |

## 최종 재생성

검수 완료 후 다음 산출물을 다시 생성했다.

- `data/processed/obud_reviews/public/obud_reviews_deidentified.csv`
- `data/processed/analysis/public/class_hype_metrics.csv`
- `data/processed/analysis/public/studio_hype_metrics.csv`
- `reports/analysis/yeonhui_yoga_week_analysis_report.md`
- `reports/analysis/methodology_and_data_lineage.md`
- `data/database/yogaweek_public.duckdb`

## 재현 명령

```powershell
python scripts\ai_review_quality_check.py --use-api --preserve-success --model gemini-3.1-flash-lite --sleep 3 --max-retries 5 --checkpoint-every 1
python scripts\build_analysis_tables.py
python scripts\build_public_duckdb.py
```
