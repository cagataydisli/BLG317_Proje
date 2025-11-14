import os
import time
import psycopg2

dsn = os.environ.get("DATABASE_URL")
if not dsn:
    print("DATABASE_URL not set")
    raise SystemExit(1)

# normalize common prefixes
if dsn.startswith("postgresql+psycopg2://"):
    dsn = dsn.replace("postgresql+psycopg2://", "postgresql://", 1)
if dsn.startswith("postgres://"):
    dsn = dsn.replace("postgres://", "postgresql://", 1)

retries = int(os.environ.get("DB_WAIT_RETRIES", 60))
delay = float(os.environ.get("DB_WAIT_DELAY", 1.0))

for i in range(retries):
    try:
        conn = psycopg2.connect(dsn)
        conn.close()
        print("Postgres is available")
        break
    except Exception as e:
        print(f"Postgres not ready ({i+1}/{retries}): {e}")
        time.sleep(delay)
else:
    print("Postgres did not become ready in time")
    raise SystemExit(1)