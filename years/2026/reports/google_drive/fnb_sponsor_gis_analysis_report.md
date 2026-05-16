# F&B and Sponsor GIS Analysis Report

작성일: 2026-05-17

## 요약

- F&B 협업 브랜드: 16개
- F&B 좌표 확보: 16개
- 수동 검토 필요: 0개
- 행사 장소 300m 이내 F&B 후보: 14개
- 스폰서 asset inventory 브랜드/폴더: 15개
- 스폰서 asset 총합: 174개

## F&B 거리 후보

- 비전스트롤 (카페): nearest=비전스트롤 콜라보, distance_km=0.0
- 케뚜 (식당): nearest=시이작, distance_km=0.0
- 텍스처커피 (카페): nearest=파츄코파라다이스, distance_km=0.031
- 연희동국화빵 (디저트): nearest=연희정음, distance_km=0.042
- 엄마식탁 (식당): nearest=연희정음, distance_km=0.042
- 금옥호두과자 (디저트): nearest=연희정음, distance_km=0.06
- 춘광 (요리주점): nearest=빅블루요가, distance_km=0.07
- 노만주의 (카페): nearest=비전스트롤 콜라보, distance_km=0.088
- 탄정 (티하우스): nearest=시이작, distance_km=0.094
- 도우클럽 (식당): nearest=연희정음, distance_km=0.095
- 금옥당 (디저트): nearest=빅블루요가, distance_km=0.103
- 마우디 (식당): nearest=데이스타콜라보, distance_km=0.103
- 마우디브런치 (식당): nearest=마이트리, distance_km=0.113
- 쏘블루 (카페/서점): nearest=대저택프라이빗, distance_km=0.139
- 베지스 (식당): nearest=마인드플로우, distance_km=0.408
- 위어도우 (식당): nearest=대저택프라이빗, distance_km=0.431

## 해석

- 이 분석은 실제 쿠폰 사용 기록이 아니라, F&B 협업표와 주소 기반 동선 가능성 분석이다.
- 가까운 F&B 브랜드는 다음 회차에서 지도, 체크인 안내, 웰니스 맵, 쿠폰 동선 설계에 활용할 수 있다.
- 스폰서 asset inventory는 후원사별 자료 보유량을 보여줄 뿐, 후원 가치나 관계의 우열을 뜻하지 않는다.

## 산출물

- `data\processed\analysis\public\fnb_partner_brands_public.csv`
- `data\processed\analysis\public\fnb_partner_brands_gis.geojson`
- `data\processed\analysis\public\sponsor_asset_inventory_public.csv`

## 한계

- 주소는 Google Drive 협업표 기준이며, 실제 영업 위치/폐업/이전 여부는 별도 확인이 필요하다.
- 거리는 직선거리다. 실제 보행 시간은 OSMnx 보행 네트워크 분석으로 확장할 수 있다.
- 쿠폰 사용 실제 로그가 없으므로 지역 소비 효과는 아직 가능성 분석 단계다.
