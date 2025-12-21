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
               p.league, t.team_name, p.team_url, p.team_id,
               p.player_foot, p.player_bio
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
        p_id, p_name, p_height, p_birth, p_league, t_name, t_url, t_id, p_foot, p_bio = row

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
            "player_foot": p_foot,
            "player_bio": p_bio,
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


# --- 7. OYUNCU İSTATİSTİKLERİ (ADVANCED QUERY) ---
@app.route('/players/stats')
def players_stats_page():
    # Correlated Subquery:
    # Her oyuncu için, o oyuncunun bulunduğu takımın boy ortalamasını (İç Sorgu) hesapla.
    # Eğer oyuncunun boyu, takım ortalamasından büyükse listele.
    
    query = """
        SELECT 
            p.player_name, 
            p.player_height, 
            t.team_name, 
            (
                SELECT AVG(CAST(NULLIF(regexp_replace(p2.player_height, '[^0-9]', '', 'g'), '') AS INTEGER)) 
                FROM Players p2 
                WHERE p2.team_id = p.team_id
            ) as team_avg_height
        FROM Players p
        JOIN Teams t ON p.team_id = t.team_id
        WHERE 
            CAST(NULLIF(regexp_replace(p.player_height, '[^0-9]', '', 'g'), '') AS INTEGER) > 
            (
                SELECT AVG(CAST(NULLIF(regexp_replace(p3.player_height, '[^0-9]', '', 'g'), '') AS INTEGER)) 
                FROM Players p3 
                WHERE p3.team_id = p.team_id
            )
        ORDER BY t.team_name, p.player_name
    """
    
    try:
        rows = db_api.query(query)
    except Exception as e:
        print(f"Stats Query Error: {e}")
        rows = []
        
    stats = []
    for row in rows:
        # Clean height for calculation
        try:
            # "190 cm" -> 190
            p_h_clean = int(''.join(filter(str.isdigit, str(row[1]))))
        except:
            p_h_clean = 0
            
        t_avg_clean = float(row[3]) if row[3] else 0
        diff = int(p_h_clean - t_avg_clean)

        stats.append({
            "player_name": row[0],
            "player_height": row[1],
            "team_name": row[2],
            "team_avg_height": round(row[3], 1) if row[3] else 0,
            "diff": diff
        })
        
    # --- EKSTRA ADVANCED QUERIES ---

    # 1. En Skorer Takımın Oyuncuları (Nested)
    q1 = """
        SELECT player_name, team_name, player_height 
        FROM Players 
        WHERE team_id = (
            SELECT team_id FROM standings ORDER BY team_points_scored DESC LIMIT 1
        )
    """
    
    # 2. Galibiyetsiz Hocalar (Exists/Join)
    q2 = """
        SELECT tr.technic_member_name, t.team_name 
        FROM technic_roster tr
        JOIN Teams t ON tr.team_id = t.team_id
        WHERE t.team_name IN (
            SELECT team_name FROM standings WHERE team_wins = 0
        )
    """

    # 3. Maç Yapmamış Takımlar (NOT IN)
    q3 = """
        SELECT team_name, league 
        FROM Teams 
        WHERE team_id NOT IN (
            SELECT home_team_id FROM Matches 
            UNION 
            SELECT away_team_id FROM Matches
        )
    """

    try:
        top_scorer_players = db_api.query(q1)
    except: top_scorer_players = []

    try:
        winless_coaches = db_api.query(q2)
    except: winless_coaches = []

    try:
        inactive_teams = db_api.query(q3)
    except: inactive_teams = []

    return render_template('players_stats.html', 
                           stats=stats,
                           top_scorer_players=top_scorer_players,
                           winless_coaches=winless_coaches,
                           inactive_teams=inactive_teams)


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
        birthdate = data.get('player_birthdate')
        league = data.get('league')
        foot = data.get('player_foot')
        bio = data.get('player_bio')

        # SQL Ekleme Sorgusu (player_id sütununu ve değerini kaldırdık)
        sql = """
            INSERT INTO Players (player_name, team_id, player_height, player_birthdate, league, player_foot, player_bio)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        if not team_id:
            team_id = None

        # execute kısmından da player_id'yi siliyoruz
        db_api.execute(sql, (player_name, team_id, height, birthdate, league, foot, bio))

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
        foot = data.get('player_foot')
        bio = data.get('player_bio')

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
                league = %s,
                player_foot = %s,
                player_bio = %s
            WHERE player_id = %s
        """

        db_api.execute(sql, (player_name, team_id, height, birthdate, league, foot, bio, player_id))

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
    # 1. Filtre için URL'den gelen 'season' parametresini al
    selected_season = request.args.get('season')

    # 2. Dropdown için tüm benzersiz sezonları çek (Örn: bsl-2024, bsl-2023...)
    seasons_query = "SELECT DISTINCT league FROM Teams ORDER BY league DESC"
    try:
        season_rows = db_api.query(seasons_query)
        # Veriyi düz listeye çevir: ['bsl-2024-2025', 'bsl-2023-2024', ...]
        all_seasons = [row[0] for row in season_rows if row[0]]
    except Exception as e:
        print(f"Sezon listesi hatası: {e}")
        all_seasons = []

    # 3. Takımları Çeken Ana Sorgu
    base_query = """
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
    """
    
    # Eğer bir sezon seçildiyse WHERE ekle, seçilmediyse hepsini getir
    if selected_season and selected_season != "all":
        query = base_query + " WHERE league = %s ORDER BY team_name ASC"
        params = (selected_season,)
    else:
        query = base_query + " ORDER BY league DESC, team_name ASC"
        params = ()

    try:
        rows = db_api.query(query, params)
    except Exception as e:
        print(f"Sorgu Hatası: {e}")
        rows = []

    # 4. Verileri HTML'e göndermek için sözlüğe çevir
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

    # 5. HTML'e hem takımları, hem sezon listesini, hem de seçili sezonu gönderiyoruz
    return render_template('teams.html', teams=teams, seasons=all_seasons, current_season=selected_season)


