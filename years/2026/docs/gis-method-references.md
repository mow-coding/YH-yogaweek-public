# GIS 분석 방법론 레퍼런스 기록

작성일: 2026-05-16

## 목적

이 문서는 2026 연희 요가 위크 GIS 분석을 설명할 때 참고할 수 있는 공식 문서와 학술 레퍼런스를 정리한다.

현재까지 만든 GIS 1차 산출물은 `ON STUDIO 수업 설명 주소 -> ArcGIS 지오코딩 -> 좌표/Hype 결합 -> Folium 지도/GeoJSON` 순서로 만들었다.
동선 최적화와 3D 시간-공간 분석은 아직 실행하지 않았고, 아래 레퍼런스를 바탕으로 후속 분석으로 설계한다.

## 위치/지오코딩

| 주제 | 참고 자료 | 이 프로젝트에서의 의미 |
|---|---|---|
| ArcGIS World Geocoding | ArcGIS Geocoding API/World Geocoding Service | 주소를 위도/경도로 바꾸는 1차 좌표화 |
| ArcGIS Network Analyst | Esri Network Analyst solvers documentation | 최단 경로, closest facility, service area, time window route 같은 고도화 후보 |

현재 지오코딩은 `scripts/geocode_studio_locations_arcgis.py`로 실행한다.
주소 후보는 먼저 ON STUDIO 수업 설명에서 가져오고, 부족한 장소는 공개 웹 검색으로 보강한다.

## 거리/동선/최단경로

| 주제 | 참고 자료 | 이 프로젝트에서의 의미 |
|---|---|---|
| NetworkX Dijkstra shortest path | NetworkX 공식 문서 | 장소 간 이동 네트워크를 만들었을 때 최단거리/최단시간 계산 |
| OSMnx | Geoff Boeing, 2017, Journal of Open Source Software | OpenStreetMap 기반 보행 네트워크 수집, 거리/경로/네트워크 분석 후보 |
| ArcGIS Network Analyst route solver | Esri 공식 문서 | 도보/차량 이동시간, 방문 순서 최적화, time window route 후보 |

1차는 두 지점 간 직선거리로 시작할 수 있다.
하지만 실제 동선 최적화는 도로/보행 네트워크가 필요하므로 OSMnx 또는 지도 API를 검토한다.

## 시간-공간 분석

| 주제 | 참고 자료 | 이 프로젝트에서의 의미 |
|---|---|---|
| Time geography | Hägerstrand 계열 시간지리학, 현대 time geography 리뷰 | 수업 시간표와 이동 가능성을 함께 보는 분석 틀 |
| Space-time prism | Miller/Kwan 계열 accessibility 연구 | 특정 수업 종료 후 다음 수업까지 도달 가능한 장소 판단 |
| Space-time cube | Esri GIS Dictionary, ArcGIS Pro Space Time Cube, GIScience/geovisualization 문헌 | x/y는 지도 위치, z는 시간으로 두는 시각화 틀 |
| WebGL 지도 컬럼 | deck.gl ColumnLayer, CARTO + deck.gl 문서 | 지도 위에 세로 방향 높이를 세우는 인터랙티브 시각화 후보 |

이 프로젝트에서는 참여자 집 주소나 실시간 이동정보를 다루지 않는다.
따라서 개인 추적이 아니라 `비식별 예약 ID + 수업 시간표 + 장소 좌표` 기반의 집계 동선 가능성만 분석한다.

## 현재 적용한 것과 아직 안 한 것

| 단계 | 현재 상태 |
|---|---|
| 장소 주소 수집 | 실행 완료. ON STUDIO 수업 설명 + 공개 웹 검색 |
| 주소 지오코딩 | 실행 완료. ArcGIS World Geocoding Service |
| Hype 지표와 좌표 결합 | 실행 완료 |
| Folium HTML 지도 | 실행 완료 |
| GeoJSON 산출 | 실행 완료 |
| 장소 간 직선거리 matrix | 실행 완료. `scripts/build_gis_distance_matrix.py` |
| OSMnx 보행 네트워크 분석 | 실행 완료. 196개 장소 쌍 모두 OSMnx 보행 네트워크 거리 사용 |
| 수업 시간표 기반 동선 가능성 분석 | 실행 완료. `scripts/build_gis_schedule_flows.py` |
| 지도 기반 space-time cube 시각화 | 실행 완료. `scripts/build_gis_deep_report.py` |

