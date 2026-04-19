import psycopg2
import time
import os

def get_connection():
    """
    중앙 집중화된 데이터베이스 연결 관리자입니다.
    환경 변수가 있으면 Docker 환경으로 간주하고, 없으면 로컬(Windows) 환경으로 간주합니다.
    """
    # 환경 변수 우선 사용 (Docker Compose용)
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "5433") # 로컬 기본값 5433
    
    try:
        return psycopg2.connect(
            host=db_host,
            database="analytics_db",
            user="user",
            password="password",
            port=int(db_port)
        )
    except Exception as e:
        # DB가 준비될 때까지 재시도
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
