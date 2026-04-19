import psycopg2
import pandas as pd
import json
from db_utils import get_connection

class DataService:
    def __init__(self):
        pass

    def get_connection(self):
        return get_connection()

    # --- [EARS v4: 시스템 헬스 및 이상 탐지 데이터 레이어] ---

    def log_error_with_summary(self, error_data):
        """
        에러 로그를 저장하고 동기적으로 요약 테이블(Summary Table)을 갱신합니다.
        성능을 위해 UPSERT(ON CONFLICT DO UPDATE) 방식을 사용하여 실시간성을 확보합니다.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            # 1. 원본 로그 저장 (error_logs)
            cur.execute("""
                INSERT INTO error_logs (timestamp, error_code, error_msg, severity, request_path, metadata)
                VALUES (NOW(), %s, %s, %s, %s, %s)
            """, (
                error_data['error_code'],
                error_data['message'],
                error_data['severity'],
                error_data['page'],
                json.dumps(error_data)
            ))

            # 2. 요약 테이블 갱신 (UPSERT)
            # 1분 단위로 버킷화하여 집계 부하를 분산함
            cur.execute("""
                INSERT INTO error_metrics_summary (minute_bucket, error_code, severity, error_count)
                VALUES (date_trunc('minute', NOW()), %s, %s, 1)
                ON CONFLICT (minute_bucket, error_code, severity)
                DO UPDATE SET error_count = error_metrics_summary.error_count + 1
            """, (error_data['error_code'], error_data['severity']))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[DataService] Error logging failed: {e}")
        finally:
            conn.close()

    def get_system_health_metrics(self):
        """요약 테이블을 기반으로 찰나의 순간에 통합 헬칭 대시보드 데이터를 가져옵니다."""
        conn = self.get_connection()
        query = """
            SELECT 
                SUM(error_count) as total_errors,
                COUNT(DISTINCT error_code) as unique_error_types,
                SUM(error_count) FILTER (WHERE severity = 'CRITICAL') as critical_errors
            FROM error_metrics_summary
            WHERE minute_bucket > NOW() - INTERVAL '1 hour'
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df.fillna(0).iloc[0]

    def get_error_distribution_by_code(self):
        """에러 코드별 분포를 요약 테이블에서 고속 조회합니다."""
        conn = self.get_connection()
        query = """
            SELECT error_code, SUM(error_count) as count
            FROM error_metrics_summary
            WHERE minute_bucket > NOW() - INTERVAL '24 hours'
            GROUP BY error_code ORDER BY count DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    # --- [Business Analytics: 기존 비즈성 분석 레이어 복구] ---

    def get_kpi_metrics(self, category="All"):
        """총 조회수, 구매수, 방문자수 등 핵심 비즈니스 KPI를 집계합니다."""
        conn = self.get_connection()
        cat_filter = "" if category == "All" else f"AND p.category = '{category}'"
        query = f"""
            SELECT 
                COUNT(*) FILTER (WHERE event_type = 'page_view') as views,
                COUNT(*) FILTER (WHERE event_type = 'purchase') as purchases,
                COUNT(DISTINCT user_id) as users
            FROM events e
            JOIN products p ON e.product_id = p.product_id
            WHERE 1=1 {cat_filter}
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df.iloc[0]

    def get_popular_products(self, category="All", limit=10):
        """가장 많이 구매된 상품 리스트를 가져옵니다."""
        conn = self.get_connection()
        cat_filter = "" if category == "All" else f"AND p.category = '{category}'"
        query = f"""
            SELECT p.name, COUNT(*) as count
            FROM events e
            JOIN products p ON e.product_id = p.product_id
            WHERE e.event_type = 'purchase' {cat_filter}
            GROUP BY p.name ORDER BY count DESC LIMIT {limit}
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_popular_search_keywords(self, category="All", limit=10):
        """인기 검색 키워드를 분석합니다."""
        conn = self.get_connection()
        cat_type_filter = "" if category == "All" else f"AND metadata->>'selected_type' = '{category}'"
        query = f"""
            SELECT metadata->>'query_string' as keyword, COUNT(*) as count
            FROM events
            WHERE event_type = 'search' {cat_type_filter}
            GROUP BY keyword ORDER BY count DESC LIMIT {limit}
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_recent_event_logs(self, limit=50):
        """최근 시스템 이벤트 로그를 실시간으로 가져옵니다. (Trace ID 포함)"""
        conn = self.get_connection()
        query = f"""
            SELECT timestamp, event_type, user_id, metadata->>'trace_id' as trace_id, metadata
            FROM events 
            ORDER BY timestamp DESC LIMIT {limit}
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_category_performance(self):
        """모든 카테고리의 성과(조회/구매)를 비교 분석합니다."""
        conn = self.get_connection()
        query = """
            SELECT p.category, 
                   COUNT(*) FILTER (WHERE e.event_type = 'page_view') as views,
                   COUNT(*) FILTER (WHERE e.event_type = 'purchase') as purchases
            FROM events e
            JOIN products p ON e.product_id = p.product_id
            GROUP BY p.category
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def get_hourly_activity(self):
        """24시간 기준 시간대별 서비스 활동량(전체 이벤트)을 가져옵니다."""
        conn = self.get_connection()
        query = """
            SELECT date_trunc('hour', timestamp) as hour, COUNT(*) as count
            FROM events
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            GROUP BY hour ORDER BY hour
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
