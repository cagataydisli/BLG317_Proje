# app.py
from flask import request, Flask, render_template, jsonify, redirect, url_for
import database.db as db_api
from datetime import datetime # En tepeye bunu ekle
import math # En tepeye eklemeyi unutma (sayfa sayısını yukarı yuvarlamak için)

app = Flask(__name__)

# Ana Sayfa Route'u
@app.route('/')
def index():
    return render_template('index.html')

# 1. Oyuncular (Çağatay Dişli)
@app.route('/players')
def players_page():
    # --- 1. Parametreleri Al ---
    search = request.args.get('search', '').strip().lower()
    sort_by = request.args.get('sort_by', '').strip()

    # Sayfalama Parametreleri (Varsayılan: 1. sayfa, 20 satır)
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
    except ValueError:
        page = 1
        per_page = 20

    # Filtre Parametreleri
    selected_teams = request.args.getlist('teams')
    selected_leagues = request.args.getlist('leagues')

    # --- 2. Filtre Listelerini Hazırla ---
    try:
        all_teams = [r[0] for r in db_api.query("SELECT DISTINCT team_name FROM teams ORDER BY team_name") if r[0]]
        all_leagues = [r[0] for r in db_api.query("SELECT DISTINCT league FROM players ORDER BY league") if r[0]]
    except:
        all_teams, all_leagues = [], []

    # --- 3. SQL ile Veriyi Çek ---
    sql = """
        SELECT p.player_id, p.player_name, p.player_height, p.player_birthdate, 
               p.league, t.team_name, p.team_url
        FROM players p
        LEFT JOIN teams t ON p.team_id = t.team_id
        WHERE 1=1
    """
    params = []

    if search:
        sql += " AND p.player_name ILIKE %s"
        params.append(f"%{search}%")

    if selected_teams:
        placeholders = ', '.join(['%s'] * len(selected_teams))
        sql += f" AND t.team_name IN ({placeholders})"
        params.extend(selected_teams)

    if selected_leagues:
        placeholders = ', '.join(['%s'] * len(selected_leagues))
        sql += f" AND p.league IN ({placeholders})"
        params.extend(selected_leagues)

    try:
        rows = db_api.query(sql, tuple(params))
    except Exception as e:
        print(f"SQL Hatası: {e}")
        rows = []

    # --- 4. Veriyi Python Listesine Çevir ---
    players = []
    today = datetime.now()

    for row in rows:
        p_id, p_name, p_height, p_birth, p_league, t_name, t_url = row

        age = 0
        birth_date_obj = datetime.min
        if p_birth and isinstance(p_birth, str) and len(p_birth.strip()) >= 8:
            try:
                clean_date = p_birth.strip()
                birth_date_obj = datetime.strptime(clean_date, "%d.%m.%Y")
                age = today.year - birth_date_obj.year - (
                            (today.month, today.day) < (birth_date_obj.month, birth_date_obj.day))
            except:
                age = 0

        players.append({
            "player_id": p_id,
            "player_name": p_name,
            "player_height": p_height,
            "player_birthdate": p_birth,
            "age": age if age > 0 else "-",
            "league": p_league,
            "team_name": t_name,
            "team_url": t_url,
            "sort_date": birth_date_obj,
            "sort_height": int(''.join(filter(str.isdigit, p_height))) if p_height and any(
                c.isdigit() for c in p_height) else 0
        })

    # --- 5. SIRALAMA ---
    if sort_by == 'name_asc':
        players.sort(key=lambda x: x['player_name'].lower())
    elif sort_by == 'age_asc':
        players.sort(key=lambda x: x['sort_date'], reverse=True)
    elif sort_by == 'age_desc':
        players.sort(key=lambda x: x['sort_date'])
    elif sort_by == 'height_desc':
        players.sort(key=lambda x: x['sort_height'], reverse=True)
    else:
        players.sort(key=lambda x: (x['team_name'] or "", x['player_name']))

    # --- 6. SAYFALAMA MANTIĞI (PAGINATION) ---
    total_count = len(players)
    total_pages = math.ceil(total_count / per_page)

    # Sayfa sınırlarını kontrol et
    if page < 1: page = 1
    if page > total_pages and total_pages > 0: page = total_pages

    # Listeyi Dilimle (Slice)
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    paginated_players = players[start_index:end_index]

    return render_template('players_table.html',
                           players=paginated_players,
                           all_teams=all_teams,
                           all_leagues=all_leagues,
                           selected_teams=selected_teams,
                           selected_leagues=selected_leagues,
                           # Sayfalama verilerini gönderiyoruz
                           current_page=page,
                           total_pages=total_pages,
                           per_page=per_page,
                           total_count=total_count)


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
        -- Sayfa çok yavaşlamasın diye limit koyabilirsin
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

#######################################################################################################################

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