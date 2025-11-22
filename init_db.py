import os
import csv
import re
from dataclasses import dataclass
from typing import List, Optional, Callable, Tuple
from psycopg2.extras import execute_values
import database.db as db_api

@dataclass
class TableSpec:
    name: str
    ddl: str
    columns: List[str]
    csv_path: Optional[str] = None 
    truncate: bool = False
    pk_field: Optional[str] = None
    converter: Optional[Callable[[dict], Tuple]] = None

def _extract_first_int(s: str) -> Optional[int]:
    if s is None:
        return None
    m = re.search(r'-?\d+', str(s))
    return int(m.group()) if m else None

def _default_row_converter(row: dict, columns: List[str]):
    vals = []
    for col in columns:
        v = row.get(col)
        if v is None or v == "":
            vals.append(None)
        else:
            # --- KRİTİK DÜZELTME BURADA ---
            # match_id, match_date, match_hour gibi alanları integer'a çevirme!
            # Olduğu gibi string (TEXT) olarak bırak.
            exclude_conversion = (
                "league", "team_name", "player_name", "technic_member_name", 
                "technic_member_role", "match_city", "match_saloon", "player_height",
                "team_url", "team_city", "saloon_name", "saloon_address",
                "match_id", "match_date", "match_hour", "match_week"
            )
            
            if col not in exclude_conversion:
                n = _extract_first_int(v)
                if n is not None:
                    vals.append(n)
                    continue
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
        
        # --- DEDUPLICATION (TEKİLLEŞTİRME) ---
        # Matches tablosu gibi PK içeren tablolarda aynı ID gelirse sonuncuyu al.
        if spec.pk_field and spec.name == "matches":
            unique_rows = {}
            # pk_field tek bir alan ise doğrudan kullan, virgüllü ise ilkini al (basit çözüm)
            pk_col = spec.pk_field.split(',')[0].strip()
            
            for r in reader:
                if spec.converter:
                    val = spec.converter(r)
                else:
                    val = _default_row_converter(r, spec.columns)
                
                # CSV'deki ham ID'yi anahtar olarak kullan
                row_id = r.get(pk_col)
                
                # Eğer ID yoksa veya boşsa, satırı atla veya işlem yap
                if row_id:
                    unique_rows[row_id] = val
                else:
                    # ID yoksa direkt ekle (riskli ama veri kaybını önler)
                    rows.append(val)
            
            # Sözlükteki tekil değerleri listeye ekle
            rows.extend(list(unique_rows.values()))
            print(f"[init_db] Deduplication for {spec.name}: Processed {len(rows)} unique rows.")
            
        else:
            # Diğer tablolar için standart akış
            for r in reader:
                if spec.converter:
                    rows.append(spec.converter(r))
                else:
                    rows.append(_default_row_converter(r, spec.columns))

        if spec.truncate:
            cur.execute(f"TRUNCATE TABLE {spec.name} CASCADE;")

        cols_str = ', '.join(spec.columns)
        insert_sql = f"INSERT INTO {spec.name} ({cols_str}) VALUES %s"

        if spec.pk_field:
            conflict_keys = [k.strip() for k in spec.pk_field.split(',')]
            update_cols = [col for col in spec.columns if col not in conflict_keys]
            
            if update_cols:
                set_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_cols])
                insert_sql += f" ON CONFLICT ({spec.pk_field}) DO UPDATE SET {set_clause}"
            else:
                insert_sql += f" ON CONFLICT ({spec.pk_field}) DO NOTHING"

        if rows:
            execute_values(cur, insert_sql, rows)
    
    return len(rows)

def ensure_table_and_load(spec: TableSpec) -> int:
    print(f"[init_db] Ensuring table {spec.name} ...")
    db_api.execute(spec.ddl)
    
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

# --- Tablo Tanımları ---
BASE_DIR = os.path.dirname(__file__)

