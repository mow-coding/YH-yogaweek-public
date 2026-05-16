# 2026-05-17 공개 전 품질 감사 작업 일지

## 목적

공개 레포를 전시용 1커밋 릴리스로 정리하기 전에, 작은 오탈자와 별칭 문제가 분석 결과를 다시 무너뜨리지 않도록 공개 전 품질 게이트를 만들고 전체 산출물을 재생성했다.

이번 작업은 단순한 디자인 수정이 아니라 분석 기준 자체의 신뢰성을 점검하는 작업이다. 특히 공개 보고서에서 요가원/장소/수업명이 잘못 갈라지면 예약, 리뷰, 정원, 정산, GIS, Viral 지표가 모두 흔들릴 수 있으므로 표준화 규칙을 중앙화했다.

## 확인된 결함

- `[시이작] 숨쉬는 테라피`와 `[시이작]숨쉬는 테라피`가 같은 수업인데 공백 차이 때문에 수업별 집계에서 갈라져 있었다.
- `review_0044`의 OCR 원문은 `[연희정음 랜드마크] 빅블루의 호흡 회복 요가`였는데, 기존 `RapidFuzz token_set_ratio`가 짧은 후보 `[연희정음] 요가`에 100점을 주어 과소매칭했다.
- 추가 감사 중 `[연희정음|랜드마크] 명상 흐름의 슬로우 빈야사`, `[연희정음|랜드마크] 부드럽게 비기너요가`, `[연남장|커뮤니티허브] Being 감각을 깨우는 하타요가`가 장소 괄호 표기 차이 때문에 리뷰 전용 행으로 따로 생기는 문제를 발견했다.
- OCR이 `[시이작]`을 `[시작]`으로 읽은 리뷰 3건이 있었고, 그중 1건은 짧은 일반 후보 `요가`로 붙을 위험이 있었다.
- Viral 축에서 `비전스트롤`과 `비전스트롤 콜라보` 표기가 분리될 수 있는 위험을 확인했다.
- GIS 축에서 초기 기획안의 `궁동산/궁둥산` 행이 active 장소처럼 남아 지도와 거리 행렬을 부풀릴 위험을 확인했다.
- 야외/러닝/트레킹 수업은 주관 요가원이 아니라 실제 집결지 기준으로 동선을 계산해야 하므로, 수업별 실제 장소 증거를 별도 표로 관리하도록 기준을 보강했다.

## 조치

- `scripts/review_processing_utils.py`에 `NAME_CANONICALIZATION_REGISTRY`와 공통 표준화 helper를 추가했다.
- 사람이 확인할 수 있는 표준화 기록으로 `references/name_canonicalization_registry.csv`를 추가했다.
- `scripts/match_review_classes.py`는 여러 번 재실행해도 기존 매칭 컬럼이 중복되지 않게 만들었고, 수업 몸통 제목뿐 아니라 괄호 안 장소 라벨과 전체 class key를 함께 보게 수정했다.
- `RapidFuzz token_set_ratio`의 짧은 후보 과대점수를 막기 위해 긴 OCR 제목이 `요가`, `명상`, `수업`, `필라테스` 같은 일반 후보로 붙는 경우를 자동 승인하지 않도록 했다.
- `scripts/ai_review_quality_check.py --preserve-success`는 Gemini가 만든 리뷰 본문/별점/태그는 보존하고, 결정론적 수업 매칭 필드만 최신 결과로 동기화하게 수정했다.
- `scripts/build_analysis_tables.py`는 `studio_key + class_base_key` 기준으로 먼저 묶고 대표 표시명을 붙이도록 바꿨다.
- `scripts/build_obud_settlement_analysis.py`, `scripts/build_capacity_hype_analysis.py`, Viral 관련 스크립트에도 같은 표준화 기준을 반영했다.
- `scripts/validate_public_release.py`를 새로 만들어 공개 전 품질 게이트를 추가했다.
- `scripts/build_gis_schedule_flows.py`에 `organizer_studio_key`와 `actual_location_key`를 분리하는 로직을 추가했다.
- `class_location_evidence_public.csv`를 생성해 수업 설명의 `📍 장소`/`집합 장소` 문구와 실제 동선 계산 위치를 함께 남겼다.

## 재생성 결과

- ON STUDIO 수업: 125건 유지.
- ON STUDIO 예약: 1,611건 유지.
- ON STUDIO 취소: 1,048건 유지.
- 오붓 리뷰 public: 96건 유지.
- Gemini Vision 구조화 검수: 96건 유지, fallback 0건.
- 리뷰 `needs_review`: 0건.
- 수업명 매칭 `class_match_needs_review`: 0건.
- `class_hype_metrics.csv`: 83행.
- `class_capacity_hype_metrics.csv`: 83행, `capacity_match_status=needs_review` 0건.
- `studio_hype_metrics.csv`: 12행 유지.
- `studio_capacity_hype_metrics.csv`: 12행 유지.
- 정산 class estimate: 110행.
- 정산 studio-month estimate: 19행.
- GIS 장소 노드: 13행.
- GIS 거리 matrix: 169행.
- GIS 수업별 장소 증거표: 83행.
- OSMnx 보행 네트워크 계산 상태: 성공.
- active GIS 산출물의 `궁동산/궁둥산` 잔존: 0건.

기존 계획상 알려진 결함만 반영하면 `class_hype_metrics`와 `class_capacity_hype_metrics`는 84행으로 줄어들 것으로 예상했다. 그러나 공개 전 감사에서 OCR 별칭과 장소 괄호 결함을 추가로 발견해 기존 리뷰 전용 행들이 올바른 기존 수업으로 흡수되었고, 최종 83행이 최신 기준이다.

## 품질 게이트

`scripts/validate_public_release.py`는 다음 항목을 검사한다.

- 공개/분석 산출물 행 수.
- `대저택 프라이빗`, `숨 명상센터`, `비전스트롤` 같은 비표준 집계 key 잔존 여부.
- `studio_key`, `(studio_key, class_base_key)`, `(service_month, studio_key, class_base_key)` 중복 여부.
- `review_0044`의 올바른 수업 매칭 여부.
- 긴 OCR 원문이 짧은 일반 후보로 과소매칭된 사례.
- 정원 매칭 `needs_review`.
- public package의 전화번호, API key, 금지 계정 문자열.
- Markdown 표 pipe 구조.
- 공개 HTML 통합 보고서 H1 중복.
- GitHub API 기준 public contributor가 `mow-coding`만 표시되는지.

최종 결과는 PASS이며, 보고서는 `reports/public_release/release_quality_gate_report.md`와 public package의 `PUBLIC_RELEASE_QUALITY_GATE.md`에 남겼다.

## 브라우저 검증

Chrome headless와 Playwright Core로 public package의 로컬 HTML을 열어 확인했다.

- `index.html`: H1 1개, 가로 overflow 없음, 콘솔 오류 없음.
- `yeonhui_yoga_week_integrated_stakeholder_report.html`: H1 1개, 표 24개, 가로 overflow 없음, 콘솔 오류 없음.
- `yeonhui_yoga_week_space_time_cube.html`: Leaflet pane 렌더링 확인, marker 12개, 콘솔 오류 없음.
- `yeonhui_yoga_week_transition_map.html`: Leaflet pane 렌더링 확인, 콘솔 오류 없음.
