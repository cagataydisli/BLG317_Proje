-- schema.sql (PostgreSQL Uyumlu)

-- Eğer tablolar varsa önce temizle (Bağımlılık sırasına göre)
DROP TABLE IF EXISTS technic_roster CASCADE;
DROP TABLE IF EXISTS Matches CASCADE;
DROP TABLE IF EXISTS Teams CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

-- =========================
-- 0) Users Table (Authentication)
-- =========================
CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL
);

-- =========================
-- 1) Teams Table (Referans Tablosu)
-- =========================

CREATE TABLE Teams (
    team_id INT PRIMARY KEY,
    staff_id INT,               -- İlişki sütunu (CSV'de yok)
    team_url VARCHAR(255),      -- Yeni
    team_name VARCHAR(100),
    league VARCHAR(64),         -- Yeni
    team_city VARCHAR(64),
    team_year INT,
    saloon_name VARCHAR(128),
    saloon_capacity INT,        -- ARTIK INT (Sayı)
    saloon_address TEXT         -- Yeni
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
ALTER TABLE Teams
ADD CONSTRAINT fk_teams_staff
FOREIGN KEY (staff_id) REFERENCES technic_roster(staff_id)
ON DELETE SET NULL;

-- =========================
-- PERFORMANCE INDEXES
-- =========================

-- Matches table indexes for faster queries
CREATE INDEX idx_matches_home_team ON Matches(home_team_id);
CREATE INDEX idx_matches_away_team ON Matches(away_team_id);
CREATE INDEX idx_matches_league ON Matches(league);
CREATE INDEX idx_matches_date ON Matches(match_date);
CREATE INDEX idx_matches_city ON Matches(match_city);
CREATE INDEX idx_matches_week ON Matches(match_week);

-- Composite index for deduplication queries (critical for performance)
CREATE INDEX idx_matches_dedup ON Matches(match_date, home_team_id, away_team_id);

-- Index for score-based queries
CREATE INDEX idx_matches_scores ON Matches(home_score, away_score) WHERE home_score IS NOT NULL;

-- Teams table index
CREATE INDEX idx_teams_name ON Teams(team_name);
CREATE INDEX idx_teams_league ON Teams(league);

-- Technic roster index
CREATE INDEX idx_technic_team ON technic_roster(team_id);