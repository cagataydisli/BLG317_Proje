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


# --- 1. ANA MENÜ (Yönlendirme) ---
@app.route('/teams')
def teams_menu():

    return redirect(url_for('teams_table_page'))


# --- 2. TABLO GÖRÜNÜMÜ (/teams/table) ---
@app.route('/teams/table')
def teams_table_page():
    # Tüm verileri çekiyoruz (En güncel lig en üstte)
    query = """
        SELECT 
            team_id,
            staff_id,
            team_url,
            team_name,
            league,
            team_city,
            team_year,
            saloon_name,
            saloon_capacity,
            saloon_address
        FROM Teams
        ORDER BY league DESC, team_name ASC
    """

    try:
        # db_api.query senin sisteminde çalışıyor
        rows = db_api.query(query)
    except Exception as e:
        print(f"Sorgu Hatası: {e}")
        rows = []

    # Verileri HTML'e göndermek için sözlüğe çeviriyoruz
    teams = []
    for row in rows:
        teams.append({
            "team_id": row[0],
            "staff_id": row[1],
            "team_url": row[2],
            "team_name": row[3],
            "league": row[4],
            "team_city": row[5],
            "team_year": row[6],
            "saloon_name": row[7],
            "saloon_capacity": row[8],
            "saloon_address": row[9]
        })

    # teams.html dosyasını render ediyoruz
    return render_template('teams.html', teams=teams)


