"""Restore comics.db from exported CSVs."""
import csv
import os
import shutil
import sqlite3
from pathlib import Path

DB = "comics.db"
BACKUP = "comics.db.broken_backup"
CSV_DIR = Path("data")

if os.path.exists(DB):
    shutil.copy2(DB, BACKUP)
    print(f"Backup do banco danificado: {BACKUP}")
os.remove(DB) if os.path.exists(DB) else None

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")

conn.execute(
    "CREATE TABLE issues ("
    "order_num INTEGER PRIMARY KEY, title TEXT NOT NULL, issue INTEGER NOT NULL,"
    "phase TEXT, event TEXT, year TEXT, slug TEXT, url TEXT,"
    "total_pages INTEGER DEFAULT 0, scrape_status TEXT DEFAULT 'pending',"
    "scraped_at TEXT, bookmark INTEGER DEFAULT 0)"
)
conn.execute(
    "CREATE TABLE pages ("
    "issue_order INTEGER NOT NULL, page_num INTEGER NOT NULL, image_url TEXT NOT NULL,"
    "file_path TEXT, downloaded INTEGER DEFAULT 0, file_size INTEGER DEFAULT 0,"
    "downloaded_at TEXT, PRIMARY KEY (issue_order, page_num),"
    "FOREIGN KEY (issue_order) REFERENCES issues(order_num))"
)
conn.execute(
    "CREATE TABLE validation_flags ("
    "issue_order INTEGER NOT NULL, flag_type TEXT NOT NULL,"
    "message TEXT, created_at TEXT NOT NULL, resolved INTEGER DEFAULT 0,"
    "PRIMARY KEY (issue_order, flag_type))"
)
conn.execute(
    "CREATE TABLE reading_progress ("
    "issue_order INTEGER PRIMARY KEY, current_page INTEGER DEFAULT 1,"
    "is_read INTEGER DEFAULT 0, last_read_at TEXT,"
    "FOREIGN KEY (issue_order) REFERENCES issues(order_num))"
)
conn.execute(
    "CREATE TABLE reports ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, issue_order INTEGER NOT NULL,"
    "page_num INTEGER, report_type TEXT NOT NULL, description TEXT,"
    "created_at TEXT NOT NULL, resolved INTEGER DEFAULT 0, resolved_at TEXT,"
    "FOREIGN KEY (issue_order) REFERENCES issues(order_num))"
)
conn.execute("CREATE TABLE sync_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
conn.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
conn.execute(
    "CREATE INDEX idx_pages_pending ON pages(downloaded) WHERE downloaded = 0"
)
conn.execute("CREATE INDEX idx_issues_scrape ON issues(scrape_status)")
conn.commit()


def load_csv(filename):
    path = CSV_DIR / filename
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def n(v):
    return None if v == "" else v


# Issues
rows = load_csv("issues.csv")
conn.executemany(
    "INSERT INTO issues VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
    [
        (
            int(r["order_num"]), r["title"], int(r["issue"]),
            n(r["phase"]), n(r["event"]), n(r["year"]),
            n(r["slug"]), n(r["url"]), int(r["total_pages"]),
            r["scrape_status"], n(r["scraped_at"]), int(r["bookmark"]),
        )
        for r in rows
    ],
)
print(f"Issues restauradas:   {len(rows)}")

# Pages (large — 30k+ rows)
rows = load_csv("pages.csv")
conn.executemany(
    "INSERT INTO pages VALUES (?,?,?,?,?,?,?)",
    [
        (
            int(r["issue_order"]), int(r["page_num"]), r["image_url"],
            n(r["file_path"]), int(r["downloaded"]),
            int(r["file_size"]), n(r["downloaded_at"]),
        )
        for r in rows
    ],
)
print(f"Paginas restauradas:  {len(rows)}")

# Reading progress
rows = load_csv("reading_progress.csv")
conn.executemany(
    "INSERT INTO reading_progress VALUES (?,?,?,?)",
    [
        (int(r["issue_order"]), int(r["current_page"]),
         int(r["is_read"]), n(r["last_read_at"]))
        for r in rows
    ],
)
print(f"Progresso restaurado: {len(rows)} issues")

# Sync meta + settings
for fname, table in [("sync_meta.csv", "sync_meta"), ("settings.csv", "settings")]:
    rows = load_csv(fname)
    if rows:
        conn.executemany(
            f"INSERT INTO {table} VALUES (?,?)",
            [(r["key"], r["value"]) for r in rows],
        )

conn.commit()
conn.close()
print("Banco restaurado com sucesso!")