## 2026-05-16 시각화 설계 보정

초기 `시간-공간 큐브`는 Plotly 3D 산점도로 만들었다. 그러나 지도 타일 위에 얹혀 있지 않아, 일반 독자가 “이 점이 연희동 어디를 뜻하는지” 직관적으로 파악하기 어려웠다.

공식/학술 레퍼런스 검토 결과, space-time cube는 원래 지도 좌표 x/y에 시간 z축을 추가하는 방식이다. Esri GIS Dictionary도 이 기법을 x/y 지도 좌표에 시간을 z축으로 더하는 방식으로 설명한다. ArcGIS Pro 튜토리얼도 3D 장면에서 시간 bin이 z축으로 쌓이는 구조와 2D 보조 시각화를 함께 쓰는 방식을 보여준다. deck.gl ColumnLayer와 CARTO + deck.gl 문서는 지도 위에 세로 컬럼을 올리는 웹 기반 구현 후보를 제공한다.

이 프로젝트의 공개 페이지에서는 별도 Mapbox 토큰이나 복잡한 WebGL 의존성을 늘리지 않기 위해, Leaflet/Folium 기반 `지도 위 시간-공간 타워` 방식으로 구현했다.

- x/y: 실제 행사 장소 좌표
- z축: 각 장소 위 세로 막대의 아래에서 위로 흐르는 수업 시작 시간
- 점 크기: 해당 수업의 예약 규모
- 점 색: 리뷰 Hype 신호

따라서 현재 `yeonhui_yoga_week_space_time_cube.html`은 일반적인 3D 산점도가 아니라, 지도 위에 시간축을 세운 2.5D 시각화로 해석한다. 처음 보는 독자에게는 `GIS 기본 지도 -> 시간 흐름 지도 -> 지도 위 시간-공간 큐브` 순서로 안내한다.

## 행사 평가 관점

GIS 분석은 단순 지도 제작이 아니라 행사 운영 평가의 일부로 사용한다.
CDC Program Evaluation Framework의 `맥락 파악 -> 프로그램 설명 -> 평가 질문 집중 -> 근거 수집 -> 결론 도출 -> 활용` 흐름을 참고하고,
eventIMPACTS Toolkit처럼 참여, 만족, 지역 이미지 같은 사회적 영향 지표를 공간적으로 해석하는 방향으로 확장한다.

## 참고 링크

- 파츄코파라다이스 위치 확인: https://www.diningcode.com/profile.php?rid=BicQTTZ7h7jV
- 파츄코파라다이스 위치 확인: https://www.konest.com/contents/gourmet_mise_detail.html?id=38240
- 궁동근린공원 위치 확인: https://tour.gw8.kr/park/534
- OSMnx JOSS 논문: https://joss.theoj.org/papers/10.21105/joss.00215
- NetworkX Dijkstra 공식 문서: https://networkx.org/documentation/stable/reference/algorithms/shortest_paths/dijkstra.html
- ArcGIS Network Analyst solvers: https://pro.arcgis.com/en/pro-app/latest/help/analysis/networks/network-analyst-solver-types.htm
- CDC Program Evaluation Framework: https://www.cdc.gov/evaluation/php/evaluation-framework/index.html
- eventIMPACTS Toolkit: https://www.eventimpacts.com/the-project/the-eventimpacts-toolkit
- Modern time geography review: https://link.springer.com/article/10.1007/s10109-023-00404-1
- Esri GIS Dictionary, Space-time cube: https://support.esri.com/en-us/gis-dictionary/space-time-cube
- ArcGIS Learn, Explore a space-time cube: https://learn.arcgis.com/en/projects/explore-a-space-time-cube/
- deck.gl ColumnLayer: https://deck.gl/docs/api-reference/layers/column-layer
- CARTO + deck.gl: https://docs.carto.com/carto-for-developers/key-concepts/carto-for-deck.gl
- Space-time cube GIS example: https://www.mdpi.com/2220-9964/7/6/209
