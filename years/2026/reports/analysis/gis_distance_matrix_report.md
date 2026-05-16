# GIS Distance Matrix Report

Generated: 2026-05-17

## Purpose

This report records the venue-to-venue distance layer for the 2026 Yeonhui Yoga Week GIS analysis.

## Method

- Location nodes: 13
- Distance matrix rows: 169
- Walking speed assumption: 4.8 km/h
- Fallback route factor: straight-line distance x 1.3
- OSMnx status: `success:graph_radius_m=2694:nodes=15256:edges=42270`
- Rows using OSMnx walking network: 169
- Location nodes needing manual verification: 0

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
| 마이트리 | 연희정음 | 185.83 | 2.32 | osmnx_walk_network |
| 연희정음 | 마이트리 | 185.83 | 2.32 | osmnx_walk_network |

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
| 너울너울 | 빅블루요가 | 1631.8 | 20.4 | osmnx_walk_network |
| 빅블루요가 | 너울너울 | 1631.8 | 20.4 | osmnx_walk_network |

## Limits

- OSMnx distances depend on current OpenStreetMap coverage and the downloaded walking network.
- If OSMnx is unavailable or a path cannot be found, `walk_distance_m` uses the documented straight-line fallback.
- No active location nodes currently require manual coordinate verification.
