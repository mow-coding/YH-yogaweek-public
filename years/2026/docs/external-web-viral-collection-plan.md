# 외부 웹 바이럴 수집 계획

작성일: 2026-05-16

## 현재 결정

1차 외부 바이럴 수집 범위는 네이버 블로그와 유튜브로 제한한다.

인스타그램은 1차 자동 수집 범위에서 제외한다. 공식 API로 공개 검색 결과를 안정적으로 가져오기 어렵고, 비공개 계정, 스토리, 로그인 우회, 계정 추적 문제가 생기기 쉽기 때문이다.

## 수집 목적

목적은 참가자 개인을 평가하거나 추적하는 것이 아니다.

목적은 2026 연희 요가 위크가 오붓 플랫폼 밖에서 어떻게 언급되었는지 확인하는 것이다.

볼 질문은 다음과 같다.

- 외부 웹에서 연희요가위크가 얼마나 언급되었는가?
- 어떤 요가원, 수업, 장소가 자주 언급되었는가?
- 네이버 블로그와 유튜브 반응은 예약, 리뷰, GIS 지표와 어떤 관계가 있는가?
- 나중에 Hype와 별도로 비교할 `Viral signal` 또는 `외부 확산 신호`를 만들 수 있는가?

## 현재 수집 방식

### 네이버 블로그

- 공식 네이버 검색 API의 블로그 검색 결과를 사용한다.
- 원본 수집 파일은 `data/raw/external_web/naver_blog_mentions_raw.csv`다.
- 수집 필드는 검색어, 제목, 링크, 요약, 블로그명, 블로그 링크, 작성일, 수집 시각이다.
- 네이버 API는 검색 결과 메타데이터와 요약만 제공하므로, confirmed 블로그에 한해 공개 페이지 본문을 별도로 수집한다.
- 본문 수집은 로그인, 비공개 글 접근, 우회 수집 없이 공개 페이지에서 접근 가능한 본문만 대상으로 한다.
- 본문 원본 파일은 `data/raw/external_web/naver_blog_bodies_raw.csv`이며, 개인 경험 서술이 포함될 수 있으므로 public 산출물로 내보내지 않는다.

### 유튜브

- 공식 YouTube Data API v3를 사용한다.
- 검색에는 `search.list`를 사용한다.
- 영상 상세 정보에는 `videos.list`를 사용한다.
- 채널 공개 메타데이터에는 `channels.list`를 사용한다.
- 원본 수집 파일은 `data/raw/external_web/youtube_mentions_raw.csv`다.
- 수집 필드는 영상 링크, 제목, 설명, 채널명, 채널 ID, 게시일, 조회수, 좋아요 수, 댓글 수, 공개 채널 메타데이터다.

## 출처 식별자 처리 원칙

raw와 interim 단계에서는 공개 출처 확인을 위해 다음 정보를 보존한다.

- 네이버 블로그명
- 네이버 블로그 링크
- 유튜브 채널명
- 유튜브 채널 ID
- 유튜브 영상 URL

다만 이것을 개인 실명 추정이나 플랫폼 간 동일인 추적에 사용하지 않는다.

public 산출물에서는 기본적으로 개인 출처명을 익명화하거나 집계한다.

예를 들어 public 표에서는 다음처럼 바꿀 수 있다.

```text
source_public_name -> external_source_0001
source_profile_url -> 비공개 또는 내부 검증용으로만 유지
```

## 검수 큐

네이버와 유튜브 원본 수집 파일을 합쳐 내부 검수용 큐를 만든다.

파일:

```text
data/interim/external_web/viral_mentions_review_queue.csv
```

이 큐는 중복 링크를 정리하고, 다음 컬럼을 포함한다.

- 플랫폼
- 원문 링크
- 공개 출처명
- 공개 출처 ID
- 제목
- 요약/설명
- 검색에 걸린 키워드
- 행사 키워드 포함 여부
- 자동 매칭된 요가원/장소명
- 수동 관련성 검토 필요 여부

이 큐는 public 공유용이 아니라 내부 검수용이다.

## 현재 수집 결과

### 네이버 블로그

- 검색어 파일: `references/naver-blog-viral-queries-expanded.txt`
- 검색어 수: 60
- 검색 결과 행: 2415
- 고유 링크: 1075
- 수집 리포트: `reports/external_web/naver_blog_collection_report.md`

### 유튜브

- 검색어 파일: `references/external-web-viral-queries-core.txt`
- 검색어 수: 30
- 검색 결과 행: 86
- 고유 영상: 69
- 고유 채널: 34
- 추정 quota 사용량: 3003 units
- 수집 리포트: `reports/external_web/youtube_collection_report.md`

### 통합 검수 큐

- 고유 후보 mention: 1143
- 수동 관련성 검토 필요: 1082
- 리포트: `reports/external_web/viral_mentions_review_queue_report.md`

