-- schema.sql (PostgreSQL Uyumlu)

-- Eğer tablolar varsa önce temizle (Bağımlılık sırasına göre)
DROP TABLE IF EXISTS technic_roster CASCADE;
DROP TABLE IF EXISTS Matches CASCADE;
DROP TABLE IF EXISTS Teams CASCADE;

-- =========================
-- 1) Teams Table (Referans Tablosu)
-- =========================
CREATE TABLE Teams (
    team_id INT PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    city VARCHAR(100),
    UNIQUE (team_name)
);

-- =========================
-- 2) Matches Table (Maçlar)
-- =========================
CREATE TABLE Matches (
    match_id VARCHAR(16) NOT NULL PRIMARY KEY,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    match_date DATE NULL,
    match_hour TIME NULL,
    home_score SMALLINT NULL,
    away_score SMALLINT NULL,
    league VARCHAR(64) NULL,
    match_week VARCHAR(16) NULL,
    match_city VARCHAR(64) NULL,
    match_saloon VARCHAR(128) NULL,
    CONSTRAINT fk_matches_home FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
    CONSTRAINT fk_matches_away FOREIGN KEY (away_team_id) REFERENCES Teams(team_id),
    CONSTRAINT chk_distinct_teams CHECK (home_team_id <> away_team_id)
);

-- =========================
-- 3) Technic Roster Table (Technical Staff)
-- =========================
CREATE TABLE technic_roster (
    staff_id SERIAL PRIMARY KEY,
    team_id INT NOT NULL REFERENCES Teams(team_id),
    team_url TEXT,
    league VARCHAR(64),
    technic_member_name VARCHAR(100) NOT NULL,
    technic_member_role VARCHAR(100)
);
