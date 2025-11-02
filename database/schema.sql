-- schema.sql (MySQL 8.0+) — Single file schema for all tables

-- Create database
CREATE DATABASE IF NOT EXISTS `bsl_database` 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `bsl_database`;

-- Charset & SQL mode
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET sql_mode = 'STRICT_ALL_TABLES,ONLY_FULL_GROUP_BY';

START TRANSACTION;

-- =========================
-- 1) Core reference tables
-- =========================

-- TODO: Teams schema (owned by <owner>)
-- Example:
-- CREATE TABLE IF NOT EXISTS `Teams` (
--   `team_id` INT PRIMARY KEY,
--   `team_name` VARCHAR(100) NOT NULL,
--   -- other columns...
--   UNIQUE KEY `uk_teams_name`(`team_name`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- TODO: Players schema
-- TODO: PlayerStatistics schema
-- TODO: TechnicRoster schema
-- TODO: Leaderboard schema
-- ... (ek tablolar)

-- =========================
-- 2) Matches table (Celil Aslan)
-- =========================
CREATE TABLE IF NOT EXISTS `Matches` (
  `match_id`     VARCHAR(16)  NOT NULL,
  `home_team_id` INT          NOT NULL,
  `away_team_id` INT          NOT NULL,
  `match_date`   DATE         NULL,
  `match_hour`   TIME         NULL,
  `home_score`   TINYINT UNSIGNED NULL,
  `away_score`   TINYINT UNSIGNED NULL,
  `league`       VARCHAR(64)  NULL,
  `match_week`   VARCHAR(16)  NULL,
  `match_city`   VARCHAR(64)  NULL,
  `match_saloon` VARCHAR(128) NULL,
  CONSTRAINT `pk_matches` PRIMARY KEY (`match_id`),
  CONSTRAINT `fk_matches_home` FOREIGN KEY (`home_team_id`) REFERENCES `Teams`(`team_id`),
  CONSTRAINT `fk_matches_away` FOREIGN KEY (`away_team_id`) REFERENCES `Teams`(`team_id`),
  CONSTRAINT `chk_distinct_teams` CHECK (`home_team_id` <> `away_team_id`)
) ENGINE=InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Helpful indexes
CREATE INDEX IF NOT EXISTS `idx_matches_date`      ON `Matches`(`match_date`);
CREATE INDEX IF NOT EXISTS `idx_matches_home_team` ON `Matches`(`home_team_id`);
CREATE INDEX IF NOT EXISTS `idx_matches_away_team` ON `Matches`(`away_team_id`);

COMMIT;
