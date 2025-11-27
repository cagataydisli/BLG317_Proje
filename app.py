# app.py
from flask import request, Flask, render_template, jsonify, redirect, url_for
import database.db as db_api

app = Flask(__name__)

# Ana Sayfa Route'u
@app.route('/')
def index():
    return render_template('index.html')

# 1. Oyuncular (Çağatay Dişli)
@app.route('/players')
def players_page():
    # Güncel sorgu: Hem takım linkini hem de lig bilgisini içeriyor
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
        LIMIT 500
    """
    try:
        rows = db_api.query(query)
    except Exception as e:
        print(f"Hata: {e}")
        rows = []

    # Veriyi Tuple'dan Dictionary'e çeviriyoruz (HTML'de isimle erişmek için)
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


# --- YENİ OYUNCU EKLEME ---
@app.route('/players/add', methods=['POST'])
def add_player():
    try:
        data = request.form
        player_id = data.get('player_id')
        player_name = data.get('player_name')
        team_id = data.get('team_id')
        height = data.get('player_height')
        birthdate = data.get('player_birthdate')
        league = data.get('league')

        # SQL Ekleme Sorgusu
        sql = """
            INSERT INTO Players (player_id, player_name, team_id, player_height, player_birthdate, league)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        if not team_id:
            team_id = None

        db_api.execute(sql, (player_id, player_name, team_id, height, birthdate, league))

        return redirect(url_for('players_page'))
    except Exception as e:
        return f"Ekleme Hatası: {e}"


# --- OYUNCU SİLME ---
@app.route('/players/delete/<int:player_id>', methods=['POST'])
def delete_player(player_id):
    try:
        sql = "DELETE FROM Players WHERE player_id = %s"
        db_api.execute(sql, (player_id,))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
    # Filtreleme parametreleri
    sort_by = request.args.get('sort', 'match_date')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', '100')
    fmt = request.args.get('format', 'html')
    
    # SQL injection koruması
    allowed_cols = ['match_date', 'match_week', 'league', 'match_city']
    if sort_by not in allowed_cols:
        sort_by = 'match_date'
    
    if order not in ['asc', 'desc']:
        order = 'desc'
    
    try:
        limit = int(limit)
        if limit < 1 or limit > 10000:
            limit = 100
    except:
        limit = 100
    
    # Maç verilerini çekerken Ev Sahibi ve Deplasman takımlarının isimlerini getirmek için
    # teams tablosuna İKİ KEZ join yapıyoruz (t1: home, t2: away)
    query = f"""
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
            m.match_week,
            m.match_city,
            m.home_team_id,
            m.away_team_id
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        ORDER BY m.{sort_by} {order}, m.match_hour ASC
        LIMIT {limit}
    """
    rows = db_api.query(query)
    
    cols = ['match_id', 'match_date', 'match_hour', 'home_team', 'home_score', 
            'away_score', 'away_team', 'match_saloon', 'league', 'match_week',
            'match_city', 'home_team_id', 'away_team_id']
    
    matches = [dict(zip(cols, row)) for row in rows]
    
    if fmt == 'json':
        return jsonify(matches)
    
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

    # BURASI ÖNEMLİ
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