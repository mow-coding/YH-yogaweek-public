# 패키지 설치 및 검증 로그

작성일: 2026-05-09

이 문서는 분석 환경에 어떤 패키지를 설치했고, 어떤 방식으로 검증했는지 남기는 기록이다.

## 설치 목적

오붓 리뷰 화면은 마우스 드래그로 텍스트 복사가 되지 않으므로, 리뷰 스크린샷을 OCR로 읽어 텍스트 데이터로 변환해야 한다.

또한 리뷰와 SNS 후기를 주제별로 묶기 위해 토픽 모델링 도구가 필요하다.

## 설치된 패키지

| 패키지 | 버전 | 용도 |
|---|---:|---|
| easyocr | 1.7.2 | 리뷰 스크린샷 OCR 후보 |
| paddleocr | 3.5.0 | 리뷰 스크린샷 OCR 후보 |
| paddlepaddle | 3.3.1 | PaddleOCR 실행 엔진 |
| bertopic | 0.17.4 | 리뷰/SNS 토픽 모델링 |
| sentence-transformers | 5.4.1 | 문장 임베딩, 의미 기반 유사도 |
| torch | 2.11.0+cpu | EasyOCR, sentence-transformers 실행 기반 |
| torchvision | 0.26.0+cpu | EasyOCR 이미지 처리 기반 |
| hdbscan | 0.8.42 | BERTopic 내부 군집화 |
| umap-learn | 0.5.12 | BERTopic 내부 차원 축소 |
| rapidfuzz | 3.14.5 | OCR 수업명과 표준 수업명 유사도 매칭 |
| openai | 2.36.0 | 이미지 기반 OCR 검수와 구조화 추출 후보 |
| google-cloud-vision | 3.14.0 | Google Cloud Vision OCR 후보 |
| google-cloud-documentai | 3.14.0 | Google Document AI OCR 후보 |
| pydantic | 2.13.4 | AI 추출 결과 JSON 구조 검증 |

## 검증 결과

다음 import 검증을 통과했다.

```text
easyocr: OK 1.7.2
bertopic: OK 0.17.4
sentence_transformers: OK 5.4.1
paddleocr: OK 3.5.0
paddle: OK 3.3.1
torch: OK 2.11.0+cpu
torchvision: OK 0.26.0+cpu
rapidfuzz: OK 3.14.5
openai: OK 2.36.0
google.cloud.vision: OK
google.cloud.documentai: OK
pydantic: OK 2.13.4
```

또한 `python -m pip check` 결과는 다음과 같다.

```text
No broken requirements found.
```

## 운영 메모

현재 설치된 PyTorch는 CPU 버전이다.

초기 분석과 수십~수백 장 수준의 리뷰 스크린샷 OCR 테스트에는 CPU 버전으로 시작한다.

나중에 리뷰 스크린샷이 매우 많거나 OCR 품질이 병목이 되면 Google Cloud Vision, Google Document AI, OpenAI Vision을 이용한 외부 API 검수 파이프라인을 검토한다.

외부 API 사용에는 API 키 또는 클라우드 인증 정보가 필요하며, 원본 리뷰 이미지가 외부 서비스로 전송될 수 있으므로 개인정보와 공유 범위를 먼저 확인한다.
