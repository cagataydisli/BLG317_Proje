from flask import Flask, render_template

# Flask uygulamasını başlat
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
    # Burada veritabanından oyuncu verileri çekilecek
    # Şimdilik taslak sayfayı göster:
    return render_template('players.html')

# 2. Takımlar (Talip Demir)
@app.route('/teams')
def teams_page():
    # Burada veritabanından takım verileri çekilecek
    # Şimdilik taslak sayfayı göster:
    return render_template('teams.html')

# 3. Maçlar (Celil Aslan)
@app.route('/matches')
def matches_page():
    # Burada veritabanından maç verileri çekilecek
    # Şimdilik taslak sayfayı göster:
    return render_template('matches.html')

# 4. Teknik Ekip (Musa Can Turgut)
@app.route('/staff')
def staff_page():
    # Burada veritabanından teknik ekip verileri çekilecek
    # Şimdilik taslak sayfayı göster:
    return render_template('staff.html')

# 5. Puan Durumu (Emir Şahin)
@app.route('/standings')
def standings_page():
    # Burada veritabanından puan durumu verileri çekilecek
    # Şimdilik taslak sayfayı göster:
    return render_template('standings.html')


# Uygulamayı çalıştırmak için
if __name__ == '__main__':
    app.run(debug=True)