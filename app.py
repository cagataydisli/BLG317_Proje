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


<<<<<<< Updated upstream
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
=======
# --- 1. TAKIM ANA MENÜ (Yönlendirme) ---
@app.route('/teams')
def teams_menu():
    return redirect(url_for('teams_table_page'))


# --- 2. TAKIM TABLO GÖRÜNÜMÜ (/teams/table) ---
@app.route('/teams/table')
def teams_table_page():
    # Tüm verileri çekiyoruz (En güncel lig en üstte)
>>>>>>> Stashed changes
    query = """
        SELECT 
            team_id, team_name, team_city, team_year, 
            saloon_name, saloon_capacity, league, team_url
        FROM team_data
        ORDER BY team_name
    """
<<<<<<< Updated upstream
    rows = db_api.query(query)
    
=======

    try:
        rows = db_api.query(query)
    except Exception as e:
        print(f"Sorgu Hatası: {e}")
        rows = []

>>>>>>> Stashed changes
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


<<<<<<< Updated upstream
# 3. Maçlar (Celil Aslan)
@app.route('/matches')
def matches_page():
    # Maç verilerini çekerken Ev Sahibi ve Deplasman takımlarının isimlerini getirmek için
    # teams tablosuna İKİ KEZ join yapıyoruz (t1: home, t2: away)
    query = """
=======
# --- 3. TAKIM EKLEME İŞLEMİ (/teams/add) ---
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
        
        # Staff ID
        s_id = data.get('staff_id')
        s_id = int(s_id) if s_id and s_id.strip() else None

        # Kapasite
        s_cap = data.get('saloon_capacity')
        s_cap = int(s_cap) if s_cap and s_cap.strip() else None

        # Yıl
        t_year = data.get('team_year')
        t_year = int(t_year) if t_year and t_year.strip() else None

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


# --- 4. TAKIM SİLME İŞLEMİ (/teams/delete/ID) ---
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
    
    query = f"""
>>>>>>> Stashed changes
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
# =========================================================
# 4. Teknik Ekip (Musa Can Turgut) – LIST + FILTER + PAGINATION
# =========================================================
# 4. Teknik Ekip (Musa Can Turgut) – LIST + FILTER + PAGINATION
# =========================================================
@app.route('/staff')
def staff_page():
<<<<<<< Updated upstream
    # --- Sayfa numarası ---
    page_param = request.args.get('page', '1')
    try:
        page = int(page_param)
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    limit = 50
    offset = (page - 1) * limit

    # --- Filtre parametreleri ---
    search = (request.args.get('search') or '').strip()
    team_filter = (request.args.get('team') or '').strip()
    role_filter = (request.args.get('role') or '').strip()

    where_clauses = []
    params = []

    if search:
        where_clauses.append("LOWER(tr.technic_member_name) LIKE %s")
        params.append(f"%{search.lower()}%")

    if team_filter:
        where_clauses.append("t.team_name = %s")
        params.append(team_filter)

    if role_filter:
        where_clauses.append("tr.technic_member_role = %s")
        params.append(role_filter)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    # --- Toplam satır sayısı (filtreli) ---
    count_sql = f"""
        SELECT COUNT(*)
        FROM technic_roster tr
        JOIN teams t ON tr.team_id = t.team_id
        {where_sql}
    """
    total_rows = db_api.query(count_sql, tuple(params))[0][0]

    # --- Asıl veri (filtreli + sayfalı) ---
    data_sql = f"""
=======

    # -----------------------------
    # 1. Filtre Parametreleri
    # -----------------------------
    f_name = request.args.get('name')
    f_role = request.args.get('role')
    f_team = request.args.get('team')
    f_league = request.args.get('league')

    # Sayfalama
    try:
        page = int(request.args.get('page', 1))
        per_page = 20
    except:
        page = 1
        per_page = 20

    # -----------------------------
    # 2. BASE SQL (ŞEMAYA UYGUN)
    # -----------------------------
    base_sql = """
>>>>>>> Stashed changes
        SELECT 
            tr.staff_id,
            tr.technic_member_name, 
            tr.technic_member_role, 
            t.team_name,
            t.team_id,
            tr.league
        FROM technic_roster tr
