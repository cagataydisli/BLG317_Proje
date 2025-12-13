# app.py
from flask import request, Flask, render_template, jsonify, redirect, url_for
from flask import flash
import database.db as db_api
from datetime import datetime # En tepeye bunu ekle
import math # En tepeye eklemeyi unutma (sayfa sayısını yukarı yuvarlamak için)
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "345678987654345678"

# --- LOGIN MANAGER KURULUMU ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Giriş yapılmamışsa buraya yönlendir

# Kullanıcı Modeli (Flask-Login için gerekli)
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    # Veritabanından kullanıcıyı ID ile bulup getirir
    sql = "SELECT id, username, password_hash FROM Users WHERE id = %s"
    row = db_api.query(sql, (user_id,))
    if row:
        return User(row[0][0], row[0][1], row[0][2])
    return None


# --- GİRİŞ YAP (LOGIN) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Kullanıcıyı bul
        sql = "SELECT id, username, password_hash FROM Users WHERE username = %s"
        user_data = db_api.query(sql, (username,))

        if user_data:
            user_obj = User(user_data[0][0], user_data[0][1], user_data[0][2])
            # Şifre doğru mu kontrol et
            if check_password_hash(user_obj.password_hash, password):
                login_user(user_obj)
                flash('Giriş başarılı!', 'success')
                # Eğer daha önce gitmek istediği bir sayfa varsa oraya, yoksa anasayfaya
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))

        flash('Hatalı kullanıcı adı veya şifre', 'danger')

    return render_template('login.html')


# --- KAYIT OL (REGISTER) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Basit validasyon
        if not username or not password:
            flash("Kullanıcı adı ve şifre zorunlu", "warning")
            return redirect(url_for('register'))

        # Şifreyi güvenli hale getir (Hashle)
        hashed_pw = generate_password_hash(password)

        try:
            sql = "INSERT INTO Users (username, password_hash) VALUES (%s, %s)"
            db_api.execute(sql, (username, hashed_pw))
            flash('Hesap oluşturuldu! Şimdi giriş yapabilirsiniz.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Hata (Kullanıcı adı alınmış olabilir): {e}', 'danger')

    return render_template('register.html')


# --- ÇIKIŞ YAP (LOGOUT) ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Çıkış yapıldı.', 'info')
    return redirect(url_for('login'))






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

    try:
        # GROUP BY team_name: Aynı isimdeki takımları grupla.
        # MIN(team_id): Her grubun ilk ID'sini al (Select kutusu için bir ID lazım).
        query = """
                SELECT MIN(team_id), team_name 
                FROM Teams 
                GROUP BY team_name 
                ORDER BY team_name
            """
        teams_data = db_api.query(query)

        teams_dropdown = [{'id': r[0], 'name': r[1]} for r in teams_data]
    except Exception as e:
        print(f"Takım listesi hatası: {e}")
        teams_dropdown = []

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
               p.league, t.team_name, p.team_url, p.team_id
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
        p_id, p_name, p_height, p_birth, p_league, t_name, t_url, t_id = row

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
            "team_id": t_id,  # Bunu da sözlüğe ekledik
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
                           teams_dropdown=teams_dropdown,
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
@login_required
def add_player():
    try:
        data = request.form

        # player_id'yi ARTIK FORM'DAN ALMIYORUZ
        # player_id = data.get('player_id')  <-- BU SATIR SİLİNDİ/YORUM SATIRI OLDU

        player_name = data.get('player_name')
        team_id = data.get('team_id')
        height = data.get('player_height')
        birthdate = data.get('player_birthdate')
        league = data.get('league')

        # SQL Ekleme Sorgusu (player_id sütununu ve değerini kaldırdık)
        sql = """
            INSERT INTO Players (player_name, team_id, player_height, player_birthdate, league)
            VALUES (%s, %s, %s, %s, %s)
        """

        if not team_id:
            team_id = None

        # execute kısmından da player_id'yi siliyoruz
        db_api.execute(sql, (player_name, team_id, height, birthdate, league))

        flash(f"{player_name} başarıyla eklendi.", "success")  # Kullanıcıya bilgi verelim
        return redirect(url_for('players_page'))
    except Exception as e:
        # Hata mesajını terminale yazdıralım ki görelim
        print(f"Ekleme Hatası: {e}")
        flash(f"Ekleme Hatası: {e}", "danger")
        return redirect(url_for('players_page'))


