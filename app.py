# app.py
from flask import request, Flask, render_template, jsonify
import database.db as db_api

app = Flask(__name__)

# Ana Sayfa Route'u
@app.route('/')
def index():
    return render_template('index.html')

# 1. Oyuncular (Çağatay Dişli)
@app.route('/players')
def players_page():
    try:
        # HTML'deki sıraya göre verileri çekiyoruz:
        # 0: ID, 1: İsim, 2: Doğum, 3: Boy, 4: Takım Adı, 5: Takım ID
        sql = """
            SELECT 
                P.player_id, 
                P.player_name, 
                P.player_birthdate, 
                P.player_height, 
                T.team_name, 
                P.team_id
            FROM Players P
            LEFT JOIN Teams T ON P.team_id = T.team_id
            LIMIT 500
        """
        all_players = db_api.query(sql)
    except Exception as e:
        print(f"Hata: {e}")
        all_players = []

    return render_template('players_table.html', players=all_players)

def players_menu():
    return render_template('players.html')

# 2. Oyuncu Tablosu (Veritabanı sorgusu buraya taşındı)
@app.route('/players/table')
def players_table_page():
    query = """
        SELECT 
            p.player_id, 
            p.player_name, 
            p.player_height, 
            p.player_birthdate, 
            p.league, 
            t.team_name,
            p.team_url
        FROM players p
        LEFT JOIN teams t ON p.team_id = t.team_id
        ORDER BY t.team_name, p.player_name
        LIMIT 500 -- Sayfa çok yavaşlamasın diye limit koyabilirsin
    """
    rows = db_api.query(query)
    
    players = []
    for row in rows:
        players.append({
            "player_id": row[0],
            "player_name": row[1],
            "player_height": row[2],
            "player_birthdate": row[3],
            "league": row[4],
            "team_name": row[5],
            "team_url": row[6]
        })

    return render_template('players_table.html', players=players)   


# 2. Takımlar (Talip Demir)
@app.route('/teams')
def teams_page():
    # Veritabanından takımları çekelim (Teams tablosunu doldurmuştuk!)
    try:
        # db_api.query fonksiyonu db.py dosyasından geliyor olmalı
        all_teams = db_api.query("SELECT * FROM Teams")
    except Exception as e:
        print(f"Hata: {e}")
        all_teams = []

    return render_template('teams.html', teams=all_teams)

    # Detaylı takım verilerini team_data tablosundan çekiyoruz
    query = """
        SELECT 
            team_id, team_name, team_city, team_year, 
            saloon_name, saloon_capacity, league, team_url
        FROM team_data
        ORDER BY team_name
    """
    rows = db_api.query(query)
    
    teams = []
    for row in rows:
        teams.append({
            "team_id": row[0],
            "team_name": row[1],
            "team_city": row[2],
            "team_year": row[3],
            "saloon_name": row[4],
            "saloon_capacity": row[5],
            "league": row[6],
            "team_url": row[7]
        })

    return render_template('teams.html', teams=teams)


# 3. Maçlar (Celil Aslan)
@app.route('/matches')
def matches_page():
    # Maç verilerini çekerken Ev Sahibi ve Deplasman takımlarının isimlerini getirmek için
    # teams tablosuna İKİ KEZ join yapıyoruz (t1: home, t2: away)
    query = """
        SELECT 
            m.match_id,
            m.match_date, 
            m.match_hour, 
            t1.team_name AS home_team, 
            m.home_score, 
            m.away_score, 
            t2.team_name AS away_team, 
            m.match_saloon, 
            m.league,
            m.match_week
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        ORDER BY m.match_date DESC, m.match_hour ASC
        LIMIT 100  -- Sayfa çok şişmesin diye limit koyabiliriz
    """
    rows = db_api.query(query)
    
    matches = []
    for row in rows:
        matches.append({
            "match_id": row[0],
            "match_date": row[1],
            "match_hour": row[2],
            "home_team": row[3],
            "home_score": row[4],
            "away_score": row[5],
            "away_team": row[6],
            "match_saloon": row[7],
            "league": row[8],
            "match_week": row[9]
        })

    return render_template('matches.html', matches=matches)

# 4. Teknik Ekip (Musa Can Turgut)
@app.route('/staff')
def staff_page():
    # Teknik ekip ve takım isimleri
    query = """
        SELECT 
            tr.technic_member_name, 
            tr.technic_member_role, 
            t.team_name, 
            tr.league
        FROM technic_roster tr
        JOIN teams t ON tr.team_id = t.team_id
        ORDER BY t.team_name, tr.technic_member_name
    """
    rows = db_api.query(query)
    
    staff = []
    for row in rows:
        staff.append({
            "name": row[0],
            "role": row[1],
            "team_name": row[2],
            "league": row[3]
        })

    return render_template('staff.html', staff=staff)

# 5. Puan Durumu (Emir Şahin)
@app.route('/standings')
def standings_page():
    # Güvenli sıralama sütunları
    allowed_cols = {
        "league","team_rank","team_name","team_matches_played","team_wins","team_losses",
        "team_points_scored","team_points_conceded","team_home_points",
        "team_home_goal_difference","team_total_goal_difference","team_total_points"
    }

    sort = request.args.get('sort', 'team_rank')
    if sort not in allowed_cols:
        sort = 'team_rank'

    order = request.args.get('order', 'asc').lower()
    order_sql = 'ASC' if order == 'asc' else 'DESC'

    # Optional limit
    try:
        limit = int(request.args.get('limit', 0))
        if limit <= 0 or limit > 1000:
            limit = None
    except ValueError:
        limit = None

    cols = [
        "league","team_rank","team_name","team_matches_played","team_wins","team_losses",
        "team_points_scored","team_points_conceded","team_home_points",
        "team_home_goal_difference","team_total_goal_difference","team_total_points"
    ]
    select_cols = ", ".join(cols)
    
    sql = f"SELECT {select_cols} FROM standings ORDER BY {sort} {order_sql}"
    
    if limit:
        sql += " LIMIT %s"
        rows = db_api.query(sql, (limit,))
    else:
        rows = db_api.query(sql)

    # Tuple listesini Dict listesine çeviriyoruz
    standings = [dict(zip(cols, row)) for row in rows]

    if request.args.get('format') == 'json':
        return jsonify(standings)
        
    return render_template('standings.html', standings=standings)

if __name__ == '__main__':
    app.run(debug=True)