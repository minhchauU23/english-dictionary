#!/usr/bin/env python3
"""
ETL: kaikki.org JSONL.gz → MySQL (local)
DEV chạy 1 lần: python etl/init.py
Sau đó dump: mysqldump -u dict_user -pdict_pass dictionary | gzip > data/seed.sql.gz
"""

import gzip
import json
import os
import sys
import time
import mysql.connector
import requests

# ── Config ────────────────────────────────────────────
JSONL_PATH = os.getenv("JSONL_PATH", "data/raw-wiktextract-data.jsonl.gz")
DB_CONFIG  = {
    "host":     os.getenv("MYSQL_HOST",     "mysql"),
    "port":     int(os.getenv("MYSQL_PORT", "3306")),
    "user":     os.getenv("MYSQL_USER",     "user"),
    "password": os.getenv("MYSQL_PASSWORD", "pass"),
    "database": os.getenv("MYSQL_DATABASE", "dictionary"),
    "charset":  "utf8mb4",
}
DATA_URL = os.getenv(
    "DATA_URL",
    "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz"
)
BATCH_SIZE = 500  # số rows insert mỗi lần executemany

def ensure_dataset(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        log(f"Dataset already exists: {path}")
        return

    log(f"Downloading dataset from {DATA_URL} ...")

    response = requests.get(DATA_URL, stream=True)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    downloaded = 0
    chunk_size = 1024 * 1024  # 1MB

    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)

                if total > 0:
                    percent = downloaded * 100 / total

                    # chỉ log mỗi 1%
                    if int(percent) % 2 == 0:
                        log(f"Downloading... {percent:.1f}% ({downloaded/1e6:.0f} MB)")

    log("Download completed.")

# ── Helpers ───────────────────────────────────────────
def log(msg):
    print(f"[ETL] {msg}", flush=True)

def connect_with_retry(config, retries=10, delay=5):
    for i in range(retries):
        try:
            conn = mysql.connector.connect(**config)
            log("Connected to MySQL.")
            return conn
        except mysql.connector.Error as e:
            log(f"MySQL not ready ({e}), retry {i+1}/{retries}...")
            time.sleep(delay)
    log("Cannot connect to MySQL. Exiting.")
    sys.exit(1)

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# ── Parse helpers ─────────────────────────────────────
def parse_pronunciation(entry_id, sounds):
    """
    sounds is list sound, for each item have ipa, audio, mp3_url, tags.
    Gom ipa + audio của cùng region vào 1 row.
    """
    rows = []
    # group by region
    region_map = {}  # region -> {ipa, audio_url}
    for s in sounds:
        tags   = s.get("tags", [])
        region = next((t for t in tags if t in ("US", "UK", "General-American", "Australia")), "General")
        ipa    = s.get("ipa")
        audio  = s.get("mp3_url") or s.get("ogg_url")
        if region not in region_map:
            region_map[region] = {"ipa": None, "audio_url": None}
        if ipa:
            region_map[region]["ipa"] = ipa
        if audio:
            region_map[region]["audio_url"] = audio

    for region, data in region_map.items():
        if data["ipa"] or data["audio_url"]:
            rows.append((entry_id, data["ipa"], region, data["audio_url"]))
    return rows

def is_already_seeded(cursor):
    cursor.execute("SELECT COUNT(*) FROM word")
    count = cursor.fetchone()[0]
    return count > 0

