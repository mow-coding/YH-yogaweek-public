# Full Reanalysis Work Log

작성일: 2026-05-16

## 1. 목적
사용자가 “분석 완벽하게 다시 해”라고 요청하여, 현재 확보된 원자료와 보관된 raw/interim/private 자료를 기준으로 public 분석 산출물을 다시 생성했다.

이번 작업은 새로운 Google Drive 원본 전량 재다운로드가 아니라, 이미 프로젝트에 보관된 원자료와 archive를 기준으로 한 전체 재분석이다. Google Drive 원본 재다운로드는 승인 계정 확인이 필요한 별도 보안 작업으로 분리한다.

## 2. 재실행한 축
- ON STUDIO 예약/취소/수업 전처리와 비식별
- 오붓 리뷰 OCR raw 통합, 리뷰 파싱, 수업명 매칭
- Gemini Vision 리뷰 구조화 검수
- 리뷰 작성자 private 후보 매칭
- 수업/요가원 Hype metrics
- 오붓 1회권/패스권 정산 기준표
- GIS 좌표, 지도, 거리 행렬, 시간표 기반 동선
- 네이버/유튜브 외부 확산(Viral) 수집, 필터, 본문 수집, 본문 feature, Viral metrics
- Google Drive archive 기반 분석
- ON STUDIO 캘린더 정원, Google Drive 정원표 대조, 정원+Hype
- F&B/스폰서 GIS
- 공유용 Notion 커뮤니케이션 자료 요약
- public DuckDB 재생성

## 3. 주요 이슈와 조치
| 이슈 | 조치 |
|---|---|
| 전체 파이프라인을 한 번에 실행했더니 30분 제한에 걸림 | 실행 단위를 core/GIS/Viral/Capacity/DB로 나누어 재실행 |
| 첫 Gemini 재실행에서 `gemini-2.5-flash` 29건 성공, 67건 fallback 발생 | 성공 29건은 보존하고 fallback 67건을 `gemini-3.1-flash-lite`로 재시도 |
| `build_analysis_tables.py`가 통합 방법론 문서를 덮어쓸 위험 | core 생성본은 `methodology_core_analysis_generated.md`로 분리하고, 통합 계보 문서는 보존하도록 수정 |
| Viral 재수집으로 숫자 변경 | 현황판, 방법론, 이해관계자 보고서, Viral 계획/로그 문서 숫자 갱신 |
| `대저택프라이빗/대저택 프라이빗`, `숨명상센터/숨 명상센터` 표기 분리 | 중앙 표준화 함수, 정원+Hype, 정산 스크립트에 별칭을 추가하고 Hype/GIS/정원/정산/보고서 산출물을 재생성 |

## 4. 최종 검수 결과
- Gemini Vision 구조화 검수: 96건
- rule-based fallback: 0건
- Pydantic 검증 실패: 0건
- ON STUDIO 수업: 125건
- ON STUDIO 예약: 1611건
- ON STUDIO 취소: 1048건
- 오붓 리뷰 public: 96건
- 수업별 Hype metrics: 83행
- 요가원별 Hype metrics: 12행
- 정산 class basis: 108행
- 정산 owner-month basis: 19행
- 정산 기준 참여 수: 1회권 589명, 패스 1088명, 총 1677명
- 네이버 블로그 raw: 2415행, 고유 링크 1075개
- 유튜브 raw: 85행, 고유 영상 68개, 고유 채널 32개
- 직접 확인된 외부 언급: 60행
- 네이버 블로그 본문 수집: 58행
- 본문 기준 strong/basic confirmed 블로그: 56행
- GIS 위치 카탈로그: 13행
- GIS 거리 행렬: 169행
- GIS 수업별 장소 증거표: 83행
- GIS 수업 시간표: 261행
- public DuckDB 재생성 완료

## 5. 해석상 주의
- Hype와 Viral은 합산하지 않는다.
- 정산액은 최종 회계액이 아니라 관측자료 기반 추정치다.
- 패스권 정산 구간은 유동환 대표 후속 확인에 따라 소비자 개인의 월간 이용완료 횟수 기준으로 해석한다.
- 이 프로젝트는 오붓 전체 월간 이용내역을 갖고 있지 않으므로, 최종 정산에는 오붓 정산서 또는 서면 확인이 필요하다.
- raw screenshot, raw Drive archive, private reviewer matching, API key는 GitHub 공유 대상이 아니다.

## 5-1. GIS 실제 집결지 기준 정정

사용자가 “야외/러닝 수업은 주관 요가원이 아니라 집결지 기준으로 동선을 봐야 한다”고 지적했다. 이 지적이 맞기 때문에 GIS 파이프라인을 정정했다.

조치 내용:

- `scripts/build_gis_schedule_flows.py`에서 `organizer_studio_key`와 `actual_location_key`를 분리했다.
- 수업 설명의 `📍 장소`, `집합 장소`, `장소:` 문구를 읽어 `class_location_evidence_public.csv`를 만든다.
- 동선 계산은 `actual_location_key` 기준으로 수행한다.
- `러닝으로 이어지는 명상`, `마인드풀 러닝`, `안산 트레킹 오감 명상`, `커피와 요가`, `몸으로 하는 선셋 자애 명상`을 샘플 검수했다.
- 초기 기획안에만 남은 `궁동산/궁둥산`은 active GIS 장소와 수업 시간표에서 제외했다.

검수 결과:

- `class_location_evidence_public.csv`: 83행.
- `class_schedule_gis.csv`: 261행, `schedule_needs_review=false` 261행.
- `location_nodes.csv`: 13행.
- `location_distance_matrix.csv`: 169행.
- active GIS 산출물의 `궁동산/궁둥산` 잔존 0건.

## 6. 2026-05-17 표기 표준화 재검수

사용자가 공개 보고서에서 `대저택프라이빗`과 `대저택 프라이빗`이 별도 행으로 보이는 문제를 지적했다. 확인 결과, GIS 위치 카탈로그에서는 이미 같은 장소로 묶였지만 Hype, 정원+Hype, 정산 집계의 일부 스크립트에서 요가원명 별칭이 빠져 있었다.

조치 내용:

- `scripts/review_processing_utils.py`: `대저택 프라이빗 -> 대저택프라이빗`, `숨 명상센터 -> 숨명상센터` 표준화 추가.
- `scripts/build_capacity_hype_analysis.py`: ON STUDIO 캘린더 정원 자료의 같은 표기 변형을 표준화.
- `scripts/build_obud_settlement_analysis.py`: 정산 집계도 중앙 표준화 함수를 사용하도록 수정.
- Hype, 정원+Hype, 정산, GIS, DuckDB, 통합 이해관계자 보고서를 재생성.

재검수 결과:

- `studio_hype_metrics.csv`: 12행, `대저택프라이빗` 98예약/6리뷰, `숨명상센터` 44예약/1리뷰.
- `studio_capacity_hype_metrics.csv`: 12행, `대저택프라이빗` 11세션/98예약/정원 98/가중 채움률 100.0%.
- `obud_settlement_basis_by_owner_month.csv`: 19행, 잘못 분리된 `대저택 프라이빗`/`숨 명상센터` key 0건.
- 통합 보고서의 채움률 표에서 `대저택프라이빗`은 단일 행으로 표시된다.