# --- 3. EKLEME İŞLEMİ (/teams/add) ---
@app.route('/teams/add', methods=['POST'])
def add_team():
    try:
        data = request.form
        
        # Form verilerini al
        t_id = data.get('team_id')
        t_name = data.get('team_name')
        t_city = data.get('team_city')
        t_league = data.get('league')
        t_url = data.get('team_url')
        s_name = data.get('saloon_name')
        s_addr = data.get('saloon_address')
        
        # Sayısal verileri işle (Boşsa None yap)
        # Staff ID
        s_id = data.get('staff_id')
        s_id = int(s_id) if s_id and s_id.strip() else None
            
        # Kapasite
        s_cap = data.get('saloon_capacity')
        s_cap = int(s_cap) if s_cap and s_cap.strip() else None

        # Yıl
        t_year = data.get('team_year')
        t_year = int(t_year) if t_year and t_year.strip() else None

        # SQL INSERT Sorgusu
        query = """
            INSERT INTO Teams (
                team_id, team_name, team_city, team_year, league, 
                staff_id, team_url, saloon_name, saloon_capacity, saloon_address
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        db_api.execute(query, (
            t_id, t_name, t_city, t_year, t_league, 
            s_id, t_url, s_name, s_cap, s_addr
        ))
        
        return redirect(url_for('teams_table_page'))

    except Exception as e:

        return f"<h3>Ekleme Başarısız!</h3><p>Hata Detayı: {e}</p><br><a href='/teams/table'>Geri Dön</a>"


# --- 4. SİLME İŞLEMİ (/teams/delete/ID) ---
@app.route('/teams/delete/<int:team_id>', methods=['POST'])
def delete_team(team_id):
    try:
        sql = "DELETE FROM Teams WHERE team_id = %s"
        db_api.execute(sql, (team_id,))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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


@app.route('/standings')
def standings_page():
    # ---------------------------------------------------------
    # ADIM 1: Filtreleme Menüsü için Benzersiz Ligleri Çek
    # ---------------------------------------------------------
    league_sql = "SELECT DISTINCT league FROM standings ORDER BY league DESC"
    try:
        league_rows = db_api.query(league_sql)
        # Template'de {{ l.league }} olarak kullanabilmek için dict listesine çeviriyoruz
        leagues = [{"league": row[0]} for row in league_rows]
    except Exception as e:
        print(f"Lig listesi hatası: {e}")
        leagues = []

    # ---------------------------------------------------------
    # ADIM 2: URL'den Parametreleri Al
    # ---------------------------------------------------------
    # Filtreleme parametresi
    selected_league = request.args.get('league')

    # Sıralama parametreleri
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

    # Limit parametresi
    try:
        limit = int(request.args.get('limit', 0))
        if limit <= 0 or limit > 1000:
            limit = None
    except ValueError:
        limit = None

    # ---------------------------------------------------------
    # ADIM 3: Ana Sorguyu İnşa Et
    # ---------------------------------------------------------
    cols = [
        "league","team_rank","team_name","team_matches_played","team_wins","team_losses",
        "team_points_scored","team_points_conceded","team_home_points",
        "team_home_goal_difference","team_total_goal_difference","team_total_points"
    ]
    select_cols = ", ".join(cols)
    
    sql = """
        SELECT 
            s.*, 
            t.team_url
        FROM standings s
        LEFT JOIN Teams t 
            ON s.league = t.league 
            AND s.team_name = t.team_name
    """
    
    params = []

    # WHERE koşulu (s.league olarak güncelledik çünkü artık iki tablo var)
    if selected_league:
        sql += " WHERE s.league = %s"
        params.append(selected_league)
    
    # Sıralama (s. ekledik ki karışıklık olmasın)
    # Not: sort değişkeni 'team_rank' gibi geldiği için başına 's.' eklemeliyiz
    sql += f" ORDER BY s.{sort} {order_sql}"

    # Limit
    if limit:
        sql += " LIMIT %s"
        params.append(limit)

    rows = db_api.query(sql, tuple(params))

    # Sütun isimlerini manuel tanımlamıştık, şimdi sonuna 'team_url' ekliyoruz
    cols = [
        "league","team_rank","team_name","team_matches_played","team_wins","team_losses",
        "team_points_scored","team_points_conceded","team_home_points",
        "team_home_goal_difference","team_total_goal_difference","team_total_points",
        "team_url"  # <-- YENİ EKLENEN
    ]

    # Tuple listesini Dict listesine çeviriyoruz
    standings = [dict(zip(cols, row)) for row in rows]

    if request.args.get('format') == 'json':
        return jsonify(standings)
        
    # HTML'e hem tablo verisini, hem lig listesini, hem de seçili ligi gönderiyoruz
    return render_template(
        'standings.html', 
        standings=standings, 
        leagues=leagues, 
        current_league=selected_league
    )
@app.route('/teams/<int:team_id>/players')
def team_players_page(team_id):
    # 1. Önce Takım Adını ve Bilgilerini Çekelim (Başlık için)
    team_query = "SELECT team_name, league, team_url FROM Teams WHERE team_id = %s"
    try:
        team_row = db_api.query(team_query, (team_id,))
        if not team_row:
            return "Takım bulunamadı!", 404
        
        # Tuple'dan veriyi alalım
        team_info = {
            "name": team_row[0][0],
            "league": team_row[0][1],
            "url": team_row[0][2]
        }
    except Exception as e:
        return f"Takım bilgisi hatası: {e}"

    # 2. O Takıma Ait Oyuncuları Çekelim
    players_query = """
        SELECT 
            player_id, 
            player_name, 
            player_height, 
            player_birthdate, 
            league
        FROM Players 
        WHERE team_id = %s
        ORDER BY player_name ASC
    """
    
    try:
        player_rows = db_api.query(players_query, (team_id,))
    except Exception as e:
        print(f"Oyuncu sorgu hatası: {e}")
        player_rows = []

    players = []
    for row in player_rows:
        players.append({
            "player_id": row[0],
            "player_name": row[1],
            "player_height": row[2],
            "player_birthdate": row[3],
            "league": row[4]
        })

    # Verileri yeni bir HTML sayfasına gönderiyoruz
    return render_template('team_players.html', team=team_info, players=players)

if __name__ == '__main__':
    app.run(debug=True)