import database.db as db_api


def reset_players_table():
    print("🧹 Oyuncular tablosu temizleniyor...")
    try:
        # Önce tabloyu tamamen uçuralım (CASCADE: bağlı verileri de temizler)
        db_api.execute("DROP TABLE IF EXISTS Players CASCADE;")
        print("✅ Eski tablo silindi.")

        # Şimdi init_db.py dosyasını çağırıp yeniden oluşturtalım
        # (Burada init_db modülünü import edip fonksiyonunu çağıracağız)
        import init_db
        init_db.init_db()
        print("🎉 Tablo sıfırdan oluşturuldu ve veriler yüklendi!")

    except Exception as e:
        print(f"❌ Bir hata oluştu: {e}")


if __name__ == "__main__":
    reset_players_table()