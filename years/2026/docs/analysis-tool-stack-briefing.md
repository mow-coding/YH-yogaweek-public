# 분석 도구 스택 브리핑

작성일: 2026-05-15

이 문서는 2026 연희 요가 위크 분석에서 어떤 도구를 왜 썼는지 설명하기 위한 기록이다.  
목표는 “AI가 알아서 했다”가 아니라, 원천자료부터 리포트까지 어떤 도구와 검증 절차를 거쳤는지 설명 가능하게 만드는 것이다.

## 핵심 스택

| 도구 | 역할 | 이번 프로젝트에서 한 일 |
|---|---|---|
| Python | 전체 처리 실행 환경 | 전처리, OCR 결과 파싱, 매칭, 분석표 생성 |
| pandas | 표 데이터 처리 | CSV 읽기/쓰기, 집계, 결합, Hype metrics 계산 |
| DuckDB | 로컬 SQL 분석 DB | public CSV를 `yogaweek_public.duckdb`로 묶음 |
| JupyterLab | 탐색 분석 후보 | 이후 그래프/가설 탐색용 |
| Plotly | 시각화 후보 | 막대그래프, 레이더 차트, 인터랙티브 차트 후보 |
| Google Cloud Vision | OCR | 오붓 리뷰 스크린샷 96건 OCR |
| EasyOCR | OCR 비교 후보 | 1건 테스트 후 Google Vision을 기본 OCR로 선택 |
| RapidFuzz | 문자열 유사도 매칭 | OCR 수업명을 ON STUDIO 수업명 DB와 매칭 |
| Pydantic | 구조화 결과 검증 | AI/fallback 검수 결과가 정해진 스키마를 지키는지 확인 |
| Gemini Vision API | AI 구조화 검수 후보 | API key 사용 가능 시 이미지+OCR 기반 JSON 검수 |
| scikit-learn | 설명 가능한 모델링 후보 | 취소율/리뷰율/군집 분석 후보 |
| BERTopic | 토픽 모델링 후보 | 리뷰/SNS 텍스트 주제 분석 후보. 1차 리포트에서는 보류 |
| sentence-transformers | 문장 임베딩 후보 | 리뷰 의미 유사도/주제 묶기 후보. 1차 리포트에서는 보류 |
| Folium | GIS 지도 | 요가원/행사 장소 지도와 이동 가능성 지도 생성 |
| NetworkX | 그래프/최단경로 | OSMnx 보행 네트워크 거리 계산과 동선 후보 분석 |
| OSMnx | 보행 네트워크 GIS | OpenStreetMap 기반 실제 도보거리 후보 계산. 실패 시 fallback 사용 |
| geopy/geopandas | GIS 보조 도구 | 좌표/공간 데이터 처리 후보 |

## 현재 실제로 사용된 도구

1차 산출물 생성에 실제로 사용된 도구는 다음과 같다.

- Python
- pandas
- DuckDB
- Google Cloud Vision OCR
- RapidFuzz
- Pydantic
- Gemini Vision API
- Folium
- NetworkX
- OSMnx/geopy/geopandas

Gemini Vision API는 원본 이미지와 OCR 텍스트를 함께 사용해 오붓 리뷰 96건을 전건 구조화 검수했다.
최종 검수 결과는 `gemini_vision_structured_output` 96건, 규칙 기반 fallback 0건, Pydantic 검증 실패 0건이다.
GIS 심화 분석에서는 OSMnx/geopy/geopandas를 설치했으며, 실제 실행에서 OSMnx 보행 네트워크 거리 계산이 성공했다.
OSMnx가 실패할 경우에도 직선거리 x 1.3 보정값으로 자동 fallback하도록 설계했다.

## OCR 처리 방식

오붓 리뷰는 마우스 드래그 복사가 되지 않아 스크린샷을 OCR했다.

처리 순서:

1. 리뷰 스크린샷 96개를 `data/raw/obud_reviews/screenshots`에 저장
2. `scripts/ocr_obud_reviews_google_vision.py`로 Google Vision OCR 실행
3. OCR txt/json을 `data/raw/obud_reviews/ocr_text`에 저장
4. `scripts/build_obud_google_ocr_raw_table.py`로 OCR raw CSV 생성
5. `scripts/parse_obud_reviews.py`로 리뷰 필드 구조화

## 수업명 매칭 방식

OCR은 수업명을 일부 다르게 읽을 수 있다. 예를 들어 영어 표기, 띄어쓰기, 괄호, 오타가 생길 수 있다.

그래서 다음 방식으로 보정했다.

1. OCR 수업명과 ON STUDIO 수업명에서 공백/특수문자 차이를 줄임
2. `Big Blue Yoga`, `Coffee and Yoga`, `Ashtanga Full Primary` 같은 영어 OCR 표현을 표준 수업명 후보로 보정
3. `RapidFuzz`로 유사도 계산
4. 90점 이상 자동 승인, 90점 미만 검수 필요

현재 96건 모두 90점 이상으로 매칭되었다.

## AI 검수 방식

`scripts/ai_review_quality_check.py`는 두 가지 모드로 동작한다.

- Gemini API 사용 가능: 원본 이미지와 OCR 텍스트를 함께 보고 JSON 구조화 검수
- Gemini API 사용 불가: OCR/매칭 결과를 기반으로 규칙 기반 fallback 생성

두 경우 모두 Pydantic으로 결과 스키마를 검증한다.

현재 실행 결과:

- 검수 행 수: 96건
- 검증 실패: 0건
- 모드: `gemini_vision_structured_output`
- 모델: `gemini-2.5-flash` 29건, `gemini-3.1-flash-lite` 67건
- 참고: 중간에 모델 쿼터 이슈가 있어 남은 67건을 다른 Gemini 모델로 이어서 처리했지만, 두 결과 모두 같은 Pydantic 스키마로 검증했다.

## 1차 리포트에서 보류한 도구

BERTopic, sentence-transformers, scikit-learn 기반 모델링은 설치/후보로 남겨두되 1차 리포트에서는 과한 모델링보다 설명 가능한 집계를 우선했다.

이유는 다음과 같다.

- 리뷰 96건은 고급 토픽 모델링을 하기에는 아직 작은 편이다.
- 이해관계자 제출용 리포트에서는 복잡한 모델보다 근거가 명확한 지표가 더 설득력 있다.
- 이후 SNS/블로그/문서/메신저 데이터가 추가되면 텍스트 모델링 가치가 커진다.

## 이해관계자에게 설명할 수 있는 문장

이번 분석은 Python 기반의 재현 가능한 데이터 파이프라인으로 진행했다.  
원천자료는 보존하고, 개인정보가 포함될 수 있는 데이터는 private 영역에 분리했으며, 외부 공유용 데이터는 비식별 public 표로 따로 만들었다.  
OCR은 Google Cloud Vision을 사용했고, 수업명 보정은 ON STUDIO 수업 DB와 RapidFuzz 유사도 매칭을 사용했다.  
AI 검수는 Gemini Vision API로 수행했고, 결과는 Pydantic 스키마로 검증했다.  
GIS 분석은 ArcGIS 지오코딩, Folium 지도, OSMnx/NetworkX 보행 네트워크 분석 후보, 그리고 fallback 거리 추정 규칙을 함께 사용했다.