# --- OYUNCU SİLME ---
@app.route('/players/delete/<int:player_id>', methods=['POST'])
@login_required
def delete_player(player_id):
    try:
        sql = "DELETE FROM Players WHERE player_id = %s"
        db_api.execute(sql, (player_id,))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# --- OYUNCU GÜNCELLEME (UPDATE) ---
@app.route('/players/update', methods=['POST'])
@login_required
def update_player():
    try:
        data = request.form

        # Formdan gelen veriler
        player_id = data.get('player_id')  # WHERE koşulu için gerekli
        player_name = data.get('player_name')
        team_id = data.get('team_id')
        height = data.get('player_height')
        birthdate = data.get('player_birthdate')
        league = data.get('league')

        # team_id boş gelirse None yap (SQL hatası almamak için)
        if not team_id or team_id.strip() == "":
            team_id = None

        # SQL Update Sorgusu
        sql = """
            UPDATE Players 
            SET player_name = %s, 
                team_id = %s, 
                player_height = %s, 
                player_birthdate = %s, 
                league = %s
            WHERE player_id = %s
        """

        db_api.execute(sql, (player_name, team_id, height, birthdate, league, player_id))

        flash(f"Oyuncu ({player_name}) başarıyla güncellendi.", "success")
        return redirect(url_for('players_page'))

    except Exception as e:
        print(f"Güncelleme Hatası: {e}")
        return f"Güncelleme Hatası: {e}"

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
    
    # Fetch all teams for dropdown menus
    teams_query = "SELECT team_id, team_name FROM Teams ORDER BY team_name"
    teams_rows = db_api.query(teams_query)
    teams = [{'team_id': row[0], 'team_name': row[1]} for row in teams_rows]
    
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
    
    # Complex Query: Analytics Statistics
    analytics_query = """
        SELECT 
            m.match_city,
            COUNT(*) as total_matches,
            ROUND(AVG(m.home_score + m.away_score), 2) as avg_total_points,
            MAX(m.home_score + m.away_score) as highest_scoring_game,
            COUNT(CASE WHEN m.home_score > m.away_score THEN 1 END) as home_wins
        FROM Matches m
        WHERE m.home_score IS NOT NULL AND m.away_score IS NOT NULL
        GROUP BY m.match_city
        HAVING COUNT(*) >= 5
        ORDER BY avg_total_points DESC
        LIMIT 10
    """
    analytics_rows = db_api.query(analytics_query)
    analytics = [{
        'city': row[0],
        'total_matches': row[1],
        'avg_total_points': row[2],
        'highest_scoring_game': row[3],
        'home_wins': row[4]
    } for row in analytics_rows]
    
    if fmt == 'json':
        return jsonify(matches)
    
    return render_template('matches.html', matches=matches, teams=teams, analytics=analytics)