# --- 3. EKLEME İŞLEMİ (/teams/add) ---
@app.route('/teams/add', methods=['POST'])
@login_required
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
@login_required
def delete_team(team_id):
    try:
        sql = "DELETE FROM Teams WHERE team_id = %s"
        db_api.execute(sql, (team_id,))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
@app.route('/teams/update', methods=['POST'])
@login_required
def update_team():
    try:
        data = request.form

        sql = """
            UPDATE Teams
            SET team_name = %s,
                league = %s,
                team_city = %s,
                team_year = %s,
                team_url = %s,
                staff_id = %s,
                saloon_name = %s,
                saloon_capacity = %s,
                saloon_address = %s
            WHERE team_id = %s
        """

        db_api.execute(sql, (
            data.get('team_name'),
            data.get('league'),
            data.get('team_city'),
            data.get('team_year') or None,
            data.get('team_url'),
            data.get('staff_id') or None,
            data.get('saloon_name'),
            data.get('saloon_capacity') or None,
            data.get('saloon_address'),
            data.get('team_id')
        ))

        flash("Takım başarıyla güncellendi.", "success")

    except Exception as e:
        print(f"TEAM UPDATE ERROR: {e}")
        flash("Takım güncellenirken hata oluştu.", "danger")

    return redirect(url_for('teams_table_page'))


# =====================================================================
# 3. MATCHES MODULE (Celil Aslan - 150210703)
# =====================================================================
# This module demonstrates:
# - Full CRUD operations (Create, Read, Update, Delete)
# - Complex 4+ table JOINs
# - Nested Subqueries
# - LEFT/RIGHT OUTER JOINs  
# - Set Operations (UNION, INTERSECT, EXCEPT)
# - Aggregations with GROUP BY and HAVING
# - Advanced filtering and pagination
# =====================================================================