TABLE_SPECS: List[TableSpec] = [
    # 1. TEAM_DATA
    TableSpec(
        name="team_data",
        ddl="""
CREATE TABLE IF NOT EXISTS team_data (
  team_id INTEGER PRIMARY KEY,
  team_url TEXT,
  team_name TEXT,
  league TEXT,
  team_city TEXT,
  team_year INTEGER,
  saloon_name TEXT,
  saloon_capacity INTEGER,
  saloon_address TEXT
);
""",
        columns=[
          "team_id", "team_url", "team_name", "league", "team_city", 
          "team_year", "saloon_name", "saloon_capacity", "saloon_address"
        ],
        csv_path=os.path.join(BASE_DIR, "tables", "team_data.csv"),
        truncate=False,       
        pk_field="team_id"    
    ),

    # 2. STANDINGS
    TableSpec(
        name="standings",
        ddl="""
CREATE TABLE IF NOT EXISTS standings (
  standings_id SERIAL PRIMARY KEY,
  league TEXT NOT NULL,
  team_rank INTEGER,
  team_name TEXT NOT NULL,
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
        csv_path=os.path.join(BASE_DIR, "tables", "standings.csv"),
        truncate=True 
    ),

    # 3. PLAYERS
    TableSpec(
        name="players",
        ddl="""
CREATE TABLE IF NOT EXISTS players (
  players_id SERIAL PRIMARY KEY,
  player_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  team_url TEXT,
  league TEXT NOT NULL,
  player_name TEXT NOT NULL,
  player_birthdate TEXT,
  player_height TEXT,
  UNIQUE(player_id, team_id), 
  FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE
);
""",
        columns=[
          "team_id","team_url","league","player_name","player_id","player_birthdate","player_height"
        ],
        csv_path=os.path.join(BASE_DIR, "tables", "player_data.csv"),
        truncate=False,
        pk_field="player_id, team_id" 
    ),

    # 4. MATCHES
    TableSpec(
        name="matches",
        ddl="""
CREATE TABLE IF NOT EXISTS matches (
  match_id TEXT PRIMARY KEY,
  home_team_id INTEGER NOT NULL,
  away_team_id INTEGER NOT NULL,
  match_date TEXT,
  match_hour TIME,
  home_score INTEGER,
  away_score INTEGER,
  league TEXT NOT NULL,
  match_week TEXT,
  match_city TEXT,
  match_saloon TEXT,
  FOREIGN KEY (home_team_id) REFERENCES teams(team_id) ON DELETE CASCADE,
  FOREIGN KEY (away_team_id) REFERENCES teams(team_id) ON DELETE CASCADE
);
""",
        columns=[
          "match_id","home_team_id","away_team_id","match_date","match_hour",
          "home_score","away_score","league","match_week","match_city","match_saloon"
        ],
        csv_path=os.path.join(BASE_DIR, "tables", "matches.csv"),
        truncate=False,
        pk_field="match_id" 
    ),

    # 5. TECHNIC ROSTER
    TableSpec(
        name="technic_roster",
        ddl="""
CREATE TABLE IF NOT EXISTS technic_roster (
  technic_id SERIAL PRIMARY KEY,
  team_id INTEGER NOT NULL,
  team_url TEXT,
  league TEXT NOT NULL,
  technic_member_name TEXT NOT NULL,
  technic_member_role TEXT NOT NULL,
  FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE,
  UNIQUE(team_id, league, technic_member_name, technic_member_role)
);
""",
        columns=[
          "team_id","team_url","league","technic_member_name","technic_member_role"
        ],
        csv_path=os.path.join(BASE_DIR, "tables", "technic_roster.csv"),
        truncate=True,
        pk_field="team_id, league, technic_member_name, technic_member_role"
    ),
]

def ensure_teams_table():
    ddl = """
CREATE TABLE IF NOT EXISTS teams (
  team_id INTEGER PRIMARY KEY,
  team_name TEXT,
  league TEXT
);
"""
    print("[init_db] Ensuring base teams table ...")
    db_api.execute(ddl)

def extract_teams_from_csvs():
    teams_map = {} 
    csv_files = [
        ("tables/team_data.csv", ["team_id"]), 
        ("tables/player_data.csv", ["team_id"]),
        ("tables/matches.csv", ["home_team_id", "away_team_id"]),
        ("tables/technic_roster.csv", ["team_id"]),
    ]
    
    for csv_file, team_cols in csv_files:
        csv_path = os.path.join(BASE_DIR, csv_file)
        if os.path.exists(csv_path):
            with open(csv_path, newline='', encoding='utf-8') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    for col in team_cols:
                        if col in row and row[col]:
                            team_id = _extract_first_int(row[col])
                            if team_id:
                                league = row.get("league", "unknown")
                                t_name = row.get("team_name")
                                
                                if team_id not in teams_map:
                                    teams_map[team_id] = {"name": t_name, "league": league}
                                else:
                                    if not teams_map[team_id]["name"] and t_name:
                                        teams_map[team_id]["name"] = t_name
    
    return teams_map

def load_teams():
    teams_map = extract_teams_from_csvs()
    conn = db_api.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE teams CASCADE;")
            rows = []
            for team_id, data in teams_map.items():
                rows.append((team_id, data["name"], data["league"]))
            
            if rows:
                insert_sql = "INSERT INTO teams (team_id, team_name, league) VALUES %s ON CONFLICT (team_id) DO NOTHING"
                execute_values(cur, insert_sql, rows)
        
        conn.commit()
        print(f"[init_db] Loaded {len(rows)} unique teams into base table")
        return len(rows)
    except Exception as e:
        conn.rollback()
        print(f"[init_db] ERROR loading teams: {e}")
        raise
    finally:
        db_api.put_conn(conn)

def drop_all_tables():
    tables = ["technic_roster", "matches", "players", "standings", "team_data", "teams"]
    print("[init_db] !!! Dropping ALL tables for a fresh start !!!")
    conn = db_api.get_conn()
    try:
        with conn.cursor() as cur:
            for table in tables:
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        conn.commit()
        print("[init_db] All tables dropped successfully.")
    except Exception as e:
        conn.rollback()
        print(f"[init_db] ERROR dropping tables: {e}")
        raise
    finally:
        db_api.put_conn(conn)

def init_db():
    total = 0
    drop_all_tables()

    print("[init_db] === Step 1: Loading Base Teams Table ===")
    try:
        ensure_teams_table()
        load_teams()
    except Exception as e:
        print(f"[init_db] ERROR loading base teams: {e}")
        raise

    print("[init_db] === Step 2: Loading Detailed Team Data ===")
    team_data_spec = next(ts for ts in TABLE_SPECS if ts.name == "team_data")
    try:
        total += ensure_table_and_load(team_data_spec)
    except Exception as e:
        print(f"[init_db] ERROR loading team_data: {e}")
        raise

    print("[init_db] === Step 3: Loading Other Tables ===")
    for spec in TABLE_SPECS:
        if spec.name == "team_data": continue
        try:
            total += ensure_table_and_load(spec)
        except Exception as e:
            print(f"[init_db] ERROR initializing {spec.name}: {e}")
            raise
    
    print(f"[init_db] ✓ Initialization complete.")

if __name__ == "__main__":
    init_db()