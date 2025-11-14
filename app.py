from flask import request, Flask, render_template, jsonify
import database.db as db_api   # yeni helper
# --- Veritabanı Yapılandırması BAŞLANGIÇ ---


app = Flask(__name__)



# Ana Sayfa Route'u
@app.route('/')
def index():
    return render_template('index.html')

# --- Görev Dağılımı Alanları ---
# Herkes kendi sorumluluğundaki bölümü geliştirecek.

# 1. Oyuncular (Çağatay Dişli)
@app.route('/players')
def players_page():

    # 'all_players' listesini 'players' adıyla HTML şablonuna gönderiyoruz.
    return render_template('players.html', players=all_players)

# 2. Takımlar (Talip Demir)
@app.route('/teams')
def teams_page():
    # Şimdilik taslak sayfayı göster:
    return render_template('teams.html', teams=all_teams)

# 3. Maçlar (Celil Aslan)
@app.route('/matches')
def matches_page():
    # Şimdilik taslak sayfayı göster:
    return render_template('matches.html')

# 4. Teknik Ekip (Musa Can Turgut)
@app.route('/staff')
def staff_page():
    # Şimdilik taslak sayfayı göster:
    return render_template('staff.html')

# 5. Puan Durumu (Emir Şahin)
@app.route('/standings')
def standings_page():
    
    # güvenli sıralama için izin verilen sütunlar
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

    # optional limit (safe int with an upper bound)
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

    # rows -> list of dicts for template/JSON
    standings = [dict(zip(cols, row)) for row in rows]

    if request.args.get('format') == 'json':
        return jsonify(standings)
    return render_template('standings.html', standings=standings)


# Uygulamayı çalıştırmak için
if __name__ == '__main__':
    app.run(debug=True)