@app.route('/matches')
def matches_page():
    """
    Main matches listing page with advanced filtering, pagination, and analytics.
    Demonstrates: Multi-table JOINs, Aggregations, Subqueries
    """
    # ==================== FILTER PARAMETERS ====================
    sort_by = request.args.get('sort', 'match_date')
    order = request.args.get('order', 'desc')
    fmt = request.args.get('format', 'html')
    
    # Pagination parameters
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
    except ValueError:
        page, per_page = 1, 50
    
    # Advanced filter parameters
    search_team = request.args.get('search_team', '').strip()
    selected_league = request.args.get('league', '')
    selected_city = request.args.get('city', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    score_filter = request.args.get('score_filter', '')  # home_wins, away_wins, high_scoring
    min_score_diff = request.args.get('min_score_diff', '')
    selected_weeks = request.args.getlist('weeks')  # Checkbox multi-select

    # NEW FILTERS
    home_team_filter = request.args.get('home_team', '')
    away_team_filter = request.args.get('away_team', '')
    any_team_filter = request.args.get('any_team', '')
    match_status = request.args.get('match_status', '')  # played, unplayed
    selected_saloon = request.args.get('saloon', '')
    game_closeness = request.args.get('game_closeness', '')  # close, blowout
    date_preset = request.args.get('date_preset', '')  # today, week, month
    total_score_min = request.args.get('total_score_min', '')
    total_score_max = request.args.get('total_score_max', '')
    
    # SQL injection protection - use mapping for complete control
    SORT_COLUMNS = {
        'match_date': 'm.match_date',
        'match_week': 'm.match_week',
        'league': 'm.league',
        'match_city': 'm.match_city',
        'home_score': 'm.home_score',
        'away_score': 'm.away_score'
    }
    sort_column = SORT_COLUMNS.get(sort_by, 'm.match_date')
    order = 'DESC' if order.lower() == 'desc' else 'ASC'
    
    # ==================== DROPDOWN DATA ====================
    # Fetch ALL teams for dropdowns (need all team_ids for edit modal to work correctly)
    # Teams with same name but different seasons have different IDs
    teams_query = """
        SELECT team_id, team_name, league
        FROM Teams
        ORDER BY team_name, league DESC
    """
    teams_rows = db_api.query(teams_query)
    teams = [{'team_id': row[0], 'team_name': row[1], 'league': row[2]} for row in teams_rows]

    # Fetch unique leagues for filter
    leagues_query = "SELECT DISTINCT league FROM Matches WHERE league IS NOT NULL ORDER BY league DESC"
    leagues = [row[0] for row in db_api.query(leagues_query)]

    # Fetch unique cities for filter
    cities_query = "SELECT DISTINCT match_city FROM Matches WHERE match_city IS NOT NULL ORDER BY match_city"
    cities = [row[0] for row in db_api.query(cities_query)]

    # Fetch unique weeks for checkbox filter (natural sort: NS 01, NS 02, ... NS 10, NS 11)
    weeks_query = """
        SELECT match_week FROM (
            SELECT DISTINCT match_week FROM Matches WHERE match_week IS NOT NULL
        ) w
        ORDER BY 
            SUBSTRING(match_week FROM '^[A-Za-z]+'),
            CAST(NULLIF(REGEXP_REPLACE(match_week, '[^0-9]', '', 'g'), '') AS INTEGER) NULLS LAST
    """
    all_weeks = [row[0] for row in db_api.query(weeks_query)]

    # NEW: Fetch saloons with their cities for filtering
    saloons_query = """
        SELECT DISTINCT match_city, match_saloon 
        FROM Matches 
        WHERE match_saloon IS NOT NULL AND match_saloon != '' AND match_city IS NOT NULL
        ORDER BY match_city, match_saloon
    """
    saloons_with_cities = [{'city': row[0], 'saloon': row[1]} for row in db_api.query(saloons_query)]
    all_saloons = list(set([s['saloon'] for s in saloons_with_cities]))  # Unique saloons for backward compat
    
    # ==================== DYNAMIC WHERE CLAUSE ====================
    where_clauses = ["1=1"]
    params = []

    # Date preset quick filter (MUST BE FIRST - overrides date_from/date_to)
    from datetime import datetime, timedelta
    if date_preset == 'today':
        today = datetime.now().date()
        where_clauses.append("m.match_date = %s")
        params.append(today)
    elif date_preset == 'week':
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        where_clauses.append("m.match_date >= %s AND m.match_date <= %s")
        params.extend([week_ago, today])
    elif date_preset == 'month':
        today = datetime.now().date()
        month_ago = today - timedelta(days=30)
        where_clauses.append("m.match_date >= %s AND m.match_date <= %s")
        params.extend([month_ago, today])
    else:
        # Manual date range filter (only if no preset selected)
        if date_from:
            where_clauses.append("m.match_date >= %s")
            params.append(date_from)
        if date_to:
            where_clauses.append("m.match_date <= %s")
            params.append(date_to)

    # Team name search (searches both home and away teams)
    if search_team:
        where_clauses.append("(t1.team_name ILIKE %s OR t2.team_name ILIKE %s)")
        params.extend([f"%{search_team}%", f"%{search_team}%"])

    # NEW: Specific home team filter (by team name, not ID)
    if home_team_filter:
        where_clauses.append("t1.team_name = %s")
        # Get team name from the dropdown value (which is actually a team_id, we need to look it up)
        try:
            team_name_query = "SELECT team_name FROM Teams WHERE team_id = %s LIMIT 1"
            team_name_result = db_api.query(team_name_query, (int(home_team_filter),))
            if team_name_result:
                params.append(team_name_result[0][0])
        except:
            pass

    # NEW: Specific away team filter (by team name, not ID)
    if away_team_filter:
        where_clauses.append("t2.team_name = %s")
        try:
            team_name_query = "SELECT team_name FROM Teams WHERE team_id = %s LIMIT 1"
            team_name_result = db_api.query(team_name_query, (int(away_team_filter),))
            if team_name_result:
                params.append(team_name_result[0][0])
        except:
            pass

    # NEW: Any team involved filter (by team name, not ID)
    if any_team_filter:
        where_clauses.append("(t1.team_name = %s OR t2.team_name = %s)")
        try:
            team_name_query = "SELECT team_name FROM Teams WHERE team_id = %s LIMIT 1"
            team_name_result = db_api.query(team_name_query, (int(any_team_filter),))
            if team_name_result:
                team_name = team_name_result[0][0]
                params.extend([team_name, team_name])
        except:
            pass

    # League filter
    if selected_league:
        where_clauses.append("m.league = %s")
        params.append(selected_league)

    # City filter
    if selected_city:
        where_clauses.append("m.match_city = %s")
        params.append(selected_city)

    # NEW: Saloon/Arena filter
    if selected_saloon:
        where_clauses.append("m.match_saloon = %s")
        params.append(selected_saloon)

    # NEW: Match status filter (played/unplayed)
    if match_status == 'played':
        where_clauses.append("m.home_score IS NOT NULL AND m.away_score IS NOT NULL")
    elif match_status == 'unplayed':
        where_clauses.append("m.home_score IS NULL OR m.away_score IS NULL")

    # Score filter (radio button)
    if score_filter == 'home_wins':
        where_clauses.append("m.home_score > m.away_score")
    elif score_filter == 'away_wins':
        where_clauses.append("m.home_score < m.away_score")
    elif score_filter == 'high_scoring':
        where_clauses.append("(m.home_score + m.away_score) >= 180")

    # NEW: Game closeness filter
    if game_closeness == 'close':
        # Close games: decided by 5 points or less
        where_clauses.append("ABS(m.home_score - m.away_score) <= 5 AND m.home_score IS NOT NULL")
    elif game_closeness == 'blowout':
        # Blowouts: 20+ point difference
        where_clauses.append("ABS(m.home_score - m.away_score) >= 20 AND m.home_score IS NOT NULL")

    # NEW: Total score range filter
    if total_score_min:
        try:
            min_val = int(total_score_min)
            where_clauses.append("(m.home_score + m.away_score) >= %s")
            params.append(min_val)
        except ValueError:
            pass
    if total_score_max:
        try:
            max_val = int(total_score_max)
            where_clauses.append("(m.home_score + m.away_score) <= %s")
            params.append(max_val)
        except ValueError:
            pass

    # Minimum score difference
    if min_score_diff:
        try:
            diff = int(min_score_diff)
            where_clauses.append("ABS(m.home_score - m.away_score) >= %s")
            params.append(diff)
        except ValueError:
            pass

    # Week multi-select (checkboxes)
    if selected_weeks:
        placeholders = ', '.join(['%s'] * len(selected_weeks))
        where_clauses.append(f"m.match_week IN ({placeholders})")
        params.extend(selected_weeks)
    
    where_sql = " AND ".join(where_clauses)
    
    # ==================== COUNT QUERY FOR PAGINATION ====================
    count_query = f"""
        SELECT COUNT(*) FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        WHERE {where_sql}
    """
    total_count = db_api.query(count_query, tuple(params))[0][0]
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    # Ensure valid page number
    if page < 1: page = 1
    if page > total_pages: page = total_pages
    
    offset = (page - 1) * per_page
    
    # ==================== MAIN QUERY (2-Table JOIN) ====================
    main_query = f"""
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
        WHERE {where_sql}
        ORDER BY {sort_column} {order}, m.match_hour ASC
        LIMIT %s OFFSET %s
    """
    query_params = tuple(params) + (per_page, offset)
    rows = db_api.query(main_query, query_params)
    
    cols = ['match_id', 'match_date', 'match_hour', 'home_team', 'home_score', 
            'away_score', 'away_team', 'match_saloon', 'league', 'match_week',
            'match_city', 'home_team_id', 'away_team_id']
    matches = [dict(zip(cols, row)) for row in rows]
    
    # ==================== COMPLEX QUERY 1: Team Performance (GROUP BY + HAVING + Aggregations) ====================
    # Real-world meaningful stat: Team performance summary with wins, losses, averages
    # Use the selected league filter, or auto-detect from filtered matches
    if selected_league:
        analytics_league = selected_league
    else:
        # Auto-detect most common league from current filter results
        league_detect_query = f"""
            SELECT m.league, COUNT(*) as cnt
            FROM matches m
            JOIN teams t1 ON m.home_team_id = t1.team_id
            JOIN teams t2 ON m.away_team_id = t2.team_id
            WHERE {where_sql}
            GROUP BY m.league
            ORDER BY cnt DESC
            LIMIT 1
        """
        league_result = db_api.query(league_detect_query, tuple(params))
        analytics_league = league_result[0][0] if league_result else 'bsl-2024-2025'

    analytics_display_season = analytics_league.replace('bsl-', '').upper() if analytics_league else 'All Seasons'

    analytics_query = """
        WITH ranked_matches AS (
            -- FIXED: Deduplicate by team IDs instead of scores to prevent data loss
            -- Each match appears twice in data with swapped home/away teams
            -- Keep only the first one based on team_id pair + date
            SELECT
                m.match_id,
                m.match_date,
                m.home_score,
                m.away_score,
                m.home_team_id,
                m.away_team_id,
                ROW_NUMBER() OVER (
                    PARTITION BY m.match_date,
                                 LEAST(m.home_team_id, m.away_team_id),
                                 GREATEST(m.home_team_id, m.away_team_id)
                    ORDER BY m.match_id
                ) as rn
            FROM Matches m
            WHERE m.league = %s AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL
        ),
        unique_matches AS (
            SELECT match_id, match_date, home_score, away_score, home_team_id, away_team_id
            FROM ranked_matches
            WHERE rn = 1
        ),
        match_results AS (
            -- Home team results
            SELECT 
                t.team_name,
                um.match_id,
                um.home_score AS scored, 
                um.away_score AS conceded,
                CASE WHEN um.home_score > um.away_score THEN 1 ELSE 0 END AS won,
                CASE WHEN um.home_score < um.away_score THEN 1 ELSE 0 END AS lost
            FROM unique_matches um
            JOIN Teams t ON um.home_team_id = t.team_id
            UNION ALL
            -- Away team results  
            SELECT 
                t.team_name,
                um.match_id,
                um.away_score AS scored, 
                um.home_score AS conceded,
                CASE WHEN um.away_score > um.home_score THEN 1 ELSE 0 END AS won,
                CASE WHEN um.away_score < um.home_score THEN 1 ELSE 0 END AS lost
            FROM unique_matches um
            JOIN Teams t ON um.away_team_id = t.team_id
        ),
        team_stats AS (
            SELECT 
                team_name,
                COUNT(*) as games_played,
                SUM(won) as wins,
                SUM(lost) as losses,
                ROUND(AVG(scored)::numeric, 1) as avg_points_scored,
                ROUND(AVG(conceded)::numeric, 1) as avg_points_conceded
            FROM match_results
            GROUP BY team_name
            HAVING COUNT(*) >= 3
        )
        SELECT 
            team_name,
            games_played,
            wins,
            losses,
            ROUND((wins * 100.0 / games_played)::numeric, 1) as win_pct,
            avg_points_scored,
            avg_points_conceded,
            ROUND((avg_points_scored - avg_points_conceded)::numeric, 1) as point_diff
        FROM team_stats
        ORDER BY win_pct DESC, point_diff DESC
    """
    analytics_rows = db_api.query(analytics_query, (analytics_league,))
    analytics = [{
        'team_name': row[0],
        'games_played': row[1],
        'wins': row[2],
        'losses': row[3],
        'win_pct': float(row[4]) if row[4] else 0,
        'avg_points_scored': float(row[5]) if row[5] else 0,
        'avg_points_conceded': float(row[6]) if row[6] else 0,
        'point_diff': float(row[7]) if row[7] else 0
    } for row in analytics_rows]
    
    # ==================== COMPLEX QUERY 2: 4+ Table JOIN ====================
    # Joins: Matches + Teams(home) + Teams(away) + Standings(home) + Standings(away)
    # Shows matches with team standings info
    complex_join_query = """
        SELECT 
            m.match_id,
            t1.team_name AS home_team,
            t2.team_name AS away_team,
            m.home_score,
            m.away_score,
            COALESCE(s1.team_rank, 0) AS home_team_rank,
            COALESCE(s2.team_rank, 0) AS away_team_rank,
            COALESCE(s1.team_wins, 0) AS home_team_wins,
            COALESCE(s2.team_wins, 0) AS away_team_wins,
            m.league
        FROM Matches m
        INNER JOIN Teams t1 ON m.home_team_id = t1.team_id
        INNER JOIN Teams t2 ON m.away_team_id = t2.team_id
        LEFT OUTER JOIN Standings s1 ON t1.team_name = s1.team_name AND m.league = s1.league
        LEFT OUTER JOIN Standings s2 ON t2.team_name = s2.team_name AND m.league = s2.league
        WHERE m.home_score IS NOT NULL 
          AND m.away_score IS NOT NULL
          AND m.league = %s
        ORDER BY m.match_date DESC
        LIMIT 10
    """
    try:
        complex_join_rows = db_api.query(complex_join_query, (analytics_league,))
        complex_join_data = [{
            'match_id': row[0],
            'home_team': row[1],
            'away_team': row[2],
            'home_score': row[3],
            'away_score': row[4],
            'home_rank': row[5],
            'away_rank': row[6],
            'home_wins': row[7],
            'away_wins': row[8],
            'league': row[9]
        } for row in complex_join_rows]
    except Exception as e:
        print(f"Complex join error: {e}")
        complex_join_data = []
    
    # ==================== COMPLEX QUERY 3: NESTED SUBQUERY ====================
    # Find matches with above-average home team performance
    nested_subquery = """
        WITH ranked_matches AS (
            SELECT m.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY m.match_date,
                                    LEAST(m.home_team_id, m.away_team_id),
                                    GREATEST(m.home_team_id, m.away_team_id)
                       ORDER BY m.match_id
                   ) as rn
            FROM Matches m
            WHERE m.league = %s AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL
        ),
        unique_matches AS (
            SELECT * FROM ranked_matches WHERE rn = 1
        ),
        league_avg AS (
            SELECT AVG(home_score) as avg_score FROM unique_matches
        )
        SELECT
            m.match_id,
            t1.team_name AS home_team,
            t2.team_name AS away_team,
            m.home_score,
            m.away_score,
            m.match_date,
            la.avg_score
        FROM unique_matches m
        JOIN Teams t1 ON m.home_team_id = t1.team_id
        JOIN Teams t2 ON m.away_team_id = t2.team_id
        CROSS JOIN league_avg la
        WHERE m.home_score > la.avg_score
        ORDER BY m.home_score DESC
        LIMIT 20
    """
    try:
        nested_rows = db_api.query(nested_subquery, (analytics_league,))
        nested_data = [{
            'match_id': row[0],
            'home_team': row[1],
            'away_team': row[2],
            'home_score': row[3],
            'away_score': row[4],
            'match_date': row[5]
        } for row in nested_rows]
    except Exception as e:
        print(f"Nested subquery error: {e}")
        nested_data = []
    
    # ==================== COMPLEX QUERY 4: LEFT OUTER JOIN ====================
    # Shows teams participation statistics - demonstrates OUTER JOIN
    # Some teams may have registered but not played all their matches
    outer_join_query = """
        WITH ranked_matches AS (
            SELECT m.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY m.match_date,
                                    LEAST(m.home_team_id, m.away_team_id),
                                    GREATEST(m.home_team_id, m.away_team_id)
                       ORDER BY m.match_id
                   ) as rn
            FROM Matches m
            WHERE m.league = %s AND m.home_score IS NOT NULL
        ),
        unique_matches AS (
            SELECT * FROM ranked_matches WHERE rn = 1
        ),
        league_teams AS (
            SELECT DISTINCT home_team_id AS team_id FROM unique_matches
            UNION
            SELECT DISTINCT away_team_id AS team_id FROM unique_matches
        )
        SELECT 
            t.team_id,
            t.team_name,
            %s as league,
            COUNT(m.match_id) AS total_matches,
            COALESCE(SUM(CASE WHEN m.home_team_id = t.team_id AND m.home_score > m.away_score THEN 1
                              WHEN m.away_team_id = t.team_id AND m.away_score > m.home_score THEN 1
                              ELSE 0 END), 0) AS wins
        FROM Teams t
        INNER JOIN league_teams lt ON t.team_id = lt.team_id
        LEFT OUTER JOIN unique_matches m ON (t.team_id = m.home_team_id OR t.team_id = m.away_team_id)
        GROUP BY t.team_id, t.team_name
        ORDER BY total_matches DESC, wins DESC
        LIMIT 16
    """
    try:
        outer_join_rows = db_api.query(outer_join_query, (analytics_league, analytics_league))
        outer_join_data = [{
            'team_id': row[0],
            'team_name': row[1],
            'league': row[2],
            'total_matches': row[3],
            'wins': row[4]
        } for row in outer_join_rows]
    except Exception as e:
        print(f"Outer join error: {e}")
        outer_join_data = []
    
    # ==================== COMPLEX QUERY 5: SET OPERATIONS (UNION) ====================
    # Teams that won at home UNION Teams that won away
    set_operation_query = """
        WITH ranked_matches AS (
            SELECT m.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY m.match_date,
                                    LEAST(m.home_team_id, m.away_team_id),
                                    GREATEST(m.home_team_id, m.away_team_id)
                       ORDER BY m.match_id
                   ) as rn
            FROM Matches m
            WHERE m.league = %s AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL
        ),
        unique_matches AS (
            SELECT * FROM ranked_matches WHERE rn = 1
        ),
        home_wins AS (
            SELECT DISTINCT t.team_name, 'Home Win' AS win_type, m.match_date, m.home_score, m.away_score, t2.team_name as opponent
            FROM unique_matches m
            JOIN Teams t ON m.home_team_id = t.team_id
            JOIN Teams t2 ON m.away_team_id = t2.team_id
            WHERE m.home_score > m.away_score
        ),
        away_wins AS (
            SELECT DISTINCT t.team_name, 'Away Win' AS win_type, m.match_date, m.away_score as home_score, m.home_score as away_score, t2.team_name as opponent
            FROM unique_matches m
            JOIN Teams t ON m.away_team_id = t.team_id
            JOIN Teams t2 ON m.home_team_id = t2.team_id
            WHERE m.away_score > m.home_score
        )
        SELECT * FROM (
            SELECT * FROM home_wins
            UNION ALL
            SELECT * FROM away_wins
        ) combined
        ORDER BY match_date DESC
        LIMIT 20
    """
    try:
        set_op_rows = db_api.query(set_operation_query, (analytics_league,))
        set_operation_data = [{
            'team_name': row[0],
            'win_type': row[1],
            'match_date': row[2],
            'team_score': row[3],
            'opponent_score': row[4],
            'opponent': row[5]
        } for row in set_op_rows]
    except Exception as e:
        print(f"Set operation error: {e}")
        set_operation_data = []
    
    # ==================== HEAD-TO-HEAD STATISTICS ====================
    # FIXED: Normalize team pairs to avoid duplicate rivalries
    h2h_query = """
        WITH ranked_matches AS (
            SELECT m.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY m.match_date,
                                    LEAST(m.home_team_id, m.away_team_id),
                                    GREATEST(m.home_team_id, m.away_team_id)
                       ORDER BY m.match_id
                   ) as rn
            FROM Matches m
            WHERE m.league = %s AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL
        ),
        unique_matches AS (
            SELECT * FROM ranked_matches WHERE rn = 1
        ),
        all_matchups AS (
            SELECT
                CASE WHEN t1.team_name < t2.team_name THEN t1.team_name ELSE t2.team_name END AS team1,
                CASE WHEN t1.team_name < t2.team_name THEN t2.team_name ELSE t1.team_name END AS team2,
                CASE
                    WHEN t1.team_name < t2.team_name THEN
                        CASE WHEN m.home_score > m.away_score THEN 1 ELSE 0 END
                    ELSE
                        CASE WHEN m.away_score > m.home_score THEN 1 ELSE 0 END
                END AS team1_won,
                CASE
                    WHEN t1.team_name < t2.team_name THEN
                        CASE WHEN m.home_score < m.away_score THEN 1 ELSE 0 END
                    ELSE
                        CASE WHEN m.away_score < m.home_score THEN 1 ELSE 0 END
                END AS team2_won,
                CASE WHEN m.home_score = m.away_score THEN 1 ELSE 0 END AS is_draw
            FROM unique_matches m
            JOIN Teams t1 ON m.home_team_id = t1.team_id
            JOIN Teams t2 ON m.away_team_id = t2.team_id
        )
        SELECT
            team1,
            team2,
            COUNT(*) AS total_games,
            SUM(team1_won) AS team1_wins,
            SUM(team2_won) AS team2_wins,
            SUM(is_draw) AS draws
        FROM all_matchups
        GROUP BY team1, team2
        HAVING COUNT(*) >= 2
        ORDER BY total_games DESC, team1_wins DESC
        LIMIT 20
    """
    try:
        h2h_rows = db_api.query(h2h_query, (analytics_league,))
        h2h_data = [{
            'team1': row[0],
            'team2': row[1],
            'total_games': row[2],
            'team1_wins': row[3],
            'team2_wins': row[4],
            'draws': row[5]
        } for row in h2h_rows]
    except Exception as e:
        print(f"H2H error: {e}")
        h2h_data = []
    
    if fmt == 'json':
        return jsonify({
            'matches': matches,
            'pagination': {'page': page, 'per_page': per_page, 'total': total_count, 'pages': total_pages},
            'analytics': analytics
        })
    
    # ==================== QUICK STATS FOR DASHBOARD ====================
    quick_stats_query = """
        WITH ranked_matches AS (
            SELECT m.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY m.match_date,
                                    LEAST(m.home_team_id, m.away_team_id),
                                    GREATEST(m.home_team_id, m.away_team_id)
                       ORDER BY m.match_id
                   ) as rn
            FROM Matches m
            WHERE m.league = %s AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL
        ),
        unique_matches AS (
            SELECT * FROM ranked_matches WHERE rn = 1
        )
        SELECT
            COUNT(*) AS total_matches,
            COUNT(CASE WHEN home_score > away_score THEN 1 END) AS home_wins,
            COUNT(CASE WHEN home_score < away_score THEN 1 END) AS away_wins,
            COUNT(CASE WHEN home_score = away_score THEN 1 END) AS draws,
            ROUND(AVG(home_score + away_score)::numeric, 1) AS avg_total_score,
            MAX(home_score + away_score) AS highest_score,
            (SELECT COUNT(DISTINCT team_id) FROM (
                SELECT home_team_id AS team_id FROM unique_matches
                UNION
                SELECT away_team_id AS team_id FROM unique_matches
            ) t) AS unique_teams
        FROM unique_matches
    """
    try:
        stats_row = db_api.query(quick_stats_query, (analytics_league,))[0]
        quick_stats = {
            'total_matches': stats_row[0],
            'home_wins': stats_row[1],
            'away_wins': stats_row[2],
            'home_win_pct': round(stats_row[1] * 100 / stats_row[0], 1) if stats_row[0] > 0 else 0,
            'away_win_pct': round(stats_row[2] * 100 / stats_row[0], 1) if stats_row[0] > 0 else 0,
            'avg_total_score': float(stats_row[4]) if stats_row[4] else 0,
            'highest_score': stats_row[5],
        }
    except:
        quick_stats = {}

    # ==================== NEW: BIGGEST BLOWOUTS ====================
    blowouts_query = """
        WITH ranked_matches AS (
            SELECT m.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY m.match_date,
                                    LEAST(m.home_team_id, m.away_team_id),
                                    GREATEST(m.home_team_id, m.away_team_id)
                       ORDER BY m.match_id
                   ) as rn
            FROM Matches m
            WHERE m.league = %s AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL
        ),
        unique_matches AS (
            SELECT * FROM ranked_matches WHERE rn = 1
        )
        SELECT
            t1.team_name AS winner,
            t2.team_name AS loser,
            CASE WHEN m.home_score > m.away_score THEN m.home_score ELSE m.away_score END AS winner_score,
            CASE WHEN m.home_score > m.away_score THEN m.away_score ELSE m.home_score END AS loser_score,
            ABS(m.home_score - m.away_score) AS point_diff,
            m.match_date,
            CASE WHEN m.home_score > m.away_score THEN 'Home' ELSE 'Away' END AS winner_location
        FROM unique_matches m
        JOIN Teams t1 ON m.home_team_id = t1.team_id
        JOIN Teams t2 ON m.away_team_id = t2.team_id
        WHERE ABS(m.home_score - m.away_score) >= 20
        ORDER BY point_diff DESC, m.match_date DESC
        LIMIT 10
    """
    try:
        blowouts_rows = db_api.query(blowouts_query, (analytics_league,))
        biggest_blowouts = [{
            'winner': row[0],
            'loser': row[1],
            'winner_score': row[2],
            'loser_score': row[3],
            'point_diff': row[4],
            'match_date': row[5],
            'winner_location': row[6]
        } for row in blowouts_rows]
    except Exception as e:
        print(f"Blowouts query error: {e}")
        biggest_blowouts = []

    # ==================== NEW: HOME VS AWAY PERFORMANCE ====================
    home_away_query = """
        WITH ranked_matches AS (
            SELECT m.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY m.match_date,
                                    LEAST(m.home_team_id, m.away_team_id),
                                    GREATEST(m.home_team_id, m.away_team_id)
                       ORDER BY m.match_id
                   ) as rn
            FROM Matches m
            WHERE m.league = %s AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL
        ),
        unique_matches AS (
            SELECT * FROM ranked_matches WHERE rn = 1
        ),
        home_stats AS (
            SELECT
                t.team_name,
                COUNT(*) as home_games,
                SUM(CASE WHEN m.home_score > m.away_score THEN 1 ELSE 0 END) as home_wins,
                ROUND(AVG(m.home_score)::numeric, 1) as avg_home_scored
            FROM unique_matches m
            JOIN Teams t ON m.home_team_id = t.team_id
            GROUP BY t.team_name
        ),
        away_stats AS (
            SELECT
                t.team_name,
                COUNT(*) as away_games,
                SUM(CASE WHEN m.away_score > m.home_score THEN 1 ELSE 0 END) as away_wins,
                ROUND(AVG(m.away_score)::numeric, 1) as avg_away_scored
            FROM unique_matches m
            JOIN Teams t ON m.away_team_id = t.team_id
            GROUP BY t.team_name
        )
        SELECT
            COALESCE(h.team_name, a.team_name) as team_name,
            COALESCE(h.home_games, 0) as home_games,
            COALESCE(h.home_wins, 0) as home_wins,
            COALESCE(h.avg_home_scored, 0) as avg_home_scored,
            COALESCE(a.away_games, 0) as away_games,
            COALESCE(a.away_wins, 0) as away_wins,
            COALESCE(a.avg_away_scored, 0) as avg_away_scored,
            CASE WHEN h.home_games > 0 THEN ROUND((h.home_wins * 100.0 / h.home_games)::numeric, 1) ELSE 0 END as home_win_pct,
            CASE WHEN a.away_games > 0 THEN ROUND((a.away_wins * 100.0 / a.away_games)::numeric, 1) ELSE 0 END as away_win_pct
        FROM home_stats h
        FULL OUTER JOIN away_stats a ON h.team_name = a.team_name
        WHERE COALESCE(h.home_games, 0) + COALESCE(a.away_games, 0) >= 5
        ORDER BY (COALESCE(h.home_games, 0) + COALESCE(a.away_games, 0)) DESC
        LIMIT 12
    """
    try:
        home_away_rows = db_api.query(home_away_query, (analytics_league,))
        home_away_stats = [{
            'team_name': row[0],
            'home_games': row[1],
            'home_wins': row[2],
            'avg_home_scored': float(row[3]) if row[3] else 0,
            'away_games': row[4],
            'away_wins': row[5],
            'avg_away_scored': float(row[6]) if row[6] else 0,
            'home_win_pct': float(row[7]) if row[7] else 0,
            'away_win_pct': float(row[8]) if row[8] else 0
        } for row in home_away_rows]
    except Exception as e:
        print(f"Home/Away stats error: {e}")
        home_away_stats = []

    # ==================== NEW: LEAGUE AVERAGE FOR NESTED QUERY ====================
    try:
        league_avg_query = """
            WITH ranked_matches AS (
                SELECT m.*,
                       ROW_NUMBER() OVER (
                           PARTITION BY m.match_date,
                                        LEAST(m.home_team_id, m.away_team_id),
                                        GREATEST(m.home_team_id, m.away_team_id)
                           ORDER BY m.match_id
                       ) as rn
                FROM Matches m
                WHERE m.league = %s AND m.home_score IS NOT NULL
            ),
            unique_matches AS (
                SELECT * FROM ranked_matches WHERE rn = 1
            )
            SELECT ROUND(AVG(home_score)::numeric, 1) as avg_home_score
            FROM unique_matches
        """
        avg_result = db_api.query(league_avg_query, (analytics_league,))
        league_avg_home_score = float(avg_result[0][0]) if avg_result and avg_result[0][0] else 0
    except:
        league_avg_home_score = 0

    return render_template('matches.html',
        matches=matches,
        teams=teams,
        analytics=analytics,
        complex_join_data=complex_join_data,
        nested_data=nested_data,
        outer_join_data=outer_join_data,
        set_operation_data=set_operation_data,
        h2h_data=h2h_data,
        quick_stats=quick_stats,
        analytics_display_season=analytics_display_season,
        # NEW ANALYTICS
        biggest_blowouts=biggest_blowouts,
        home_away_stats=home_away_stats,
        league_avg_home_score=league_avg_home_score,
        # Pagination data
        current_page=page,
        total_pages=total_pages,
        per_page=per_page,
        total_count=total_count,
        # Filter data for dropdowns
        leagues=leagues,
        cities=cities,
        all_weeks=all_weeks,
        all_saloons=all_saloons,
        saloons_with_cities=saloons_with_cities,
        # Selected filter values (to maintain state)
        selected_league=selected_league,
        selected_city=selected_city,
        selected_weeks=selected_weeks,
        search_team=search_team,
        date_from=date_from,
        date_to=date_to,
        score_filter=score_filter,
        min_score_diff=min_score_diff,
        # NEW: Additional filter states
        home_team_filter=home_team_filter,
        away_team_filter=away_team_filter,
        any_team_filter=any_team_filter,
        match_status=match_status,
        selected_saloon=selected_saloon,
        game_closeness=game_closeness,
        date_preset=date_preset,
        total_score_min=total_score_min,
        total_score_max=total_score_max
    )

# --- MATCHES: CREATE (Add Match) ---
@app.route('/matches/add', methods=['POST'])
@login_required
def add_match():
    try:
        data = request.form
        
        # Extract form data
        home_team_id = data.get('home_team_id')
        away_team_id = data.get('away_team_id')
        match_date = data.get('match_date') or None  # Convert empty string to None
        match_hour = data.get('match_hour') or None  # Convert empty string to None
        match_week = data.get('match_week') or None
        league = data.get('league')
        match_city = data.get('match_city') or None
        match_saloon = data.get('match_saloon') or None
        home_score = data.get('home_score')
        away_score = data.get('away_score')
        
        # Validation: League is required
        if not league or not league.strip():
            flash("Error: League is required!", "danger")
            return redirect(url_for('matches_page'))
        
        # Validation: Check if home and away teams are different
        if home_team_id == away_team_id:
            flash("Error: Home and away teams cannot be the same!", "danger")
            return redirect(url_for('matches_page'))
        
        # AUTO-GENERATE match_id: Format = "1EA" + number (e.g., 1EA263, 1EA4509, 1EA10000...)
        # Find the highest existing match_id number and increment
        max_id_query = """
            SELECT COALESCE(MAX(CAST(SUBSTRING(match_id FROM 4) AS INTEGER)), 4999) 
            FROM Matches 
            WHERE match_id ~ '^1EA[0-9]+$'
        """
        max_result = db_api.query(max_id_query)
        print(f"DEBUG max_result: {max_result}")
        
        # Handle result - COALESCE ensures we always get a number
        next_num = max_result[0][0] + 1
        print(f"DEBUG next_num: {next_num}")
        
        # Generate match_id: "1EA" + next number
        match_id = f"1EA{next_num}"
        print(f"DEBUG match_id: {match_id}")
        
        # Ensure uniqueness (in case of conflicts)
        existing = db_api.query("SELECT 1 FROM Matches WHERE match_id = %s", (match_id,))
        while existing and len(existing) > 0:
            next_num += 1
            match_id = f"1EA{next_num}"
            existing = db_api.query("SELECT 1 FROM Matches WHERE match_id = %s", (match_id,))
        
        # Handle scores: convert to int or None
        try:
            home_score = int(home_score) if home_score and home_score.strip() else None
            away_score = int(away_score) if away_score and away_score.strip() else None
            
            # Validate: Both scores must be set or both empty
            if (home_score is None) != (away_score is None):
                flash("Error: Both scores must be set or both must be empty!", "danger")
                return redirect(url_for('matches_page'))
        except ValueError:
            flash("Error: Scores must be valid numbers!", "danger")
            return redirect(url_for('matches_page'))
        
        # SQL Insert (now includes scores)
        sql = """
            INSERT INTO Matches (
                match_id, home_team_id, away_team_id, match_date, match_hour,
                home_score, away_score, match_week, league, match_city, match_saloon
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        db_api.execute(sql, (
            match_id, home_team_id, away_team_id, match_date, match_hour,
            home_score, away_score, match_week, league, match_city, match_saloon
        ))
        
        flash(f"Match successfully added! (ID: {match_id})", "success")
        return redirect(url_for('matches_page'))
        
    except Exception as e:
        print(f"ADD MATCH ERROR: {e}")
        flash(f"Error adding match: {e}", "danger")
        return redirect(url_for('matches_page'))

# --- MATCHES: UPDATE (Edit Match/Scores) ---
@app.route('/matches/update', methods=['POST'])
@login_required
def update_match():
    try:
        data = request.form
        
        # Extract form data (convert empty strings to None for SQL NULL)
        match_id = data.get('match_id')
        home_team_id = data.get('home_team_id')
        away_team_id = data.get('away_team_id')
        match_date = data.get('match_date') or None
        match_hour = data.get('match_hour') or None
        home_score = data.get('home_score')
        away_score = data.get('away_score')
        match_week = data.get('match_week') or None
        league = data.get('league') or None
        match_city = data.get('match_city') or None
        match_saloon = data.get('match_saloon') or None
        
        # Validation: Teams cannot be the same
        if home_team_id == away_team_id:
            flash("Error: Home and away teams cannot be the same!", "danger")
            return redirect(url_for('matches_page'))
        
        # Convert scores to int or None with validation
        try:
            home_score = int(home_score) if home_score and home_score.strip() else None
            away_score = int(away_score) if away_score and away_score.strip() else None

            # VALIDATION: Both scores must be set or both must be empty (consistency check)
            if (home_score is None) != (away_score is None):
                flash("Error: Both scores must be set or both must be empty!", "danger")
                return redirect(url_for('matches_page'))

            # Validate scores are non-negative
            if home_score is not None and home_score < 0:
                flash("Error: Home score cannot be negative!", "danger")
                return redirect(url_for('matches_page'))
            if away_score is not None and away_score < 0:
                flash("Error: Away score cannot be negative!", "danger")
                return redirect(url_for('matches_page'))

            # Validate reasonable score range (basketball typically 0-200)
            if home_score is not None and home_score > 300:
                flash("Error: Home score seems unrealistic (>300)!", "danger")
                return redirect(url_for('matches_page'))
            if away_score is not None and away_score > 300:
                flash("Error: Away score seems unrealistic (>300)!", "danger")
                return redirect(url_for('matches_page'))
        except ValueError:
            flash("Error: Scores must be valid numbers!", "danger")
            return redirect(url_for('matches_page'))
        
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
@login_required
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
        SELECT 
            s.league, 
            s.team_rank, 
            s.team_name, 
            s.team_matches_played, 
            s.team_wins, 
            s.team_losses, 
            s.team_points_scored, 
            s.team_points_conceded, 
            s.team_home_points, 
            s.team_home_goal_difference, 
            s.team_total_goal_difference, 
            s.team_total_points,
            s.team_id,   -- <--- YENİ EKLENEN KISIM
            t.team_url
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
        "league",
        "team_rank",
        "team_name",
        "team_matches_played",
        "team_wins",
        "team_losses",
        "team_points_scored",
        "team_points_conceded",
        "team_home_points",
        "team_home_goal_difference",
        "team_total_goal_difference",
        "team_total_points",
        "team_id",  # <--- YENİ EKLENEN KISIM
        "team_url"
    ]
    standings = [dict(zip(cols, row)) for row in rows]

    return render_template(
        'standings.html', 
        standings=standings, 
        leagues=leagues,
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
        # --- TEAM PLAYER AGE STATISTICS ---
    from datetime import datetime

    today = datetime.now()
    ages = []

    for p in players:
        birth = p.get("player_birthdate")
        if birth and isinstance(birth, str) and len(birth.strip()) >= 8:
            try:
                bdate = datetime.strptime(birth.strip(), "%d.%m.%Y")
                age = today.year - bdate.year - (
                    (today.month, today.day) < (bdate.month, bdate.day)
                )
                ages.append({
                    "name": p["player_name"],
                    "age": age
                })
            except:
                pass

        # İstatistikleri üret
        if ages:
            avg_age = round(sum(a["age"] for a in ages) / len(ages), 1)
            youngest = min(ages, key=lambda x: x["age"])
            oldest = max(ages, key=lambda x: x["age"])
        else:
            avg_age = "-"
            youngest = None
            oldest = None

        team_stats = {
            "player_count": len(players),
            "avg_age": avg_age,
            "youngest": youngest,
            "oldest": oldest
        }

    # Verileri yeni bir HTML sayfasına gönderiyoruz
    return render_template('team_players.html', team=team_info, players=players, stats= team_stats)





if __name__ == '__main__':
    app.run(debug=True)