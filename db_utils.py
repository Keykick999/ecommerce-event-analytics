import psycopg2
import time

def get_connection():
    """
    중앙 집중화된 데이터베이스 연결 관리자입니다.
    Docker 환경의 포트 매핑(5433)과 재시도 로직을 포함합니다.
    """
    try:
        return psycopg2.connect(
            host="127.0.0.1",
            database="analytics_db",
            user="user",
            password="password",
            port=5433
        )
    except Exception as e:
        # DB가 아직 준비되지 않은 경우를 대비한 3회 재시도 로직
        for i in range(3):
            print(f"DB 연결 재시도 중... ({i+1}/3)")
            time.sleep(2)
            try:
                return psycopg2.connect(
                    host="127.0.0.1",
                    database="analytics_db",
                    user="user",
                    password="password",
                    port=5433
                )
            except:
                continue
        raise e
