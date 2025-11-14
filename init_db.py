# ...existing code...
import os
import csv
import re
from dataclasses import dataclass
from typing import List, Optional, Callable, Tuple
from psycopg2.extras import execute_values
import database.db as db_api

@dataclass
class TableSpec:
    name: str                      # table name in DB
    ddl: str                       # CREATE TABLE ... SQL
    columns: List[str]             # column names in CSV and INSERT
    csv_path: Optional[str] = None # path to CSV file (optional)
    truncate: bool = True          # truncate before insert
    converter: Optional[Callable[[dict], Tuple]] = None
    # converter: function(row_dict) -> tuple(values) if custom conversion needed

def _extract_first_int(s: str) -> Optional[int]:
    if s is None:
        return None
    m = re.search(r'-?\d+', s)
    return int(m.group()) if m else None

def _default_row_converter(row: dict, columns: List[str]):
    vals = []
    for col in columns:
        v = row.get(col)
        if v is None or v == "":
            vals.append(None)
        else:
            # numeric normalization: extract first integer if present
            if col not in ("league", "team_name"):
                n = _extract_first_int(v)
                if n is not None:
                    vals.append(n)
                    continue
                # try float fallback
                try:
                    vals.append(int(float(v)))
                    continue
                except Exception:
                    vals.append(None)
                    continue
            vals.append(v)
    return tuple(vals)

def load_csv_using_conn(conn, spec: TableSpec) -> int:
    if not spec.csv_path or not os.path.exists(spec.csv_path):
        print(f"[init_db] CSV not found for {spec.name}: {spec.csv_path} — skipping CSV load")
        return 0

    with conn.cursor() as cur, open(spec.csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        rows = []
        for r in reader:
            if spec.converter:
                rows.append(spec.converter(r))
            else:
                rows.append(_default_row_converter(r, spec.columns))

        if spec.truncate:
            cur.execute(f"TRUNCATE TABLE {spec.name};")

        insert_sql = f"INSERT INTO {spec.name} ({', '.join(spec.columns)}) VALUES %s"
        if rows:
            execute_values(cur, insert_sql, rows)
    return len(rows)

def ensure_table_and_load(spec: TableSpec) -> int:
    # create table
    print(f"[init_db] Ensuring table {spec.name} ...")
    db_api.execute(spec.ddl)
    # if CSV given, bulk load
    if spec.csv_path:
        conn = db_api.get_conn()
        try:
            count = load_csv_using_conn(conn, spec)
            conn.commit()
            print(f"[init_db] Loaded {count} rows into {spec.name}")
            return count
        except Exception:
            conn.rollback()
            raise
        finally:
            db_api.put_conn(conn)
    return 0

# --- register table specs here ---
BASE_DIR = os.path.dirname(__file__)
TABLE_SPECS: List[TableSpec] = [
    TableSpec(
        name="standings",
        ddl="""
CREATE TABLE IF NOT EXISTS standings (
  league TEXT NOT NULL,
  team_rank INTEGER,
  team_name TEXT,
  team_matches_played INTEGER,
  team_wins INTEGER,
  team_losses INTEGER,
  team_points_scored INTEGER,
  team_points_conceded INTEGER,
  team_home_points INTEGER,
  team_home_goal_difference INTEGER,
  team_total_goal_difference INTEGER,
  team_total_points INTEGER
);
""",
        columns=[
          "league","team_rank","team_name","team_matches_played","team_wins","team_losses",
          "team_points_scored","team_points_conceded","team_home_points",
          "team_home_goal_difference","team_total_goal_difference","team_total_points"
        ],
        csv_path=os.path.join(BASE_DIR, "tables", "standings.csv")
    ),

    # örnek: diğer tabloları buraya ekleyin
    # TableSpec(
    #     name="teams",
    #     ddl="CREATE TABLE IF NOT EXISTS teams (id SERIAL PRIMARY KEY, team_name TEXT UNIQUE, city TEXT);",
    #     columns=["id","team_name","city"],
    #     csv_path=os.path.join(BASE_DIR, "tables", "teams.csv")
    # ),
]

def init_db():
    total = 0
    for spec in TABLE_SPECS:
        try:
            total += ensure_table_and_load(spec)
        except Exception as e:
            print(f"[init_db] ERROR initializing {spec.name}: {e}")
            raise
    print(f"[init_db] Initialization complete. Total rows inserted: {total}")

if __name__ == "__main__":
    init_db()
    print("Database initialization finished.")
# ...existing code...