# ── Main ETL ──────────────────────────────────────────
def main():
    ensure_dataset(JSONL_PATH)
    if not os.path.exists(JSONL_PATH):
        log(f"File not found: {JSONL_PATH}")
        log("Đặt file JSONL.gz vào data/ rồi chạy lại.")
        sys.exit(1)

    conn   = connect_with_retry(DB_CONFIG)
    cursor = conn.cursor()

    if is_already_seeded(cursor):
        log("DB already seeded → EXIT ETL")
        cursor.close()
        conn.close()
        sys.exit(0)

    # Tắt FK checks và autocommit để insert nhanh hơn
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("SET unique_checks = 0")
    conn.autocommit = False

    # ── SEED ADMIN + ROLE ───────────────────────────────
    def seed_admin_and_roles():
        log("Seeding admin + roles ...")

        # role
        cursor.execute("INSERT IGNORE INTO role (id, name) VALUES ('ADMIN', 'ADMIN'), ('USER', 'USER')")

        # admin user (id = 1 cố định cho đơn giản)
        cursor.execute("INSERT IGNORE INTO user (id, email, password_hash, first_name, last_name) VALUES (1, 'admin@system.local', 'N/A', 'Admin', 'System')")

        # assign role admin
        cursor.execute("INSERT IGNORE INTO user_role (user_id, role_id) VALUES (1, 'ADMIN')")

        conn.commit()
        log("Admin + roles seeded.")

    seed_admin_and_roles()
    # ── PASS 1: word, entry, pronunciation, sense, example, word_form ──
    log("=== PASS 1: word / entry / pronunciation / sense / example / word_form ===")

    word_spelling_to_id = {}   # cache spelling → id
    total_entries = 0

    buf_word         = []
    buf_entry        = []
    buf_pronunciation= []
    buf_sense        = []
    buf_example      = []
    buf_word_form    = []

    # ID counters (auto_increment ở DB nhưng mình tự quản để build FK)
    user_id   = 1
    word_id   = 1
    entry_id  = 1
    pron_id   = 1
    sense_id  = 1
    example_id= 1
    form_id   = 1

    def flush_pass1():
        if buf_word:
            cursor.executemany(
                "INSERT IGNORE INTO word (id, created_by, updated_by, spelling) VALUES (%s, %s, %s, %s)", buf_word)
        if buf_entry:
            cursor.executemany(
                "INSERT IGNORE INTO entry (id, word_id, pos, entry_order, created_by, updated_by) VALUES (%s,%s,%s,%s,%s, %s)", buf_entry)
        if buf_pronunciation:
            cursor.executemany(
                "INSERT INTO pronunciation (id, created_by, updated_by, entry_id, ipa, region, audio_url) VALUES (%s,%s,%s,%s,%s,%s,%s)", buf_pronunciation)
        if buf_sense:
            cursor.executemany(
                "INSERT INTO sense (id, created_by, updated_by, entry_id, definition, sense_order) VALUES (%s,%s,%s,%s,%s,%s)", buf_sense)
        if buf_example:
            cursor.executemany(
                "INSERT INTO example (id, created_by, updated_by, sense_id, text) VALUES (%s,%s,%s,%s,%s)", buf_example)
        if buf_word_form:
            cursor.executemany(
                "INSERT INTO word_form (id, created_by, updated_by, entry_id, form, tags) VALUES (%s,%s,%s,%s,%s,%s)", buf_word_form)
        conn.commit()
        buf_word.clear(); buf_entry.clear(); buf_pronunciation.clear()
        buf_sense.clear(); buf_example.clear(); buf_word_form.clear()

    with gzip.open(JSONL_PATH, "rt", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Chỉ lấy tiếng Anh
            if obj.get("lang_code") != "en":
                continue

            spelling = obj.get("word", "").strip().lower()
            pos      = obj.get("pos", "").strip()
            if not spelling or not pos:
                continue

            # ── word ──
            if spelling not in word_spelling_to_id:
                word_spelling_to_id[spelling] = word_id
                buf_word.append((word_id, user_id, user_id, spelling))
                word_id += 1

            current_word_id = word_spelling_to_id[spelling]

            # entry_order: đếm số entry cùng word+pos đã có
            entry_order = sum(
                1 for e in buf_entry
                if e[1] == current_word_id and e[2] == pos
            ) + 1

            # ── entry ──
            current_entry_id = entry_id
            buf_entry.append((entry_id, current_word_id, pos, entry_order, user_id, user_id))
            entry_id += 1

            # ── pronunciation ──
            for row in parse_pronunciation(current_entry_id, obj.get("sounds", [])):
                buf_pronunciation.append((pron_id, user_id, user_id) + row)
                pron_id += 1

            # ── sense ──
            for s_order, sense in enumerate(obj.get("senses", []), 1):
                glosses = sense.get("glosses", [])
                definition = glosses[0].strip() if glosses else None
                if not definition:
                    continue

                current_sense_id = sense_id
                buf_sense.append((sense_id, user_id, user_id, current_entry_id, definition, s_order))
                sense_id += 1

                # examples
                for ex in sense.get("examples", []):
                    text = ex.get("text", "").strip()
                    if text:
                        buf_example.append((example_id, user_id, user_id, current_sense_id, text))
                        example_id += 1

            # ── word_form ──
            for form_obj in obj.get("forms", []):
                form = form_obj.get("form", "").strip()
                tags = ",".join(form_obj.get("tags", []))
                if form:
                    buf_word_form.append((form_id, user_id, user_id, current_entry_id, form, tags or None))
                    form_id += 1

            total_entries += 1

            # Flush mỗi BATCH_SIZE entries
            if total_entries % BATCH_SIZE == 0:
                flush_pass1()
                if total_entries % 10000 == 0:
                    log(f"  Pass 1: {total_entries:,} entries processed, {len(word_spelling_to_id):,} words")

    flush_pass1()
    log(f"Pass 1 done. {total_entries:,} entries, {len(word_spelling_to_id):,} words.")

    # ── PASS 2: sense_relation (synonym / antonym) ──
    log("=== PASS 2: sense_relation (synonym / antonym) ===")

    # Reload word map từ DB (chắc chắn đầy đủ hơn cache)
    cursor.execute("SELECT id, spelling FROM word")
    db_word_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Reload sense map: (entry_id, sense_order) → sense_id
    cursor.execute("SELECT id, entry_id, sense_order FROM sense")
    sense_map = {(row[1], row[2]): row[0] for row in cursor.fetchall()}

    # Reload entry map: (word_id, pos, entry_order) → entry_id
    cursor.execute("SELECT id, word_id, pos, entry_order FROM entry")
    entry_map = {(row[1], row[2], row[3]): row[0] for row in cursor.fetchall()}

    relation_id  = 1
    buf_relation = []
    skipped      = 0

    def flush_relations():
        if buf_relation:
            cursor.executemany(
                """INSERT IGNORE INTO sense_relation
                   (id, sense_id, related_word_id, relation_type, created_by, updated_by)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                buf_relation
            )
            conn.commit()
            buf_relation.clear()

    entry_order_tracker = {}  # word_id+pos → count

    with gzip.open(JSONL_PATH, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("lang_code") != "en":
                continue

            spelling = obj.get("word", "").strip().lower()
            pos      = obj.get("pos", "").strip()
            if not spelling or not pos:
                continue

            current_word_id = db_word_map.get(spelling)
            if not current_word_id:
                continue

            key = (current_word_id, pos)
            entry_order_tracker[key] = entry_order_tracker.get(key, 0) + 1
            current_entry_id = entry_map.get((current_word_id, pos, entry_order_tracker[key]))
            if not current_entry_id:
                continue

            for s_order, sense in enumerate(obj.get("senses", []), 1):
                current_sense_id = sense_map.get((current_entry_id, s_order))
                if not current_sense_id:
                    continue

                for rel_type, key_name in [("SYNONYM", "synonyms"), ("ANTONYM", "antonyms")]:
                    for item in sense.get(key_name, []):
                        related_spelling = item.get("word", "").strip().lower()
                        related_word_id  = db_word_map.get(related_spelling)
                        if not related_word_id:
                            skipped += 1
                            continue
                        buf_relation.append((relation_id, current_sense_id, related_word_id, rel_type, user_id, user_id))
                        relation_id += 1

            if len(buf_relation) >= BATCH_SIZE:
                flush_relations()

    flush_relations()
    log(f"Pass 2 done. {relation_id - 1:,} relations inserted, {skipped:,} skipped (word not found).")

    # Re-enable constraints
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    cursor.execute("SET unique_checks = 1")
    conn.commit()
    cursor.close()
    conn.close()

    log("=== ETL hoàn tất ===")
   
    log("Chạy lệnh sau để export dump:")
    log("  mysqldump -u dict_user -pdict_pass dictionary | gzip > data/seed.sql.gz")
    sys.exit(0)

if __name__ == "__main__":
    main()
