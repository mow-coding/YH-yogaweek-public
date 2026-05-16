# GIS Deep Analysis Report

Generated: 2026-05-17

## Scope

This report extends the first GIS pass from static venue points into distance, schedule, and movement-feasibility analysis.
It does not use participant home addresses or real GPS traces. Movement means same-day possible transitions inferred from de-identified reservations and class times.

## Outputs

- Location nodes: `data/processed/analysis/public/location_nodes.csv`
- Distance matrix: `data/processed/analysis/public/location_distance_matrix.csv`
- Class schedule GIS: `data/processed/analysis/public/class_schedule_gis.csv`
- Public same-day transition feasibility: `data/processed/analysis/public/transition_feasibility_public.csv`
- Public same-day location transition feasibility: `data/processed/analysis/public/location_transition_feasibility_public.csv`
- Public location mobility role metrics: `data/processed/analysis/public/location_mobility_role_metrics.csv`
- Private participant itinerary: `data/processed/analysis/private/participant_itinerary_gis_private.csv`
- Time slider map: `reports/analysis/yeonhui_yoga_week_time_slider_map.html`
- Transition map: `reports/analysis/yeonhui_yoga_week_transition_map.html`
- Map-based space-time cube: `reports/analysis/yeonhui_yoga_week_space_time_cube.html`

## Data Summary

- Location nodes: 13
- Distance matrix rows: 169
- Class schedule rows: 261
- Parsed class schedule rows: 261
- Class schedule rows needing review: 0
- Public same-day class/session transition rows: 167
- Public same-day location transition rows: 74
- Public location mobility role rows: 13
- Time slider map generated: True
- Transition map generated: True
- Map-based space-time cube generated: True

## Feasibility Status Counts

| feasibility_status | feasibility_label | transition_count |
| --- | --- | --- |
| comfortable | 여유 있음 | 209 |
| overlap | 시간 겹침 | 12 |
| tight | 빠듯함 | 8 |
| difficult | 시간표상 어려움 | 4 |

## Nearest Venue Pairs

| origin_display_name | destination_display_name | walk_distance_m | walk_minutes | walk_method |
| --- | --- | --- | --- | --- |
| 시이작 | 비전스트롤 | 42.18 | 0.53 | osmnx_walk_network |
| 비전스트롤 | 시이작 | 42.18 | 0.53 | osmnx_walk_network |
| 비전스트롤 | 연희정음 | 118.51 | 1.48 | osmnx_walk_network |
| 연희정음 | 비전스트롤 | 118.51 | 1.48 | osmnx_walk_network |
| 연희정음 | 시이작 | 160.69 | 2.01 | osmnx_walk_network |
| 시이작 | 연희정음 | 160.69 | 2.01 | osmnx_walk_network |
| 데이스타콜라보 | 빅블루요가 | 162.02 | 2.03 | osmnx_walk_network |
| 빅블루요가 | 데이스타콜라보 | 162.02 | 2.03 | osmnx_walk_network |

## Farthest Venue Pairs

| origin_display_name | destination_display_name | walk_distance_m | walk_minutes | walk_method |
| --- | --- | --- | --- | --- |
| 너울너울 | 숨 명상센터 | 2596.15 | 32.45 | osmnx_walk_network |
| 숨 명상센터 | 너울너울 | 2596.15 | 32.45 | osmnx_walk_network |
| 마인드플로우 | 너울너울 | 2424.94 | 30.31 | osmnx_walk_network |
| 너울너울 | 마인드플로우 | 2424.94 | 30.31 | osmnx_walk_network |
| 마인드플로우 | 연남장 | 1753.99 | 21.92 | osmnx_walk_network |
| 연남장 | 마인드플로우 | 1753.99 | 21.92 | osmnx_walk_network |
| 너울너울 | 데이스타콜라보 | 1703.74 | 21.3 | osmnx_walk_network |
| 데이스타콜라보 | 너울너울 | 1703.74 | 21.3 | osmnx_walk_network |

## Busiest Location Transition Candidates

| origin_display_name | destination_display_name | feasibility_label | transition_count | avg_gap_minutes | avg_walk_minutes |
| --- | --- | --- | --- | --- | --- |
| 연남장 | 연남장 | 여유 있음 | 39 | 98.46 | 0.0 |
| 연희정음 | 연남장 | 여유 있음 | 13 | 163.08 | 5.02 |
| 마이트리 | 마이트리 | 여유 있음 | 11 | 71.82 | 0.0 |
| 빅블루요가 | 마이트리 | 여유 있음 | 7 | 180.0 | 6.08 |
| 시이작 | 마인드플로우 | 여유 있음 | 5 | 249.0 | 16.8 |
| 연남장 | 바운드하우스 | 여유 있음 | 5 | 132.0 | 12.14 |
| 마이트리 | 시이작 | 여유 있음 | 5 | 297.0 | 4.33 |
| 무릉 | 연남장 | 여유 있음 | 5 | 174.0 | 10.03 |
| 연남장 | 연희정음 | 여유 있음 | 5 | 60.0 | 5.02 |
| 무릉 | 시이작 | 여유 있음 | 4 | 157.5 | 3.16 |
| 연남장 | 마이트리 | 여유 있음 | 4 | 90.0 | 5.31 |
| 마인드플로우 | 무릉 | 여유 있음 | 4 | 127.5 | 16.66 |