수동 관련성 검토 필요 행이 많은 이유는 의도적인 보수 규칙 때문이다.
검색어를 넓게 잡아 많이 수집하되, 제목/요약/출처명에서 `연희요가위크` 계열 행사 키워드가 직접 확인되지 않는 행은 사람이 검토하도록 남긴다.
요가원명이나 장소명만 등장하는 경우는 다른 맥락의 글일 수 있으므로 자동 관련 확정으로 보지 않는다.

## 완료된 후속 처리

1. `filter_yeonhui_yoga_week_mentions.py`로 `연희요가위크` 직접 언급 후보를 1차 confirmed로 분리했다.
2. confirmed 후보에는 public 익명화 ID를 붙였다.
3. confirmed 후보를 기준으로 플랫폼별 언급 수, 유튜브 조회수 proxy, 요가원/장소명 자동 매칭 요약을 계산했다.
4. 네이버 블로그 confirmed 58건은 공개 본문까지 수집했다.
5. 본문 기준 행사명 확인, 노이즈 위험, 테마, 후기 깊이, 감정 강도, 혼합글 위험도까지 별도 feature로 만들었다.
6. 기존 Hype 지표와 합산하지 않고, 별도 Viral 지표를 나란히 비교한다.

## 1차 엄격 필터 결과

필터 기준은 다음과 같다.

- 검색어 자체는 확인 증거로 쓰지 않는다.
- 제목 또는 요약/설명에 `연희요가위크`가 직접 등장해야 한다.
- 띄어쓰기 변형인 `연희 요가 위크`는 공백 정규화 후 같은 행사명으로 본다.
- 게시일은 내부 회의가 시작된 2026년 2월 이후여야 한다.
- 요가원명이나 장소명만 나온 후보는 자동 confirmed로 보지 않는다.

결과:

- 입력 후보 mention: 1143
- confirmed 행사 mention: 58
- confirmed 네이버 블로그: 56
- confirmed 유튜브 영상: 2
- public 익명화 표: `data/processed/analysis/public/yeonhui_yoga_week_viral_mentions_public.csv`
- 플랫폼 요약: `data/processed/analysis/public/yeonhui_yoga_week_viral_platform_summary.csv`
- 요가원/장소명 요약: `data/processed/analysis/public/yeonhui_yoga_week_viral_studio_summary.csv`
- 필터 리포트: `reports/external_web/yeonhui_yoga_week_mention_filter_report.md`

## 네이버 블로그 본문 검수 결과

- confirmed 네이버 블로그 본문 수집: 56/56 성공
- 빈 본문: 0
- 수집 실패: 0
- 총 본문 글자 수: 80776자
- 본문에 `연희요가위크` 직접 확인: 54건
- 제목/요약은 맞지만 본문에서 행사명이 확인되지 않은 노이즈 위험 후보: 2건
- 본문 기준 strong/basic confirmed: 54건
- 본문 기준 수동 확인 권장: 5건
- 본문 기준 high-depth 후기/맥락 글: 30건
- 본문 기준 positive/very positive 톤 글: 47건

본문 기반 해석용 public 산출물:

```text
data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_theme_summary.csv
data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_studio_summary.csv
data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_deep_features_public.csv
data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_post_type_summary.csv
data/processed/analysis/public/yeonhui_yoga_week_naver_blog_body_quality_summary.csv
reports/external_web/naver_blog_body_deep_feature_report.md
```

## Viral과 Hype 분리

Viral과 Hype는 별도 축으로 둔다.

- Hype: 예약, 취소, 리뷰, 만족도, 재방문, 결제 반응처럼 행사 내부 참여/경험에서 나온 신호
- Viral: 네이버 블로그, 유튜브처럼 행사 밖 공개 웹에서 확인되는 확산 신호

따라서 Viral 지표는 기존 `studio_hype_metrics.csv`에 합산하지 않는다.
대신 별도 파일로 관리한다.

파일:

```text
data/processed/analysis/public/yeonhui_yoga_week_viral_overall_summary.csv
data/processed/analysis/public/yeonhui_yoga_week_viral_platform_metrics.csv
data/processed/analysis/public/yeonhui_yoga_week_viral_studio_metrics.csv
data/processed/analysis/public/yeonhui_yoga_week_viral_unmatched_mentions_public.csv
reports/external_web/yeonhui_yoga_week_viral_analysis_report.md
```

현재 별도 Viral 지표 요약:

- confirmed 외부 언급: 60개
- 익명 출처: 33개
- 네이버 블로그: 56개
- 유튜브 영상: 2개
- 유튜브 조회수 proxy: 1808
- 스튜디오/장소 매칭 지표 행: 10개
- 스튜디오/장소 미매칭 confirmed mention: 15개

## 참고 공식 문서

- 네이버 블로그 검색 API: https://developers.naver.com/docs/serviceapi/search/blog/blog.md
- YouTube Data API `search.list`: https://developers.google.com/youtube/v3/docs/search/list
- YouTube Data API quota calculator: https://developers.google.com/youtube/v3/determine_quota_cost
- YouTube Data API channels resource: https://developers.google.com/youtube/v3/docs/channels
- Google Cloud API key 관리: https://cloud.google.com/docs/authentication/api-keys
