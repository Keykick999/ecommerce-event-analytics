# 고가용성 이커머스 이벤트 로그 파이프라인 및 이상 탐지 시스템

대규모 트래픽 환경에서 발생하는 사용자 행동 로그를 실시간으로 수집·분석하고, 시스템 장애에 능동적으로 대응하기 위한 이벤트 로그 파이프라인입니다. 성능 최적화, 데이터 정합성, 운영 관측성(Observability)을 중심으로 설계했습니다.

---

## 빠른 시작
Docker와 Docker Compose가 설치되어 있으면 아래 명령어 하나로 전체 스택을 올릴 수 있습니다.

```bash
docker-compose up -d --build
```
실행 후 `http://localhost:8501`에 접속하면 통합 대시보드를 확인할 수 있습니다.

---

## 시스템 설계

### 이벤트 설계 의도
이벤트 생성기는 단순히 랜덤 데이터를 만드는 것이 아니라, 실제 이커머스 서비스의 비즈니스 흐름을 반영하도록 만들었습니다. page_view → search → purchase로 이어지는 전환 과정을 추적하고, error 이벤트에는 Trace ID를 붙여 장애 전후의 사용자 행동을 end-to-end로 파악할 수 있게 했습니다.

### 저장소 및 스키마 설계
주 저장소로 PostgreSQL을 선택한 이유는 두 가지입니다. ACID 트랜잭션으로 정합성을 보장할 수 있고, JSONB 타입을 통해 스키마 변경 없이도 새로운 로그 속성을 유연하게 수용할 수 있어서입니다.

스키마는 하이브리드 방식으로 설계했습니다. Timestamp, Trace ID, Severity처럼 쿼리 조건으로 자주 쓰이는 필드는 컬럼으로 정규화해 인덱싱 효율을 높이고, 가변적인 컨텍스트 데이터는 JSONB 메타데이터로 처리했습니다. 또한 로그 폭증이 비즈니스 쿼리 성능에 영향을 주지 않도록 events와 error_logs 테이블을 물리적으로 분리했습니다.

---

## 구현하면서 고민한 것들

### "실시간 집계 성능과 정합성을 어떻게 같이 잡을까"
초당 수만 건의 로그가 인입되는 환경에서 매번 COUNT(*) 쿼리를 날리는 건 DB에 큰 부담입니다. 두 가지 전략으로 이 문제를 풀었습니다.

1. UPSERT 기반의 Summary Table을 도입했습니다. 로그가 들어오는 즉시 1분 단위 요약 테이블(error_metrics_summary)을 갱신해, 대시보드 조회 시 수백만 건을 스캔하는 대신 수십 건의 요약 데이터만으로 실시간 트렌드를 보여줄 수 있게 했습니다.
2. 이상 탐지를 이중 구조로 나눴습니다. API 레이어에서는 임계치 기반으로 즉시 서킷 브레이킹을 하고, 워커 레이어에서는 통계적 베이스라인을 분석하는 방식으로, 감지 속도와 정확도 사이의 균형을 맞췄습니다.

---

## AWS 기반 고가용성 아키텍처 (선택 B)
현업에서 이 시스템을 운영한다면 아래와 같은 클라우드 네이티브 구성으로 확장할 것입니다.

| 단계 | 서비스 | 역할 |
| :--- | :--- | :--- |
| Ingestion | Amazon Kinesis Data Streams | 트래픽 폭증 시 완충 버퍼 (Backpressure 관리) |
| Processing | AWS Lambda | 데이터 정제 및 PII 마스킹 (Auto-scaling 레이어) |
| Storage (Hot) | Amazon RDS for PostgreSQL | 활성 로그 및 요약 데이터 저장 |
| Storage (Cold) | Amazon S3 + Athena | Raw 로그 장기 보관 및 시계열 분석용 데이터 레이크 |
| Monitoring | CloudWatch + Managed Grafana | 실시간 지표 수집 및 시각화 전용 관제 시스템 |

---

## Kubernetes 리소스 설계 (선택 A)
이벤트 생성기 앱을 클러스터에 배포하기 위해 세 가지 리소스를 작성했습니다.

- Deployment: 파드의 desired state를 정의하고, Rolling Update를 통해 무중단 배포를 관리합니다. replicas 설정으로 특정 노드 장애 시에도 이벤트 생성이 멈추지 않는 자가 치유 능력을 확보했습니다.
- ConfigMap: DB 접속 정보 등 환경 설정을 애플리케이션 이미지와 분리해, 코드 수정 없이 개발·검증·운영 환경 간 이식이 가능하도록 했습니다.
- Service: 여러 파드에 대한 단일 진입점을 제공하며, 향후 Prometheus 등 모니터링 시스템과의 연동을 염두에 두고 고정 엔드포인트를 노출시켰습니다.

---

## 프로젝트 구조
```text
.
├── k8s/               # Kubernetes 리소스 (Deployment, Service, ConfigMap)
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
├── database/          # SQL 초기화 스크립트
├── generator.py       # 이벤트 생성기 (Simulator)
├── detector.py        # 이상 탐지 엔진 (Worker)
├── data_service.py    # 데이터 분석 레이어
├── dashboard.py       # 통합 대시보드 (Visualization)
├── Dockerfile         # 컨테이너 정의
└── docker-compose.yml # 오케스트레이션 정의
```
