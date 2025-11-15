from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os

# --- Veritabanı Yapılandırması BAŞLANGIÇ ---

# Proje klasörünün tam yolunu al
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Veritabanı dosyasının yolu ve adı
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/blg317_proje'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Gereksiz uyarıları kapatır

# Veritabanı nesnesini (db) Flask uygulamamıza bağlıyoruz
db = SQLAlchemy(app)

# --- Veritabanı Yapılandırması SON ---


# --- Veritabanı Modelleri (Tablolar) BAŞLANGIÇ ---

# Şimdi proje önerinizdeki  tabloları Python sınıfı olarak tanımlıyoruz.

# Talip'in Modeli
class Teams(db.Model):
    __tablename__ = 'teams'
    team_id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False)
    team_city = db.Column(db.String(100))
    team_year = db.Column(db.Integer)

    # Diğer tablolarla ilişkileri tanımla (örn: Bir takımın çok oyuncusu olabilir)
    players = db.relationship('Players', backref='team', lazy=True)
    staff = db.relationship('TechnicalStaff', backref='team', lazy=True)
    home_matches = db.relationship('Matches', foreign_keys='Matches.home_team_id', backref='home_team', lazy=True)
    away_matches = db.relationship('Matches', foreign_keys='Matches.away_team_id', backref='away_team', lazy=True)
    standings = db.relationship('Standings', backref='team', lazy=True)


# Çağatay'ın Modeli (SENİN MODELİN)
class Players(db.Model):
    __tablename__ = 'players'
    player_id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(100), nullable=False)
    player_birthdate = db.Column(db.String(50))  # Tarih için db.Date de kullanılabilir
    player_height = db.Column(db.Integer)

    # Yabancı Anahtar (Foreign Key) [cite: 8]
    team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'), nullable=False)


# Celil'in Modeli
class Matches(db.Model):
    __tablename__ = 'matches'
    match_id = db.Column(db.Integer, primary_key=True)
    match_date = db.Column(db.String(50))
    match_hour = db.Column(db.String(50))
    match_score = db.Column(db.String(50))

    # Yabancı Anahtarlar [cite: 14]
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'), nullable=False)


# Musa Can'ın Modeli
class TechnicalStaff(db.Model):
    __tablename__ = 'technical_staff'
    staff_id = db.Column(db.Integer, primary_key=True)
    nationality = db.Column(db.String(100))
    technic_member_name = db.Column(db.String(100), nullable=False)
    technic_member_role = db.Column(db.String(100))

    # Yabancı Anahtar [cite: 17]
    team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'), nullable=False)


# Emir'in Modeli
class Standings(db.Model):
    __tablename__ = 'standings'
    # Bileşik Anahtar (Composite Key)
    id = db.Column(db.Integer, primary_key=True)  # Basit bir PK eklemek genellikle daha iyidir
    team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'), nullable=False)
    league = db.Column(db.String(100), nullable=False)  # Öneride 'league' PK'nin parçasıydı
    team_matches_played = db.Column(db.Integer)
    team_wins = db.Column(db.Integer)
    team_loses = db.Column(db.Integer)
    rank = db.Column(db.Integer)

    # Bileşik anahtar kuralını ekle
    __table_args__ = (db.UniqueConstraint('team_id', 'league', name='_team_league_uc'),)


# --- Veritabanı Modelleri (Tablolar) SON ---


# Ana Sayfa Route'u
@app.route('/')
def index():
    return render_template('index.html')

# --- Görev Dağılımı Alanları ---
# Herkes kendi sorumluluğundaki bölümü geliştirecek.

# 1. Oyuncular (Çağatay Dişli)
# '/players' artık ana menüyü gösteriyor
@app.route('/players')
def players_page():
    # Bu fonksiyon artık veritabanı sorgusu yapmıyor.
    # Sadece 'players.html' menü sayfasını gösteriyor.
    return render_template('players.html')


# '/players/table' tabloyu gösteren YENİ route
@app.route('/players/table')
def players_table():
    # Veritabanından tüm oyuncuları çekme işini artık bu fonksiyon yapıyor.
    all_players = Players.query.all()

    # Veriyi yeni 'players_table.html' şablonuna gönderiyoruz.
    return render_template('players_table.html', players=all_players)

# 2. Takımlar (Talip Demir)
@app.route('/teams')
def teams_page():
    # Burada veritabanından takım verileri çekilecek
    all_teams = Teams.query.all()
    # Şimdilik taslak sayfayı göster:
    return render_template('teams.html', teams=all_teams)

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