<<<<<<< Updated upstream
        JOIN teams t ON tr.team_id = t.team_id
        {where_sql}
        ORDER BY t.team_name, tr.technic_member_name
        LIMIT %s OFFSET %s
    """
    data_params = params + [limit, offset]
    rows = db_api.query(data_sql, tuple(data_params))

=======
        LEFT JOIN teams t ON tr.team_id = t.team_id
    """
    
    # -----------------------------
    # 3. FİLTRELER
    # -----------------------------
    where_clauses = []
    params = []
    
    if f_name:
        where_clauses.append("tr.technic_member_name ILIKE %s")
        params.append(f"%{f_name}%")

    if f_role:
        where_clauses.append("tr.technic_member_role ILIKE %s")
        params.append(f"%{f_role}%")

    if f_team:
        where_clauses.append("t.team_name ILIKE %s")
        params.append(f"%{f_team}%")

    if f_league:
        where_clauses.append("tr.league ILIKE %s")
        params.append(f"%{f_league}%")

    if where_clauses:
        base_sql += " WHERE " + " AND ".join(where_clauses)

    base_sql += " ORDER BY t.team_name NULLS LAST, tr.technic_member_name"

    # -----------------------------
    # 4. QUERY ÇALIŞTIR
    # -----------------------------
    try:
        if params:
            rows = db_api.query(base_sql, tuple(params))
        else:
            rows = db_api.query(base_sql)
    except Exception as e:
        print(f"Staff query error: {e}")
        rows = []

    # -----------------------------
    # 5. PYTHON LIST
    # -----------------------------
>>>>>>> Stashed changes
    staff = []
    for r in rows:
        staff.append({
<<<<<<< Updated upstream
            "staff_id": row[0],
            "name": row[1],
            "role": row[2],
            "team_name": row[3],
            "league": row[4],
        })

    # --- Filtre dropdownları için tüm takımlar / roller ---
    teams_rows = db_api.query("""
        SELECT DISTINCT team_name
        FROM Teams
        WHERE team_name IS NOT NULL
        ORDER BY team_name ASC
    """)
    filter_teams = [r[0] for r in teams_rows]

    roles_rows = db_api.query("""
        SELECT DISTINCT technic_member_role
        FROM technic_roster
        WHERE technic_member_role IS NOT NULL
        ORDER BY technic_member_role ASC
    """)
    roles = [r[0] for r in roles_rows]

    # Yeni staff ekleme modalı için team_id + isim listesi
    teams_full_rows = db_api.query("""
        SELECT team_id, team_name, league
        FROM Teams
        ORDER BY league DESC, team_name ASC
    """)
    teams = []
    for r in teams_full_rows:
        teams.append({
            "team_id": r[0],
            "team_name": r[1],
            "league": r[2],
        })

    # --- Toplam sayfa sayısı ---
    total_pages = (total_rows + limit - 1) // limit if total_rows > 0 else 1

    return render_template(
        'staff.html',
        staff=staff,
        teams=teams,
        filter_teams=filter_teams,
        roles=roles,
        current_page=page,
        total_pages=total_pages,
        search=search,
        selected_team=team_filter,
        selected_role=role_filter,
    )

# --- Teknik Ekip EKLEME ---
@app.route('/staff/add', methods=['POST'])
def add_staff():
    try:
        data = request.form
        name = data.get('technic_member_name')
        role = data.get('technic_member_role')
        league = data.get('league')
        team_id = data.get('team_id')
        team_url = data.get('team_url')

        if not name or not team_id:
            return "Name ve Team ID zorunludur.", 400

        team_id_val = int(team_id) if team_id and team_id.strip() else None

        sql = """
            INSERT INTO technic_roster (team_id, team_url, league, technic_member_name, technic_member_role)
            VALUES (%s, %s, %s, %s, %s)
        """
        db_api.execute(sql, (team_id_val, team_url, league, name, role))

        return redirect(url_for('staff_page'))
    except Exception as e:
        return f"Ekleme Hatası: {e}", 500


# --- Teknik Ekip SİLME ---
@app.route('/staff/delete/<int:staff_id>', methods=['POST'])
=======
            "staff_id": r[0],
            "name": r[1],
            "role": r[2],
            "team_name": r[3] if r[3] else "Takım Yok",
            "team_id": r[4],
            "league": r[5]
        })

    # -----------------------------
    # 6. PAGINATION
    # -----------------------------
    total_count = len(staff)
    total_pages = max(1, math.ceil(total_count / per_page))

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * per_page
    end = start + per_page
    staff_paginated = staff[start:end]

    # -----------------------------
    # 7. TEMPLATE
    # -----------------------------
    return render_template(
        'staff.html',
        staff=staff_paginated,
        current_page=page,
        total_pages=total_pages,
        filters=request.args
    )


