# YouTube Collection Report

Generated: 2026-05-16T16:27:01+09:00

## Purpose

Collect public YouTube search result metadata for 2026 Yeonhui Yoga Week viral/sns analysis.

## Inputs

- API: YouTube Data API v3
- Search method: `search.list`
- Video details method: `videos.list`
- Queries: 30
- Published after: 2026-01-01T00:00:00Z
- Published before: 

## Outputs

- Raw CSV: `data\raw\external_web\youtube_mentions_raw.csv`
- Total search result rows saved: 85
- Unique videos: 68
- Unique channels: 32

## API Use

- Search calls: 30
- Video detail calls: 2
- Channel detail calls: 1
- Estimated quota units: 3003

## Query Counts

| query | saved_rows |
|---|---:|
| 연희요가위크 | 3 |
| 연희 요가 위크 | 3 |
| 2026 연희요가위크 | 3 |
| 2026 연희 요가 위크 | 3 |
| 연희요가축제 | 1 |
| 연희 요가 축제 | 1 |
| 연희동 요가 위크 | 6 |
| 연희동 요가 축제 | 9 |
| 오붓 연희요가위크 | 0 |
| 오붓 요가위크 | 3 |
| 빅블루요가 연희요가위크 | 0 |
| 마이트리 연희요가위크 | 0 |
| 마인드플로우 연희요가위크 | 0 |
| 시이작 연희요가위크 | 0 |
| 연희정음 연희요가위크 | 0 |
| 연남장 연희요가위크 | 0 |
| 대저택프라이빗 연희요가위크 | 0 |
| 바운드하우스 연희요가위크 | 0 |
| 너울너울 연희요가위크 | 1 |
| 무릉 연희요가위크 | 0 |
| 숨명상센터 연희요가위크 | 0 |
| 숨 명상센터 연희요가위크 | 0 |
| 비전스트롤 연희요가위크 | 0 |
| 파츄코파라다이스 연희요가위크 | 0 |
| 궁동산 연희요가위크 | 0 |
| 궁둥산 연희요가위크 | 0 |
| 연희요가위크 핸드팬 | 1 |
| 연희요가위크 너울너울 | 1 |
| 빅블루요가 정렬 에센스 | 0 |
| 마인드플로우 빈야사요가 | 50 |

## Notes

- This file records public video metadata and links only.
- API keys are read from `.secrets/youtube-api-key.txt`.
- YouTube search results are not a complete archive of all platform activity.
- Public reporting should avoid treating individual channels as evaluation targets.
