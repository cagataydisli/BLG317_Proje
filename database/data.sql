-- data.sql (MySQL) — Single file CSV loads for all tables
-- NOTE: Use absolute paths for CSVs accessible to the MySQL client (LOCAL INFILE).
-- Enable if needed:
--   -- server: SET GLOBAL local_infile = 1;
--   -- client: mysql --local-infile=1 -u user -p dbname

-- =========================
-- 0) Common settings
-- =========================
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Disable FK for bulk load (remember to re-enable)
SET FOREIGN_KEY_CHECKS = 0;

-- =========================
-- 1) Load core reference tables (must come BEFORE Matches)
-- =========================

-- TODO: Teams data
-- SET @teams_csv = '/absolute/path/to/teams.csv';
-- LOAD DATA LOCAL INFILE @teams_csv
-- INTO TABLE `Teams`
-- CHARACTER SET utf8mb4
-- FIELDS TERMINATED BY ',' ENCLOSED BY '\"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 LINES
-- (`team_id`, `team_name` /*, ... other columns ...*/);

-- TODO: Players, PlayerStatistics, TechnicRoster, Leaderboard, ...

-- =========================
-- 2) Load matches data (Celil Aslan)
-- =========================
SET @matches_csv = '/path/to/BLG317_Proje/tables/matches.csv';

LOAD DATA LOCAL INFILE @matches_csv
INTO TABLE `Matches`
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(`match_id`, `home_team_id`, `away_team_id`, `match_date`, `match_hour`, `home_score`, `away_score`, `league`, `match_week`, `match_city`, `match_saloon`);

-- =========================
-- 3) Post-load checks
-- =========================
SET FOREIGN_KEY_CHECKS = 1;

-- Quick sanity checks (optional):
-- SELECT COUNT(*) AS matches_rows FROM `Matches`;
-- SELECT * FROM `Matches` ORDER BY `match_date`, `match_hour` LIMIT 20;