# --- MATCHES: CREATE (Add Match) ---
@app.route('/matches/add', methods=['POST'])
def add_match():
    try:
        data = request.form
        
        # Extract form data
        match_id = data.get('match_id')
        home_team_id = data.get('home_team_id')
        away_team_id = data.get('away_team_id')
        match_date = data.get('match_date')
        match_hour = data.get('match_hour')
        match_week = data.get('match_week')
        league = data.get('league')
        match_city = data.get('match_city')
        match_saloon = data.get('match_saloon')
        
        # Validation: Check if home and away teams are different
        if home_team_id == away_team_id:
            flash("Error: Home and away teams cannot be the same!", "danger")
            return redirect(url_for('matches_page'))
        
        # SQL Insert
        sql = """
            INSERT INTO Matches (
                match_id, home_team_id, away_team_id, match_date, match_hour,
                match_week, league, match_city, match_saloon
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        db_api.execute(sql, (
            match_id, home_team_id, away_team_id, match_date, match_hour,
            match_week, league, match_city, match_saloon
        ))
        
        flash(f"Match successfully added! (ID: {match_id})", "success")
        return redirect(url_for('matches_page'))
        
    except Exception as e:
        print(f"ADD MATCH ERROR: {e}")
        flash(f"Error adding match: {e}", "danger")
        return redirect(url_for('matches_page'))

# --- MATCHES: UPDATE (Edit Match/Scores) ---
@app.route('/matches/update', methods=['POST'])
def update_match():
    try:
        data = request.form
        
        # Extract form data
        match_id = data.get('match_id')
        home_team_id = data.get('home_team_id')
        away_team_id = data.get('away_team_id')
        match_date = data.get('match_date')
        match_hour = data.get('match_hour')
        home_score = data.get('home_score')
        away_score = data.get('away_score')
        match_week = data.get('match_week')
        league = data.get('league')
        match_city = data.get('match_city')
        match_saloon = data.get('match_saloon')
        
        # Validation
        if home_team_id == away_team_id:
            flash("Error: Home and away teams cannot be the same!", "danger")
            return redirect(url_for('matches_page'))
        
        # Convert scores to int or None
        home_score = int(home_score) if home_score and home_score.strip() else None
        away_score = int(away_score) if away_score and away_score.strip() else None
        
        # SQL Update
        sql = """
            UPDATE Matches
            SET home_team_id = %s,
                away_team_id = %s,
                match_date = %s,
                match_hour = %s,
                home_score = %s,
                away_score = %s,
                match_week = %s,
                league = %s,
                match_city = %s,
                match_saloon = %s
            WHERE match_id = %s
        """
        
        db_api.execute(sql, (
            home_team_id, away_team_id, match_date, match_hour,
            home_score, away_score, match_week, league, match_city, match_saloon,
            match_id
        ))
        
        flash(f"Match updated! (ID: {match_id})", "success")
        return redirect(url_for('matches_page'))
        
    except Exception as e:
        print(f"UPDATE MATCH ERROR: {e}")
        flash(f"Error updating match: {e}", "danger")
        return redirect(url_for('matches_page'))

# --- MATCHES: DELETE ---
@app.route('/matches/delete/<string:match_id>', methods=['POST'])
def delete_match(match_id):
    try:
        sql = "DELETE FROM Matches WHERE match_id = %s"
        db_api.execute(sql, (match_id,))
        return jsonify({'success': True})
    except Exception as e:
        print(f"DELETE MATCH ERROR: {e}")
        return jsonify({'success': False, 'error': str(e)})

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

def parse_numeric_filter(col_name, value, where_clauses, params):
    """
    Kullanıcı girdisini analiz eder: <20, >50, >=10, 15 gibi.
    """
    if not value:
        return

    value = value.strip()
    operator = "=" # Varsayılan
    
    # Operatörleri kontrol et
    if value.startswith(">="):
        operator = ">="
        val = value[2:]
    elif value.startswith("<="):
        operator = "<="
        val = value[2:]
    elif value.startswith(">"):
        operator = ">"
        val = value[1:]
    elif value.startswith("<"):
        operator = "<"
        val = value[1:]
    else:
        # Düz sayı girildiyse eşitlik aranır
        val = value
    
    # Sayısal değerin güvenli olup olmadığını kontrol et
    if val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
        where_clauses.append(f"{col_name} {operator} %s")
        params.append(int(val))
@app.route('/standings')
def standings_page():
    # ---------------------------------------------------------
    # 1. Lig Listesi (Select Box İçin)
    # ---------------------------------------------------------
    league_sql = "SELECT DISTINCT league FROM standings ORDER BY league DESC"
    try:
        league_rows = db_api.query(league_sql)
        leagues = [{"league": row[0]} for row in league_rows]
    except Exception as e:
        print(f"Lig listesi hatası: {e}")
        leagues = []

    # ---------------------------------------------------------
    # 2. Filtre Parametrelerini Al
    # ---------------------------------------------------------
    f_league = request.args.get('league')
    f_team = request.args.get('team_name')
    f_rank = request.args.get('team_rank') # Örn: "1,2,3"
    
    # Sayısal Filtreler
    f_wins = request.args.get('team_wins')
    f_losses = request.args.get('team_losses')
    f_ps = request.args.get('team_points_scored')
    f_pc = request.args.get('team_points_conceded')
    f_points = request.args.get('team_total_points')

    # Sıralama ve Limit
    sort = request.args.get('sort', 'team_rank')
    order = request.args.get('order', 'asc').lower()
    
    # Güvenli Sıralama Sütunları
    allowed_sorts = {
        "league", "team_rank", "team_name", "team_matches_played",
        "team_wins", "team_losses", "team_points_scored",
        "team_points_conceded", "team_total_points"
    }
    if sort not in allowed_sorts: sort = 'team_rank'
    
    order_sql = 'DESC' if order == 'desc' else 'ASC' # Varsayılan ASC

    # ---------------------------------------------------------
    # 3. Dinamik SQL İnşası
    # ---------------------------------------------------------
    base_sql = """
        SELECT s.*, t.team_url
        FROM standings s
        LEFT JOIN Teams t ON s.league = t.league AND s.team_name = t.team_name
    """
    
    where_clauses = []
    params = []

    # --- LİG FİLTRESİ ---
    if f_league:
        where_clauses.append("s.league = %s")
        params.append(f_league)

    # --- TAKIM ADI FİLTRESİ (LIKE) ---
    if f_team:
        where_clauses.append("s.team_name ILIKE %s") # ILIKE: Büyük/Küçük harf duyarsız
        params.append(f"%{f_team}%")

    # --- RANK FİLTRESİ (IN) ---
    # Kullanıcı "1, 2, 5" girerse -> IN (1, 2, 5) yapar
    if f_rank:
        try:
            # Virgülle ayrılmış stringi listeye çevir
            ranks = [int(r.strip()) for r in f_rank.split(',') if r.strip().isdigit()]
            if ranks:
                placeholders = ', '.join(['%s'] * len(ranks))
                where_clauses.append(f"s.team_rank IN ({placeholders})")
                params.extend(ranks)
        except:
            pass # Hatalı format girerse yoksay

    # --- SAYISAL FİLTRELER (<, >, = desteği) ---
    parse_numeric_filter("s.team_wins", f_wins, where_clauses, params)
    parse_numeric_filter("s.team_losses", f_losses, where_clauses, params)
    parse_numeric_filter("s.team_points_scored", f_ps, where_clauses, params)
    parse_numeric_filter("s.team_points_conceded", f_pc, where_clauses, params)
    parse_numeric_filter("s.team_total_points", f_points, where_clauses, params)

    # WHERE Koşullarını Birleştir
    if where_clauses:
        base_sql += " WHERE " + " AND ".join(where_clauses)

    # ORDER BY Ekle
    base_sql += f" ORDER BY s.{sort} {order_sql}"

    # Sorguyu Çalıştır
    try:
        rows = db_api.query(base_sql, tuple(params))
    except Exception as e:
        print(f"Sorgu hatası: {e}")
        rows = []

    # Dictionary'e çevir
    cols = [
        "league","team_rank","team_name","team_matches_played","team_wins","team_losses",
        "team_points_scored","team_points_conceded","team_home_points",
        "team_home_goal_difference","team_total_goal_difference","team_total_points",
        "team_url"
    ]
    standings = [dict(zip(cols, row)) for row in rows]

    return render_template(
        'standings.html', 
        standings=standings, 
        leagues=leagues,
        # Mevcut filtreleri template'e geri gönderiyoruz ki inputlar silinmesin
        filters=request.args 
    )
def safe_int(value):
    if not value:
        return 0
    try:
        return int(value)
    except ValueError:
        return 0

@app.route('/standings/add', methods=['POST'])
def add_standing():
    try:
        # 1. String Verileri Al
        league = request.form.get('league')
        team_name = request.form.get('team_name')

        # 2. Sayısal Verileri Güvenli Çevir
        rank = safe_int(request.form.get('team_rank'))
        mp = safe_int(request.form.get('team_matches_played'))
        wins = safe_int(request.form.get('team_wins'))
        losses = safe_int(request.form.get('team_losses'))
        ps = safe_int(request.form.get('team_points_scored'))
        pc = safe_int(request.form.get('team_points_conceded'))
        points = safe_int(request.form.get('team_total_points'))

        # 3. Otomatik Hesaplamalar
        # Averaj hesapla (Atılan - Yenen)
        total_goal_diff = ps - pc

        # 4. Kontrol: Zorunlu alanlar boş mu?
        if not league or not team_name:
            flash("Hata: Lig adı ve Takım adı zorunludur!", "danger")
            return redirect(url_for('standings_page'))

        # 5. SQL Sorgusu
        # Tablonda 'team_home_points' ve 'team_home_goal_difference' zorunlu değilse 
        # veya null olabiliyorsa sorun yok, ama biz garanti olsun diye 0 gönderiyoruz.
        sql = """
            INSERT INTO standings (
                league, 
                team_name, 
                team_rank, 
                team_matches_played, 
                team_wins, 
                team_losses, 
                team_points_scored, 
                team_points_conceded, 
                team_total_points,
                team_total_goal_difference,
                team_home_points, 
                team_home_goal_difference
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0)
        """
        
        # Verileri tuple olarak hazırla
        values = (
            league, team_name, rank, 
            mp, wins, losses, 
            ps, pc, points, 
            total_goal_diff
        )

        # Sorguyu çalıştır
        db_api.execute(sql, values)

        flash(f"{team_name} başarıyla eklendi.", "success")
        
    except Exception as e:
        # HATAYI TERMİNALE YAZDIR (Debug için çok önemli)
        print(f"####################")
        print(f"SQL EKLEME HATASI: {e}")
        print(f"####################")
        flash(f"Bir hata oluştu. Detaylar terminalde yazıyor.", "danger")

    return redirect(url_for('standings_page'))
@app.route('/standings/edit', methods=['POST'])
def edit_standing():
    try:
        # 1. Hedef Satırı Bulmak İçin ESKİ Veriler
        original_league = request.form.get('original_league')
        original_team_name = request.form.get('original_team_name')

        # 2. Güncellenecek YENİ Veriler
        new_league = request.form.get('league')
        new_team_name = request.form.get('team_name')
        
        # Sayısal veriler
        rank = safe_int(request.form.get('team_rank'))
        mp = safe_int(request.form.get('team_matches_played'))
        wins = safe_int(request.form.get('team_wins'))
        losses = safe_int(request.form.get('team_losses'))
        ps = safe_int(request.form.get('team_points_scored'))
        pc = safe_int(request.form.get('team_points_conceded'))
        points = safe_int(request.form.get('team_total_points'))

        # Averajı tekrar hesapla
        total_goal_diff = ps - pc

        # 3. SQL UPDATE Sorgusu
        sql = """
            UPDATE standings
            SET 
                league = %s,
                team_name = %s,
                team_rank = %s,
                team_matches_played = %s,
                team_wins = %s,
                team_losses = %s,
                team_points_scored = %s,
                team_points_conceded = %s,
                team_total_points = %s,
                team_total_goal_difference = %s
            WHERE league = %s AND team_name = %s
        """
        
        db_api.execute(sql, (
            new_league, new_team_name, rank, mp, wins, losses, 
            ps, pc, points, total_goal_diff,
            original_league, original_team_name
        ))

        flash(f"{new_team_name} başarıyla güncellendi.", "success")
        
    except Exception as e:
        print(f"GÜNCELLEME HATASI: {e}")
        flash("Güncelleme sırasında hata oluştu.", "danger")

    # --- EKLENEN KISIM: FİLTRELERİ KORUMA ---
    return_url = request.form.get('return_url')
    if return_url:
        return redirect(return_url)
    
    return redirect(url_for('standings_page'))
@app.route('/standings/delete', methods=['POST'])
def delete_standing():
    try:
        # Silinecek satırın kimlik bilgileri
        league = request.form.get('league')
        team_name = request.form.get('team_name')

        # SQL Sorgusu
        sql = "DELETE FROM standings WHERE league = %s AND team_name = %s"
        db_api.execute(sql, (league, team_name))

        flash(f"{team_name} başarıyla silindi.", "warning") # Uyarı rengi (sarı)
        
    except Exception as e:
        print(f"SİLME HATASI: {e}")
        flash(f"Silme sırasında hata oluştu: {e}", "danger")

    # Filtrelerin olduğu sayfaya geri dön
    return_url = request.form.get('return_url')
    if return_url:
        return redirect(return_url)
    return redirect(url_for('standings_page'))
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