# BLG 317E - Veritabanı Sistemleri Projesi
## Turkish Basketball Super League (BSL) Yönetim Sistemi

Bu proje, BLG 317E dersi kapsamında Python Flask ve bir SQL veritabanı kullanılarak geliştirilen bir web tabanlı veritabanı yönetim sistemidir.

**Dataset:** [Turkish Basketball Super League Dataset](https://www.kaggle.com/datasets/onurulu/turkish-basketball-super-league-dataset/data)

---

## Grup Üyeleri ve Sorumluluklar

| Üye | Student No | Sorumlu Olduğu Ana Tablo |
| :--- | :--- | :--- |
| Çağatay Dişli | 040210081 | `Players` |
| Talip Demir | 040210514 | `Teams` |
| Celil Aslan | 150210703 | `Matches` |
| Musa Can Turgut | 150210918 | `Technical_Staff` |
| Emir Şahin | 150220072 | `Standings` |

---

## Düzeltilmiş Veritabanı Şeması

Proje önerisindeki mantıksal düzeltmeler yapılarak aşağıdaki 5 ana tablo şeması belirlenmiştir:

1.  **`Teams`** (Sorumlu: Talip)
    * **PK:** `team_id`
    * **Non-Key:** `team_name`, `team_city`, `team_year`

2.  **`Players`** (Sorumlu: Çağatay)
    * **PK:** `player_id`
    * **FK:** `team_id` (References `Teams.team_id`)
    * **Non-Key:** `player_name`, `player_birthdate`, `player_height`

3.  **`Matches`** (Sorumlu: Celil)
    * **PK:** `match_id`
    * **FK:** `home_team_id` (References `Teams.team_id`)
    * **FK:** `away_team_id` (References `Teams.team_id`)
    * **Non-Key:** `match_date`, `match_hour`, `match_score`

4.  **`Technical_Staff`** (Sorumlu: Musa Can)
    * **PK:** `staff_id`
    * **FK:** `team_id` (References `Teams.team_id`)
    * **Non-Key:** `nationality`, `technic_member_name`, `technic_member_role`

5.  **`Standings`** (Sorumlu: Emir)
    * **PK:** (`team_id`, `league`) (Composite Key)
    * **FK:** `team_id` (References `Teams.team_id`)
    * **Non-Key:** `team_matches_played`, `team_wins`, `team_loses`, `rank`

---

## Hafta 1: Görev Listesi (İlk Commit Hedefleri)

Haftalık commit zorunluluğunu karşılamak için her üyenin tamamlaması gereken ilk görevler:

1.  **Genel Görev (Bir kişi, örn: Çağatay):**
    * [ ] GitHub deposunu oluşturmak.
    * [ ] Tüm üyeleri depoya "Collaborator" olarak eklemek.
    * [ ] Bu `README.md` dosyasını, `app.py`, `.gitignore` ve `requirements.txt` dosyalarının ilk hallerini depoya yüklemek (`git push`).

2.  **Çağatay Dişli (`Players`):**
    * [ ] `app.py` içine `/players` route'unu (yukarıdaki taslaktaki gibi) eklemek.
    * [ ] `templates/players.html` adında, "Oyuncular Sayfası" başlığı içeren basit bir HTML dosyası oluşturmak.
    * [ ] Yaptığı değişiklikleri GitHub'a push etmek.

3.  **Talip Demir (`Teams`):**
    * [ ] `app.py` içine `/teams` route'unu (yukarıdaki taslaktaki gibi) eklemek.
    * [ ] `templates/teams.html` adında, "Takımlar Sayfası" başlığı içeren basit bir HTML dosyası oluşturmak.
    * [ ] Yaptığı değişiklikleri GitHub'a push etmek.

4.  **Celil Aslan (`Matches`):**
    * [ ] `app.py` içine `/matches` route'unu (yukarıdaki taslaktaki gibi) eklemek.
    * [ ] `templates/matches.html` adında, "Maçlar Sayfası" başlığı içeren basit bir HTML dosyası oluşturmak.
    * [ ] Yaptığı değişiklikleri GitHub'a push etmek.

5.  **Musa Can Turgut (`Technical_Staff`):**
    * [ ] `app.py` içine `/staff` route'unu (yukarıdaki taslaktaki gibi) eklemek.
    * [ ] `templates/staff.html` adında, "Teknik Ekip Sayfası" başlığı içeren basit bir HTML dosyası oluşturmak.
    * [ ] Yaptığı değişiklikleri GitHub'a push etmek.

6.  **Emir Şahin (`Standings`):**
    * [ ] `app.py` içine `/standings` route'unu (yukarıdaki taslaktaki gibi) eklemek.
    * [ ] `templates/standings.html` adında, "Puan Durumu Sayfası" başlığı içeren basit bir HTML dosyası oluşturmak.
    * [ ] Yaptığı değişiklikleri GitHub'a push etmek.

*(Not: `app.py` dosyasını birden fazla kişi düzenleyeceği için `git pull` yapmayı unutmayın!)*