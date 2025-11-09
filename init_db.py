from app import app, db, Teams, Players
import os

DATABASE_FILE = 'database.db'

print("Uygulama bağlamı açılıyor...")
with app.app_context():
    # Adım 1: Mevcut DB dosyasını sil (varsa)
    if os.path.exists(DATABASE_FILE):
        print("Mevcut 'database.db' dosyası siliniyor...")
        os.remove(DATABASE_FILE)

    # Adım 2: Tabloları sıfırdan oluştur
    print("Tablolar oluşturuluyor (db.create_all)...")
    db.create_all()

    print("Veriler oluşturuluyor...")
    try:
        # 1. Takımlar
        takim1 = Teams(team_name="Anadolu Efes", team_city="İstanbul", team_year=1976)
        takim2 = Teams(team_name="Fenerbahçe Beko", team_city="İstanbul", team_year=1913)

        # 2. Oyuncular
        player1 = Players(player_name="Shane Larkin", player_birthdate="1992-10-02", player_height=182, team=takim1)
        player2 = Players(player_name="Scottie Wilbekin", player_birthdate="1993-04-05", player_height=188, team=takim2)
        player3 = Players(player_name="Melih Mahmutoğlu", player_birthdate="1990-05-12", player_height=191, team=takim2)

        print("Veriler oturuma ekleniyor...")
        db.session.add_all([takim1, takim2, player1, player2, player3])

        print("Değişiklikler veritabanına kaydediliyor (commit)...")
        db.session.commit()

        print("\n--- BAŞARILI ---")
        print("Veritabanı oluşturuldu ve 2 takım, 3 oyuncu eklendi.")

    except Exception as e:
        print(f"\n--- BİR HATA OLDU ---: {e}")
        db.session.rollback()

print("İşlem tamamlandı.")