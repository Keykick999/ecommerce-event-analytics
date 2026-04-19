import os
import time
import json
import random
import psycopg2
from faker import Faker
from datetime import datetime
from uuid import uuid4

# [EARS Dependency]
from ears_utils import generate_trace_id, mask_pii, classify_severity
from data_service import DataService

# Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "database": "analytics_db",
    "user": "user",
    "password": "password",
    "port": 5432
}

fake = Faker()

class EventGenerator:
    def __init__(self):
        self.data_service = DataService()
        self.conn = self.data_service.get_connection()
        self.products = self.get_products()
        self.categories = list(set([p[2] for p in self.products]))
        self.circuit_breaker_file = "circuit_breaker_state.json"

    def get_products(self):
        cur = self.conn.cursor()
        cur.execute("SELECT product_id, name, category, price FROM products;")
        return cur.fetchall()

    def check_circuit_breaker(self):
        """서킷 브레이커 상태를 확인하여 장애 전파를 방지합니다."""
        if os.path.exists(self.circuit_breaker_file):
            with open(self.circuit_breaker_file, "r") as f:
                state = json.load(f)
                return state.get("is_open", False)
        return False

    def simulate_user_session(self):
        """한 명의 사용자가 서비스를 이용하는 전 과정을 시뮬레이션합니다."""
        trace_id = generate_trace_id()
        user_id = f"user_{random.randint(1, 1000)}"
        session_id = str(uuid4())

        # 서킷 브레이커 확인
        if self.check_circuit_breaker():
            print(f"🛑 [GEN] Circuit Breaker is OPEN. Skipping session {trace_id}")
            return

        # 1. 인위적 에러 발생 시뮬레이션 (검색 시 10% 확률로 500 에러)
        if random.random() < 0.1:
            self.log_error(user_id, session_id, trace_id, "500", "Internal Server Error", "/api/search")
            return

        # 2. 정상 유입 로직
        category = random.choice(self.categories)
        target_products = [p for p in self.products if p[2] == category]

        # Search
        self.insert_event(user_id, session_id, 'search', None, {
            "trace_id": trace_id,
            "query_string": fake.word(),
            "selected_type": category
        })

        # View and Purchase
        for product in random.sample(target_products, k=random.randint(1, 2)):
            p_id, p_name, p_cat, p_price = product
            
            # View
            self.insert_event(user_id, session_id, 'page_view', p_id, {
                "trace_id": trace_id,
                "url": f"/products/{p_id}"
            })

            # 5% 확률로 결제 장애 발생 시뮬레이션
            if random.random() < 0.05:
                self.log_error(user_id, session_id, trace_id, "PAY_FAILED", "Credit card declined", "/api/payment/execute")
                continue

            # Purchase
            if random.random() < 0.3:
                self.insert_event(user_id, session_id, 'purchase', p_id, {
                    "trace_id": trace_id,
                    "order_id": str(uuid4()),
                    "total_amount": float(p_price),
                    "payment_info": mask_pii({"card_number": fake.credit_card_number()}) # Masking applied!
                })

    def log_error(self, user_id, session_id, trace_id, code, msg, path):
        """시스템 장애 로그를 기록하고 분석 엔진에 전달합니다."""
        severity = classify_severity(path, code)
        error_data = {
            "trace_id": trace_id,
            "user_id": user_id,
            "session_id": session_id,
            "error_code": code,
            "message": msg,
            "page": path,
            "severity": severity
        }
        # 분석 요약 테이블 갱신을 포함한 로그 저장
        self.data_service.log_error_with_summary(error_data)
        
        # 일반 events 테이블에도 기록 (통합 로그용)
        self.insert_event(user_id, session_id, 'error', None, error_data)
        print(f"🚨 [GEN] Error Logged: {code} at {path} ({severity})")

    def insert_event(self, user_id, session_id, event_type, product_id, metadata):
        cur = self.conn.cursor()
        query = """
            INSERT INTO events (user_id, session_id, event_type, product_id, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(query, (user_id, session_id, event_type, product_id, json.dumps(metadata)))
        self.conn.commit()

    def run(self, iterations=100):
        print("🚀 High-Fidelity Event Generator started...")
        for _ in range(iterations):
            self.simulate_user_session()
            time.sleep(random.uniform(0.2, 0.8))

if __name__ == "__main__":
    gen = EventGenerator()
    gen.run(500)
