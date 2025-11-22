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
            if col not in ("league", "team_name", "match_date", "match_hour", "match_id", "match_city", "match_saloon"):
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


def load_csv_using_conn(conn, spec: TableSpec):
    if not spec.csv_path or not os.path.exists(spec.csv_path):
        print(f"[init_db] CSV not found for {spec.name}: {spec.csv_path} — skipping CSV load")
        return 0

    rows = []
    with open(spec.csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vals = _default_row_converter(row, spec.columns)
            rows.append(vals)

    if not rows:
        return 0

    cols_str = ", ".join(spec.columns)
    placeholders = ", ".join(["%s"] * len(spec.columns))

    inserted_count = 0
    with conn.cursor() as cur:
        # Matches tablosu için satır satır yükleme yapalım ki hatalı olanları atlayabilelim
        if spec.name.lower() in ("matches", "players"):
            print(f"[init_db] Loading {spec.name} row by row to handle missing keys...")
            for row in rows:
                try:
                    sql = f"INSERT INTO {spec.name} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                    cur.execute(sql, row)
                    inserted_count += 1
                except Exception as e:
                    # Hata mesajında ForeignKeyViolation varsa o satırı atla
                    conn.rollback()  # Önceki hatayı temizle
                    # print(f"Skipping match due to error: {e}")
                    continue
            conn.commit()

        # Diğer tablolar için hızlı (bulk) yükleme devam etsin
        else:
            insert_sql = f"INSERT INTO {spec.name} ({cols_str}) VALUES %s ON CONFLICT DO NOTHING"
            try:
                execute_values(cur, insert_sql, rows)
                conn.commit()
                inserted_count = len(rows)
            except Exception as e:
                conn.rollback()
                print(f"[init_db] Error loading {spec.name}: {e}")
                raise e

    print(f"[init_db] Loaded {inserted_count} rows into {spec.name}")
    return inserted_count

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
TABLE_SPECS = [
    # 1. Önce Takımlar yüklenmeli (Çünkü Maçlar buna bağımlı)
    TableSpec(
        name="Teams",
        ddl="""
            CREATE TABLE IF NOT EXISTS Teams (
                team_id INT PRIMARY KEY,
                team_name VARCHAR(100) NOT NULL UNIQUE
            );
        """,
        # CSV dosyanızdaki sütun isimleri burayla eşleşmeli:
        columns=["team_id", "team_name"],
        csv_path=os.path.join(BASE_DIR, "tables", "team_data.csv")
    ),

    # 2. Maçlar Tablosu
    TableSpec(
        name="Matches",
        ddl="""
            CREATE TABLE IF NOT EXISTS Matches (
                match_id VARCHAR(16) NOT NULL PRIMARY KEY,
                home_team_id INT NOT NULL,
                away_team_id INT NOT NULL,
                match_date DATE,
                match_hour TIME,
                home_score SMALLINT,
                away_score SMALLINT,
                league VARCHAR(64),
                match_week VARCHAR(16),
                match_city VARCHAR(64),
                match_saloon VARCHAR(128),
                CONSTRAINT fk_matches_home FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
                CONSTRAINT fk_matches_away FOREIGN KEY (away_team_id) REFERENCES Teams(team_id)
            );
        """,
        # CSV'deki başlık sırasına göre burayı düzenle:
        columns=[
            "match_id", "home_team_id", "away_team_id", "match_date", "match_hour",
            "home_score", "away_score", "league", "match_week", "match_city", "match_saloon"
        ],
        csv_path=os.path.join(BASE_DIR, "tables", "matches.csv")
    ),

    # 3. Standings (Zaten vardı, en sona ekleyebilirsin)
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
            "league", "team_rank", "team_name", "team_matches_played", "team_wins", "team_losses",
            "team_points_scored", "team_points_conceded", "team_home_points",
            "team_home_goal_difference", "team_total_goal_difference", "team_total_points"
        ],
        csv_path=os.path.join(BASE_DIR, "tables", "standings.csv")
    ),

    TableSpec(
        name="Players",
        ddl="""
                CREATE TABLE IF NOT EXISTS Players (
                    team_id INT,
                    team_url VARCHAR(255),
                    league VARCHAR(100),
                    player_name VARCHAR(200),
                    player_id INT PRIMARY KEY,
                    player_birthdate VARCHAR(50), -- Tarih formatı karmaşıksa VARCHAR güvenlidir
                    player_height VARCHAR(20)    -- '2.05' veya '205 cm' gibi olabilir

                    
                );
            """,
        # DİKKAT: Buradaki sıra CSV dosyanızdaki sütun sırasıyla BİREBİR AYNI olmalı!
        # Sizin verdiğiniz bilgiye göre: team_id, team_url, league, player_name, player_id, player_birthdate, player_height
        columns=[
            "team_id",
            "team_url",
            "league",
            "player_name",
            "player_id",
            "player_birthdate",
            "player_height"
        ],

        # Dosya ismini de doğruladık:
        csv_path=os.path.join(BASE_DIR, "tables", "player_data.csv")
    ),
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