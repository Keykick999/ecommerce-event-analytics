import time
import json
import os
from data_service import DataService

class AnomalyDetector:
    def __init__(self):
        self.data_service = DataService()
        self.state_file = "circuit_breaker_state.json"
        
    def get_error_stats(self):
        """최근 5분간의 에러 발생 현황을 가져옵니다."""
        conn = self.data_service.get_connection()
        query = """
            SELECT COUNT(*) as error_count
            FROM error_logs
            WHERE timestamp > NOW() - INTERVAL '5 minutes'
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df['error_count'][0]

    def analyze_and_react(self):
        """하이브리드 탐지 로직: 임계치 체크 + 동적 상태 제어"""
        error_count = self.get_error_stats()
        
        # 1. 고정 임계치 기반 신속 대응 (5분 내 10건 이상 시 서킷 오픈)
        threshold = 10
        if error_count >= threshold:
            print(f"🚨 [DETECTOR] Anomaly detected! Error count: {error_count}. Opening circuit breaker.")
            self.update_circuit_breaker(True)
        else:
            if error_count < 2: # 안정이 확인되면 다시 클로즈
                # print(f"✅ [DETECTOR] System stable. Error count: {error_count}.")
                self.update_circuit_breaker(False)

    def update_circuit_breaker(self, is_open):
        """Redis를 모사한 파일 기반 공유 상태 관리 (분산 환경 대비)"""
        state = {"is_open": is_open, "updated_at": time.time()}
        with open(self.state_file, "w") as f:
            json.dump(state, f)

    def run(self):
        print("🔍 Anomaly Detector Worker started...")
        while True:
            try:
                self.analyze_and_react()
            except Exception as e:
                print(f"Error in detector: {e}")
            time.sleep(10) # 10초마다 주기적 검사

if __name__ == "__main__":
    detector = AnomalyDetector()
    detector.run()
