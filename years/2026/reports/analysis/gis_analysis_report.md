# GIS Analysis Report

Generated: 2026-05-17

## Scope

This first GIS pass connects ON STUDIO reservations/cancellations, Obud review metrics, and venue coordinates.

## Inputs

- Studio location seed/geocoding table: `data/external/studio_locations_public.csv`
- Studio Hype metrics: `data/processed/analysis/public/studio_hype_metrics.csv`
- Class Hype metrics: `data/processed/analysis/public/class_hype_metrics.csv`

## Outputs

- Studio GIS CSV: `data/processed/analysis/public/studio_hype_gis.csv`
- Class GIS CSV: `data/processed/analysis/public/class_hype_gis.csv`
- Event location catalog GIS CSV: `data/processed/analysis/public/event_location_catalog_gis.csv`
- Studio GIS GeoJSON: `data/processed/analysis/public/studio_hype_gis.geojson`
- Event location catalog GeoJSON: `data/processed/analysis/public/event_location_catalog_gis.geojson`
- Interactive map: `reports/analysis/yeonhui_yoga_week_gis_map.html`

## Geocoding Coverage

- Normalized studio/place rows: 12
- Rows with coordinates: 12
- Rows needing manual coordinate verification: 0
- Location catalog rows: 13
- Location catalog rows with coordinates: 13
- Location catalog rows needing manual coordinate verification: 0
- Class metric rows joined to GIS locations: 83

## Spatial Reading

Marker size in the HTML map follows net reservations. Marker color follows review Hype. Gray markers are location-only nodes that currently have no reservation/review metric row. This is not a ranking table; it is a spatial reaction profile.

### High Net Reservation Nodes

| normalized_studio_key | display_name | net_reservation_count | review_count | reservation_hype | review_hype | distance_from_activity_center_km |
| --- | --- | --- | --- | --- | --- | --- |
| 연남장 | 연남장 | 150 | 12 | 95.83 | 43.75 | 0.535 |
| 마인드플로우 | 마인드플로우 | 112 | 13 | 87.5 | 62.5 | 1.054 |
| 마이트리 | 마이트리 | 109 | 13 | 79.17 | 58.34 | 0.302 |
| 시이작 | 시이작 | 58 | 13 | 70.83 | 66.67 | 0.208 |
| 대저택프라이빗 | 바운드하우스 | 47 | 6 | 62.5 | 54.16 | 0.269 |
| 빅블루요가 | 빅블루요가 | 42 | 21 | 54.17 | 91.66 | 0.014 |
| 무릉 | 무릉 | 33 | 1 | 45.83 | 16.66 | 0.251 |
| 연희정음 | 연희정음 | 23 | 12 | 37.5 | 77.08 | 0.234 |
| 숨명상센터 | 숨 명상센터 | 14 | 1 | 29.17 | 20.83 | 0.796 |
| 너울너울 | 너울너울 | 5 | 3 | 20.83 | 56.25 | 1.29 |

### High Review Nodes

| normalized_studio_key | display_name | net_reservation_count | review_count | review_rate_per_reservation | review_hype | satisfaction_hype |
| --- | --- | --- | --- | --- | --- | --- |
| 빅블루요가 | 빅블루요가 | 42 | 21 | 0.105 | 91.66 | 97.43 |
| 마이트리 | 마이트리 | 109 | 13 | 0.04452054794520548 | 58.34 | 97.85 |
| 시이작 | 시이작 | 58 | 13 | 0.05627705627705628 | 66.67 | 98.46 |
| 마인드플로우 | 마인드플로우 | 112 | 13 | 0.04814814814814815 | 62.5 | 99.08 |
| 연남장 | 연남장 | 150 | 12 | 0.034482758620689655 | 43.75 | 96.67 |
| 연희정음 | 연희정음 | 23 | 12 | 0.125 | 77.08 | 96.17 |
| 대저택프라이빗 | 바운드하우스 | 47 | 6 | 0.061224489795918366 | 54.16 | 81.0 |
| 너울너울 | 너울너울 | 5 | 3 | 0.1 | 56.25 | 100.0 |
| 무릉 | 무릉 | 33 | 1 | 0.02127659574468085 | 16.66 | 100.0 |
| 숨명상센터 | 숨 명상센터 | 14 | 1 | 0.022727272727272728 | 20.83 | 100.0 |

### Outer Nodes In This Dataset

| normalized_studio_key | display_name | address | distance_from_activity_center_km | net_reservation_count | review_count |
| --- | --- | --- | --- | --- | --- |
| 너울너울 | 너울너울 | 서울특별시 마포구 성산동 3-30 | 1.29 | 5 | 3 |
| 마인드플로우 | 마인드플로우 | 서울특별시 서대문구 연희로 224 3층 | 1.054 | 112 | 13 |
| 숨명상센터 | 숨 명상센터 | 서울특별시 서대문구 연희동 16-2 2층 | 0.796 | 14 | 1 |
| 연남장 | 연남장 | 서울특별시 서대문구 연희로5길 22 | 0.535 | 150 | 12 |
| 마이트리 | 마이트리 | 서울특별시 서대문구 연희로 85 5층 | 0.302 | 109 | 13 |
| 대저택프라이빗 | 바운드하우스 | 서울특별시 서대문구 연희동 108-6 | 0.269 | 47 | 6 |
| 무릉 | 무릉 | 서울특별시 서대문구 연희로11마길 23 | 0.251 | 33 | 1 |
| 연희정음 | 연희정음 | 서울특별시 서대문구 연희동 189-2 | 0.234 | 23 | 12 |
| 시이작 | 시이작 | 서울특별시 서대문구 연희로11나길 5 2층 | 0.208 | 58 | 13 |
| 비전스트롤 콜라보 | 비전스트롤 | 서울특별시 서대문구 연희로11가길 24 | 0.208 | 3 | 1 |

## Limits

- Coordinates are generated from ON STUDIO class-description addresses, then geocoded through ArcGIS World Geocoding Service.
- `needs_manual_verification=true` rows should be checked against a primary map source before external publication.
- This pass maps venue/studio locations, not participant home locations. It therefore describes the event network footprint, not attendee catchment areas.
