# Public Release Quality Gate Report

- status: PASS
- generated_at: 2026-05-25T18:17:02
- public_root: `C:\Users\mylifeisbusy\Documents\dev\YH-yogaweek`

## Blockers
- 없음

## Warnings
- 없음

## Passed Checks
- data\processed\onstudio\public\onstudio_classes_2026_yeonhui_yoga_week.csv rows == 125 (actual 125)
- data\processed\onstudio\public\onstudio_reservation_2026_yeonhui_yoga_week_deidentified.csv rows == 1611 (actual 1611)
- data\processed\onstudio\public\onstudio_cancel_2026_yeonhui_yoga_week_deidentified.csv rows == 1048 (actual 1048)
- data\processed\obud_reviews\public\obud_reviews_deidentified.csv rows == 96 (actual 96)
- data\processed\obud_reviews\private\obud_reviews_extracted_private.csv rows == 96 (actual 96)
- data\processed\analysis\public\studio_hype_metrics.csv rows == 12 (actual 12)
- data\processed\analysis\public\class_hype_metrics.csv rows == 83 (actual 83)
- data\processed\analysis\public\studio_capacity_hype_metrics.csv rows == 12 (actual 12)
- data\processed\analysis\public\class_capacity_hype_metrics.csv rows == 83 (actual 83)
- data\processed\analysis\public\obud_settlement_basis_by_class.csv rows == 108 (actual 108)
- data\processed\analysis\public\obud_settlement_basis_by_owner_month.csv rows == 19 (actual 19)
- data\processed\analysis\public\location_nodes.csv rows == 13 (actual 13)
- data\processed\analysis\public\location_distance_matrix.csv rows == 169 (actual 169)
- data\processed\analysis\public\class_location_evidence_public.csv rows == 83 (actual 83)
- studio_hype_metrics.studio_key has no non-canonical keys ['대저택 프라이빗', '비전스트롤', '숨 명상센터']
- class_hype_metrics.studio_key has no non-canonical keys ['대저택 프라이빗', '비전스트롤', '숨 명상센터']
- studio_capacity_hype_metrics.studio_key has no non-canonical keys ['대저택 프라이빗', '비전스트롤', '숨 명상센터']
- class_capacity_hype_metrics.studio_key has no non-canonical keys ['대저택 프라이빗', '비전스트롤', '숨 명상센터']
- obud_settlement_basis_by_class.studio_key has no non-canonical keys ['대저택 프라이빗', '비전스트롤', '숨 명상센터']
- viral_studio_metrics.matched_studio_term has no non-canonical keys ['대저택 프라이빗', '비전스트롤', '숨 명상센터']
- studio_hype_metrics unique on ['studio_key'] (duplicates 0)
- class_hype_metrics unique on ['studio_key', 'class_base_key'] (duplicates 0)
- class_capacity_hype_metrics unique on ['studio_key', 'class_base_key'] (duplicates 0)
- obud_settlement_basis_by_class unique on ['service_month', 'settlement_owner_key', 'studio_key', 'class_base_key'] (duplicates 0)
- obud_settlement_basis_by_owner_month unique on ['service_month', 'settlement_owner_key'] (duplicates 0)
- obud_settlement_basis_by_class excludes deprecated amount-estimate columns
- obud_settlement_basis_by_owner_month excludes deprecated amount-estimate columns
- Bigblue settlement owner exists for 2026-04
- Bigblue 2026-04 settlement owner includes Yeonhui Jeongeum-hosted Bigblue class
- review_0044 exists in public review table
- review_0044 matched to [연희정음|랜드마크] 빅블루의 호흡 회복 요가
- public review needs_review == 0 (actual 0)
- private class_match_needs_review == 0 (actual 0)
- no long OCR title was under-matched to a short generic class candidate ([])
- capacity_match_status needs_review == 0 (actual 0)
- active GIS tables do not contain obsolete Gungdongsan location rows
- public text scan found no forbidden patterns across 152 files
- markdown table structure checked (81 table blocks)
- public integrated report has exactly one H1 (actual 1)
- GitHub contributors == ['mow-coding'] (actual ['mow-coding'])

## Notes
- 이 품질 게이트는 공개 레포에 올리기 전 표준화, 중복, 리뷰 매칭, 정원 매칭, 민감 문자열, HTML/Markdown 표시 품질을 확인한다.
- 이번 감사에서는 기존 계획상 예상했던 84개 수업 행 외에 OCR 별칭 문제까지 추가로 정정되어 최종 `class_hype_metrics`와 `class_capacity_hype_metrics`는 83행을 기준으로 검증한다.
- 이 검사는 보안 삭제 도구가 아니라 공개 패키지 품질 검사다. 실제 secret 노출이 발견되면 key 폐기/회전과 레포 재생성이 우선이다.
