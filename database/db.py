import os
import psycopg2
from psycopg2 import pool

DATABASE_URL = os.environ.get("DATABASE_URL")
_pool = None

def init_pool(minconn=1, maxconn=5):
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(minconn, maxconn, dsn=DATABASE_URL)
    return _pool

def get_conn():
    if _pool is None:
        init_pool()
    return _pool.getconn()

def put_conn(conn):
    if _pool is not None:
        _pool.putconn(conn)

def query(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        put_conn(conn)

def execute(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        put_conn(conn)