# -------------------------
# STAFF ADD
# -------------------------
@app.route('/staff/add', methods=['POST'])
@login_required
def add_staff():
    try:
        data = request.form

        name = data.get('name')
        role = data.get('role')
        team_id = data.get('team_id')
        league = data.get('league')
        team_url = data.get('team_url')

        if not team_id or team_id.strip() == "":
            team_id = None

        sql = """
            INSERT INTO technic_roster 
            (technic_member_name, technic_member_role, team_id, league, team_url)
            VALUES (%s, %s, %s, %s, %s)
        """

        db_api.execute(sql, (name, role, team_id, league, team_url))
        flash("Teknik ekip üyesi eklendi.", "success")

    except Exception as e:
        print(f"Staff Add Error: {e}")
        flash(f"Hata: {e}", "danger")

    return redirect(url_for('staff_page'))


# -------------------------
# STAFF UPDATE
# -------------------------
@app.route('/staff/update', methods=['POST'])
@login_required
def update_staff():
    try:
        data = request.form

        staff_id = data.get('staff_id')
        name = data.get('name')
        role = data.get('role')
        team_id = data.get('team_id')
        league = data.get('league')
        team_url = data.get('team_url')

        if not team_id or team_id.strip() == "":
            team_id = None

        sql = """
            UPDATE technic_roster
            SET technic_member_name = %s,
                technic_member_role = %s,
                team_id = %s,
                league = %s,
                team_url = %s
            WHERE staff_id = %s
        """

        db_api.execute(sql, (name, role, team_id, league, team_url, staff_id))
        flash("Teknik ekip üyesi güncellendi.", "success")

    except Exception as e:
        print(f"Staff Update Error: {e}")
        flash(f"Hata: {e}", "danger")

    return redirect(url_for('staff_page'))


# -------------------------
# STAFF DELETE
# -------------------------
@app.route('/staff/delete/<int:staff_id>', methods=['POST'])
@login_required
>>>>>>> Stashed changes
def delete_staff(staff_id):
    try:
        sql = "DELETE FROM technic_roster WHERE staff_id = %s"
        db_api.execute(sql, (staff_id,))
<<<<<<< Updated upstream
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# 5. Puan Durumu (Emir Şahin)
=======
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# -------------------------
# NUMERIC FILTER HELPER
# -------------------------
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
>>>>>>> Stashed changes
@app.route('/standings')
def standings_page():
<<<<<<< Updated upstream
    # Güvenli sıralama sütunları
=======
    # 1: Lig listesini çek
    league_sql = "SELECT DISTINCT league FROM standings ORDER BY league DESC"
    try:
        league_rows = db_api.query(league_sql)
        leagues = [{"league": row[0]} for row in league_rows]
    except Exception as e:
        print(f"Lig listesi hatası: {e}")
        leagues = []

    # 2: Parametreleri al
    selected_league = request.args.get('league')

>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
    # Optional limit
=======
>>>>>>> Stashed changes
    try:
        limit = int(request.args.get('limit', 0))
        if limit <= 0 or limit > 1000:
            limit = None
    except ValueError:
        limit = None

<<<<<<< Updated upstream
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
=======
    # 3: Ana sorgu
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

    if selected_league:
        sql += " WHERE s.league = %s"
        params.append(selected_league)
    
    sql += f" ORDER BY s.{sort} {order_sql}"

    if limit:
        sql += " LIMIT %s"
        params.append(limit)

    rows = db_api.query(sql, tuple(params))

    cols = [
        "league","team_rank","team_name","team_matches_played","team_wins","team_losses",
        "team_points_scored","team_points_conceded","team_home_points",
        "team_home_goal_difference","team_total_goal_difference","team_total_points",
        "team_url"
    ]
>>>>>>> Stashed changes

    standings = [dict(zip(cols, row)) for row in rows]

    if request.args.get('format') == 'json':
        return jsonify(standings)
        
<<<<<<< Updated upstream
    return render_template('standings.html', standings=standings)
=======
    return render_template(
        'standings.html', 
        standings=standings, 
        leagues=leagues, 
        current_league=selected_league
    )
>>>>>>> Stashed changes


if __name__ == '__main__':
    app.run(debug=True)