## Location Mobility Roles

This table helps read which places behave like local movement hubs in the reservation timetable. It is not a ranking of venue quality. It counts how often a place appears in adjacent same-day booking flows.

| display_name | transfer_hub_score | incoming_transition_count | outgoing_transition_count | same_location_transition_count | comfortable_transition_count | tight_transition_count |
| --- | --- | --- | --- | --- | --- | --- |
| 연남장 | 80.0 | 75 | 68 | 42 | 93 | 3 |
| 마이트리 | 50.0 | 42 | 26 | 12 | 50 | 5 |
| 마인드플로우 | 42.5 | 21 | 29 | 5 | 34 | 6 |
| 시이작 | 42.0 | 25 | 23 | 4 | 42 | 0 |
| 빅블루요가 | 35.5 | 19 | 24 | 5 | 35 | 0 |
| 바운드하우스 | 29.0 | 20 | 15 | 4 | 28 | 0 |
| 연희정음 | 25.0 | 12 | 16 | 2 | 24 | 0 |
| 무릉 | 21.0 | 8 | 13 | 0 | 19 | 2 |
| 너울너울 | 11.0 | 4 | 7 | 0 | 11 | 0 |
| 데이스타콜라보 | 8.0 | 4 | 4 | 0 | 8 | 0 |
| 숨 명상센터 | 8.0 | 3 | 5 | 0 | 7 | 0 |
| 비전스트롤 | 3.0 | 0 | 3 | 0 | 3 | 0 |

## Busiest Class Transition Candidates

| origin_class_title_base | destination_class_title_base | feasibility_label | transition_count | avg_gap_minutes | avg_walk_minutes |
| --- | --- | --- | --- | --- | --- |
| [연남장/커뮤니티허브] 매트 필라테스로 부상 없는 몸 만들기 | [연남장/커뮤니티허브] 바람과 땀, 그리고 알아차림 - 봄날의 역동적 명상 | 여유 있음 | 5 | 60.0 | 0.0 |
| [연남장/커뮤니티허브] 마인드풀니스 테라피 요가 (아카샤(은채)) | [연남장/커뮤니티허브]Forrestyoga의 움직임을 기반으로 내몸의 바른 사용법 찾아가기 | 여유 있음 | 4 | 30.0 | 0.0 |
| [연남장/커뮤니티허브] 비트박스 공연과 호흡소리로 몰입하는 요가 | [연남장/커뮤니티허브] 마인드풀니스 테라피 요가 (아카샤(은채)) | 여유 있음 | 4 | 30.0 | 0.0 |
| [마인드플로우] 비기너요가 | [마이트리] 테라피 | 빠듯함 | 3 | 20.0 | 18.35 |
| [마이트리/연희스페셜] Root to Rise (Vinyasa) | [마이트리/연희스페셜] 꽁샘과 도전하는 에카파다라자카포타 | 여유 있음 | 3 | 30.0 | 0.0 |
| [빅블루요가/연희스페셜] 정렬 인텐시브: 견갑골 집중 | [마이트리/연희스페셜] 올레벨 빈야사 | 여유 있음 | 3 | 60.0 | 6.08 |
| [연남장/커뮤니티허브] 딥어웨이크 하타 | [마이트리] 얼라인 요가 | 여유 있음 | 3 | 60.0 | 5.31 |
| [연남장/커뮤니티허브] 바람과 땀, 그리고 알아차림 - 봄날의 역동적 명상 | [연남장/커뮤니티허브] 하루를 내려놓는 요가와 바이올린 | 여유 있음 | 3 | 60.0 | 0.0 |
| [연남장/커뮤니티허브]Forrestyoga의 움직임을 기반으로 내몸의 바른 사용법 찾아가기 | [마인드플로우/연희스페셜] 몸으로 하는 선셋 자애 명상 | 빠듯함 | 3 | 30.0 | 21.92 |
| [연희정음/랜드마크] 빅블루의 호흡 회복 요가 | [연남장/커뮤니티허브] 마인드풀니스 테라피 요가 (아카샤(은채)) | 여유 있음 | 3 | 240.0 | 5.02 |
| [연희정음/랜드마크]인요가와 저널링 with 프라우카 | [연남장/커뮤니티허브]Forrestyoga의 움직임을 기반으로 내몸의 바른 사용법 찾아가기 | 여유 있음 | 3 | 50.0 | 5.02 |
| [연남장/커뮤니티허브]처음이라 좋은 아쉬탕가 with 베지어트 | [연남장/커뮤니티허브] 마인드풀니스 테라피 요가 (아카샤(은채)) | 여유 있음 | 3 | 120.0 | 0.0 |

## Interpretation Notes

- `comfortable` means the class gap is at least estimated walk time plus 10 minutes.
- `tight` means walking may be possible, but there is less than 10 minutes of buffer.
- `difficult` means the estimated walk time is longer than the available gap.
- `overlap` means the next class starts before the previous class ends.
- Public transition tables aggregate same-day adjacent reservations only, so multi-day reservation sequences do not distort movement interpretation.
- This is an operational planning layer for next-year scheduling, not a disclosure of individual participant movement.
- The space-time cube is now rendered on top of a Leaflet map. Venue position remains the x/y map coordinate, and each vertical tower uses height as the time axis.
