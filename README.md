# E-commerce Event Log Pipeline & Analytics

이 프로젝트는 이커머스 서비스의 사용자 행동 로그를 수집하고, **관심(조회)과 실제 구매 사이의 격차**를 분석하기 위한 데이터 파이프라인입니다.

## 🚀 실행 방법 (Docker 사용)

시스템에 Docker와 Docker Compose가 설치되어 있다면 아래 명령어로 즉시 실행할 수 있습니다.

1.  **인프라 실행 (PostgreSQL)**
    ```bash
    docker-compose up -d
    ```

2.  **데이터 생성 (Python)**
    *   (Option) 가상환경 생성 및 라이브러리 설치
    ```bash
    pip install -r requirements.txt
    python generator.py
    ```

3.  **대시보드 실행 (Streamlit)**
    ```bash
    streamlit run dashboard.py
    ```

## 🛠️ 기술 스택
- **Database**: PostgreSQL 15 (Hybrid Schema with JSONB)
- **Analytics UI**: Streamlit + Plotly
- **Data Gen**: Python + Faker
- **Infrastructure**: Docker Compose

## 📊 주요 분석 포인트
- **Conversion Gap**: 상품 유형별(가전, 식품 등) 관심도 대비 결제율 차이 분석
- **Top-N Analysis**: 전체 및 카테고리별 인기 조회 상품 vs 인기 결제 상품 순위 비교
- **Search Insight**: 카테고리 내 주요 검색 키워드 트렌드 파악

---
이 프로젝트는 데이터의 일관성(RDBMS)과 로그의 유연성(JSONB)을 동시에 확보한 하이브리드 설계를 특징으로 합니다.
