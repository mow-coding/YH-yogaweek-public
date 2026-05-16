# Capacity + Hype Analysis Report

작성일: 2026-05-17

## 요약

- Hype 수업 행: 83
- ON STUDIO 캘린더 정원 수업 그룹: 84
- 정원 자동 매칭 성공: 83
- 같은 요가원 후보 없음: 0
- 수동 검토 필요: 0

## 반응 프로필 세그먼트

- expand_or_repeat_candidate: 31
- small_capacity_or_niche_strength: 23
- steady_middle: 22
- demand_development_candidate: 7

## 확장/반복 후보 상위

- [연남장|커뮤니티허브] 하루를 내려놓는 요가와 바이올린: weighted_fill_rate=1.00, reservation_hype=95.18, review_hype=20.48, sessions=1
- [연남장|커뮤니티허브] 짠짠! 막걸리요가! with 복순도가: weighted_fill_rate=1.00, reservation_hype=92.77, review_hype=20.48, sessions=1
- [대저택프라이빗] Deep Rest 인요가 & 핸드팬 사운드: weighted_fill_rate=1.00, reservation_hype=92.77, review_hype=54.52, sessions=3
- [연남장|커뮤니티허브] 처음이라 좋은 아쉬탕가 with 베지어트: weighted_fill_rate=1.00, reservation_hype=85.54, review_hype=94.88, sessions=1
- [연남장|커뮤니티허브] 마인드풀니스 테라피 요가 (아카샤(은채)): weighted_fill_rate=1.00, reservation_hype=85.54, review_hype=20.48, sessions=1
- [마이트리|연희스페셜] 꽁샘과 도전하는 에카파다라자카포타: weighted_fill_rate=1.00, reservation_hype=85.54, review_hype=20.48, sessions=1
- [연남장|커뮤니티허브] Forrestyoga의 움직임을 기반으로 내몸의 바른 사용법 찾아가기: weighted_fill_rate=1.00, reservation_hype=81.93, review_hype=51.81, sessions=1
- [연남장|커뮤니티허브] 딥어웨이크 하타: weighted_fill_rate=1.00, reservation_hype=77.11, review_hype=51.81, sessions=1
- [마이트리|연희스페셜] Root to Rise (Vinyasa): weighted_fill_rate=1.00, reservation_hype=77.11, review_hype=20.48, sessions=1
- [연희정음|랜드마크] 인요가와 저널링 with 프라우카: weighted_fill_rate=1.00, reservation_hype=73.49, review_hype=76.21, sessions=1
- [빅블루요가] 후굴의 정렬: weighted_fill_rate=1.00, reservation_hype=55.42, review_hype=94.57, sessions=1
- [대저택프라이빗] 단단하게 뿌리 내리며 자유롭게 흐르는 빈야사: weighted_fill_rate=1.00, reservation_hype=45.18, review_hype=70.78, sessions=1
- [빅블루요가|연희스페셜] 정렬 인텐시브: 고관절 집중: weighted_fill_rate=1.00, reservation_hype=45.18, review_hype=70.78, sessions=1
- [빅블루요가|연희스페셜] 호흡어드밴스 : 숨의 리듬 익히기: weighted_fill_rate=1.00, reservation_hype=45.18, review_hype=72.59, sessions=1
- [마이트리|연희스페셜] 올레벨 빈야사: weighted_fill_rate=1.00, reservation_hype=37.35, review_hype=90.36, sessions=1

## 해석 기준

- `expand_or_repeat_candidate`: Hype가 높고 정원 대비 채움률도 높아 다음 회차 확장/반복 후보.
- `message_or_schedule_review`: Hype는 있으나 채움률이 낮아 시간대, 장소, 홍보 문구, 정원 설정을 점검.
- `small_capacity_or_niche_strength`: 채움률은 높지만 Hype가 낮거나 중간이라 소규모 강점/니치 수업 후보.
- `demand_development_candidate`: 채움률이 낮아 수요 개발 또는 기획 재검토 후보.

## 산출물

- `data\processed\analysis\public\class_capacity_hype_metrics.csv`
- `data\processed\analysis\public\studio_capacity_hype_metrics.csv`

## 한계

- 정원은 ON STUDIO 캘린더 복사본 기준이며, 현장 노쇼나 대기자 흐름은 반영하지 못한다.
- 수업명 매칭은 정규화 키와 RapidFuzz를 사용했으며, 낮은 점수는 수동 검토 대상으로 남긴다.
- 채움률이 높다는 사실은 수요 신호이지만, 수업 품질이나 수익성을 단독으로 증명하지 않는다.
