CREATE DATABASE IF NOT EXISTS dictionary 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE dictionary;

-- ─── CORE ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS word (
  id             BIGINT NOT NULL AUTO_INCREMENT,
  spelling       VARCHAR(200) NOT NULL,
  frequency_rank INT NULL,
  created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_word_spelling (spelling)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS entry (
  id          BIGINT NOT NULL AUTO_INCREMENT,
  word_id     BIGINT NOT NULL,
  pos         VARCHAR(50) NOT NULL,
  entry_order INT NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_entry (word_id, pos, entry_order),
  CONSTRAINT fk_entry_word FOREIGN KEY (word_id) REFERENCES word(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS pronunciation (
  id        BIGINT NOT NULL AUTO_INCREMENT,
  entry_id  BIGINT NOT NULL,
  ipa       VARCHAR(200) NULL,
  region    VARCHAR(50) NULL,
  audio_url VARCHAR(500) NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_pronunciation_entry FOREIGN KEY (entry_id) REFERENCES entry(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS sense (
  id          BIGINT NOT NULL AUTO_INCREMENT,
  entry_id    BIGINT NOT NULL,
  definition  TEXT NOT NULL,
  sense_order INT NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  CONSTRAINT fk_sense_entry FOREIGN KEY (entry_id) REFERENCES entry(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS example (
  id       BIGINT NOT NULL AUTO_INCREMENT,
  sense_id BIGINT NOT NULL,
  text     TEXT NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_example_sense FOREIGN KEY (sense_id) REFERENCES sense(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS sense_relation (
  id              BIGINT NOT NULL AUTO_INCREMENT,
  sense_id        BIGINT NOT NULL,
  related_word_id BIGINT NOT NULL,
  relation_type   VARCHAR(20) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_sense_relation (sense_id, related_word_id, relation_type),
  KEY idx_relation_sense (sense_id),
  KEY idx_relation_word (related_word_id),
  CONSTRAINT fk_relation_sense FOREIGN KEY (sense_id) REFERENCES sense(id),
  CONSTRAINT fk_relation_word FOREIGN KEY (related_word_id) REFERENCES word(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ─── FIXED ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS word_form (
  id       BIGINT NOT NULL AUTO_INCREMENT,
  entry_id BIGINT NOT NULL,
  form     TEXT NOT NULL,
  tags     TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_word_form_entry (entry_id),
  CONSTRAINT fk_word_form_entry FOREIGN KEY (entry_id) REFERENCES entry(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ─── USER / OTHER (UNCHANGED) ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS user (
  id BIGINT NOT NULL AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(100),
  preferred_lang VARCHAR(5),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;