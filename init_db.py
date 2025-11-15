# init_db.py (Yeni .xlsx'ten dönen CSV dosyaları için güncellendi)

import pandas as pd
import os
from app import app, db, Teams, Players
# Henüz kullanmasak da diğer modelleri de import edelim
from app import Matches, TechnicalStaff, Standings
import numpy as np  # Sayısal işlemler için (NaN kontrolü vb.)

# --- CSV Dosya Yolları ---
basedir = os.path.abspath(os.path.dirname(__file__))
TABLES_FOLDER_PATH = os.path.join(basedir, 'tables')

TEAMS_CSV_PATH = os.path.join(TABLES_FOLDER_PATH, 'team_data.csv')
PLAYERS_CSV_PATH = os.path.join(TABLES_FOLDER_PATH, 'player_data.csv')

print("Uygulama bağlamı açılıyor...")
with app.app_context():
    # Adım 1: Mevcut tabloları sil ve oluştur
    print("Mevcut MySQL tabloları siliniyor (drop_all)...")
    db.drop_all()
    print("Tablolar yeniden oluşturuluyor (create_all)...")
    db.create_all()

    try:
        # --- BÖLÜM 1: Takımları Yükle (ÖNCE BU YAPILMALI) ---
        print(f"\n{TEAMS_CSV_PATH} dosyasından takımlar okunuyor...")

        # 'team_id'nin benzersiz (unique) olmasını sağlamamız lazım
        # Aynı team_id'ye sahip kayıtlar varsa, ilkini al
        teams_df = pd.read_csv(TEAMS_CSV_PATH)
        teams_df = teams_df.drop_duplicates(subset=['team_id'], keep='first')

        team_objects = []
        for index, row in teams_df.iterrows():
            # CSV'deki sütun adlarına göre modelimizi eşleştiriyoruz
            new_team = Teams(
                team_id=row['team_id'],  # PK'yı doğrudan CSV'den alıyoruz
                team_name=row['team_name'],
                team_city=row['team_city'],
                team_year=row['team_year']
            )
            team_objects.append(new_team)

        # ÖNEMLİ: PK'yı manuel atadığımız için 'bulk_save_objects' yerine 'add_all'
        # ve 'commit' kullanmak daha güvenli olabilir, ancak 'bulk' daha hızlıdır.
        db.session.add_all(team_objects)
        db.session.commit()  # Takımlar eklendi, artık oyuncular eklenebilir.

        print(f"{len(team_objects)} benzersiz takım başarıyla veritabanına eklendi.")

        # --- BÖLÜM 2: Oyuncuları Yükle (SENİN TABLON) ---
        print(f"\n{PLAYERS_CSV_PATH} dosyasından oyuncular okunuyor...")

        # Benzersiz oyuncular
        players_df = pd.read_csv(PLAYERS_CSV_PATH)
        players_df = players_df.drop_duplicates(subset=['player_id'], keep='first')

        # Az önce eklediğimiz takımların ID'lerini bir set olarak alalım
        # Sadece veritabanında var olan takımlara oyuncu ekleyebiliriz
        valid_team_ids = {team.team_id for team in team_objects}

        player_objects = []
        atlanan_oyuncu_sayisi = 0

        for index, row in players_df.iterrows():
            # Oyuncunun CSV'deki team_id'si, Takımlar tablomuzda var mı?
            if row['team_id'] not in valid_team_ids:
                # print(f"UYARI: {row['team_id']} ID'li takım bulunamadı. Oyuncu '{row['player_name']}' atlanıyor.")
                atlanan_oyuncu_sayisi += 1
                continue

            # Veritabanı modelin 'player_height' için Integer (sayı) bekliyor.
            # CSV'de 'unknown' gibi metinler olabilir, bunları temizlemeliyiz.
            player_height_raw = str(row['player_height'])
            player_height_clean = ''.join(filter(str.isdigit, player_height_raw))

            if player_height_clean:
                player_height = int(player_height_clean)
            else:
                player_height = None  # Eğer 'unknown' ise veritabanında NULL (boş) olsun

            # CSV'deki sütun adlarına göre modelimizi eşleştiriyoruz
            new_player = Players(
                player_id=row['player_id'],  # PK'yı doğrudan CSV'den alıyoruz
                player_name=row['player_name'],
                player_birthdate=str(row['player_birthdate']),  # String olarak alıyoruz
                player_height=player_height,  # Temizlenmiş sayı
                team_id=row['team_id']  # FK'yı (Yabancı Anahtar) doğrudan alıyoruz
            )
            player_objects.append(new_player)

        db.session.add_all(player_objects)
        db.session.commit()

        print(f"{len(player_objects)} oyuncu başarıyla veritabanına eklendi.")
        if atlanan_oyuncu_sayisi > 0:
            print(f"({atlanan_oyuncu_sayisi} oyuncu, takım ID'si eşleşmediği için atlandı.)")

        print("\n--- BAŞARIYLA TAMAMLANDI ---")
        print("Veritabanı oluşturuldu ve CSV verileri başarıyla yüklendi.")

    except FileNotFoundError as e:
        print(f"\n--- HATA: Dosya Bulunamadı ---: {e}")
        print("Lütfen 'team_data...csv' ve 'player_data...csv' dosyalarının 'tables' klasöründe olduğundan emin ol.")
        db.session.rollback()
    except Exception as e:
        print(f"\n--- BİR HATA OLDU ---: {e}")
        print("Lütfen hatayı kontrol et.")
        db.session.rollback()

print("İşlem tamamlandı.")