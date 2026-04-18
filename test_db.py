import psycopg2

DB_CONFIG = {
    "host": "127.0.0.1",
    "database": "analytics_db",
    "user": "user",
    "password": "password",
    "port": 5432
}

try:
    print("Connecting to DB...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("Success!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
    import traceback
    traceback.print_exc()
