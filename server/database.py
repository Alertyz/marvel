import json
import re
import sqlite3
import threading
from datetime import datetime
from .config import DB_PATH, READING_ORDER_PATH, COMICS_DIR


class ReaderDB:
    """Database for the comic reader: issues + reading progress."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or DB_PATH)
        self._local = threading.local()
        self._write_lock = threading.Lock()
        self._init_schema()
        self._ensure_populated()
        self._ensure_sync_table()

    def _conn(self):
        if not hasattr(self._local, "conn"):
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def _init_schema(self):
        c = self._conn()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS issues (
                order_num    INTEGER PRIMARY KEY,
                title        TEXT NOT NULL,
                issue        INTEGER NOT NULL,
                phase        TEXT,
                event        TEXT,
                year         TEXT,
                slug         TEXT,
                url          TEXT,
                total_pages  INTEGER DEFAULT 0,
                scrape_status TEXT DEFAULT 'pending',
                scraped_at   TEXT,
                bookmark     INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS pages (
                issue_order  INTEGER NOT NULL,
                page_num     INTEGER NOT NULL,
                image_url    TEXT NOT NULL,
                file_path    TEXT,
                downloaded   INTEGER DEFAULT 0,
                file_size    INTEGER DEFAULT 0,
                downloaded_at TEXT,
                PRIMARY KEY (issue_order, page_num),
                FOREIGN KEY (issue_order) REFERENCES issues(order_num)
            );
            CREATE TABLE IF NOT EXISTS reading_progress (
                issue_order  INTEGER PRIMARY KEY,
                current_page INTEGER DEFAULT 1,
                is_read      INTEGER DEFAULT 0,
                last_read_at TEXT,
                FOREIGN KEY (issue_order) REFERENCES issues(order_num)
            );
        """)
        c.commit()

    def _ensure_populated(self):
        c = self._conn()
        count = c.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
        if count == 0:
            self._populate_from_json()

    def _populate_from_json(self):
        if not READING_ORDER_PATH.exists():
            return
        with open(str(READING_ORDER_PATH), "r", encoding="utf-8") as f:
            data = json.load(f)
        c = self._conn()
        with self._write_lock:
            for iss in data["issues"]:
                c.execute("""
                    INSERT OR IGNORE INTO issues
                        (order_num, title, issue, phase, event, year, bookmark)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    iss["order"], iss["title"], iss["issue"],
                    iss.get("phase", ""), iss.get("event", ""),
                    iss.get("year", ""), int(iss.get("bookmark", False)),
                ))
            c.commit()

    # ── Queries ─────────────────────────────────────────────
    def get_library(self, phase=None, series=None, search=None):
        q = """
            SELECT i.order_num, i.title, i.issue, i.phase, i.event, i.year,
                   i.total_pages, i.scrape_status, i.bookmark,
                   COALESCE(rp.current_page, 1) as current_page,
                   COALESCE(rp.is_read, 0) as is_read,
                   rp.last_read_at
            FROM issues i
            LEFT JOIN reading_progress rp ON rp.issue_order = i.order_num
            WHERE 1=1
        """
        params = []
        if phase:
            q += " AND i.phase = ?"
            params.append(phase)
        if series:
            q += " AND i.title = ?"
            params.append(series)
        if search:
            q += " AND (LOWER(i.title) LIKE ? OR LOWER(i.event) LIKE ?)"
            params.extend([f"%{search.lower()}%", f"%{search.lower()}%"])
        q += " ORDER BY i.order_num"
        return [dict(r) for r in self._conn().execute(q, params).fetchall()]

    def get_issue(self, order_num):
        q = """
            SELECT i.order_num, i.title, i.issue, i.phase, i.event, i.year,
                   i.total_pages, i.scrape_status, i.bookmark,
                   COALESCE(rp.current_page, 1) as current_page,
                   COALESCE(rp.is_read, 0) as is_read,
                   rp.last_read_at
            FROM issues i
            LEFT JOIN reading_progress rp ON rp.issue_order = i.order_num
            WHERE i.order_num = ?
        """
        row = self._conn().execute(q, (order_num,)).fetchone()
        return dict(row) if row else None

    def get_eras(self):
        q = """
            SELECT i.phase, COUNT(*) as count,
                   SUM(CASE WHEN rp.is_read = 1 THEN 1 ELSE 0 END) as read_count,
                   SUM(CASE WHEN i.scrape_status = 'done' THEN 1 ELSE 0 END) as downloaded_count
            FROM issues i
            LEFT JOIN reading_progress rp ON rp.issue_order = i.order_num
            GROUP BY i.phase
            ORDER BY MIN(i.order_num)
        """
        return [dict(r) for r in self._conn().execute(q).fetchall()]

    def get_series_list(self):
        q = "SELECT DISTINCT title FROM issues ORDER BY title"
        return [r["title"] for r in self._conn().execute(q).fetchall()]

    def get_issue_page_count(self, order_num):
        """Get number of downloaded pages for an issue."""
        row = self._conn().execute(
            "SELECT COUNT(*) as c FROM pages WHERE issue_order = ? AND downloaded = 1",
            (order_num,),
        ).fetchone()
        return row["c"] if row else 0

    def get_issue_page_path(self, order_num, page_num):
        """Get local file path for a specific page, trying DB first then filesystem."""
        # Try DB
        row = self._conn().execute(
            "SELECT file_path FROM pages WHERE issue_order = ? AND page_num = ? AND downloaded = 1",
            (order_num, page_num),
        ).fetchone()
        if row and row["file_path"]:
            from pathlib import Path
            if Path(row["file_path"]).exists():
                return row["file_path"]

        # Fallback: construct path from issue data
        issue = self.get_issue(order_num)
        if not issue:
            return None
        safe = re.sub(r'[<>:"/\\|?*]', '_', issue["title"])
        issue_dir = COMICS_DIR / safe / f"Issue_{issue['issue']:03d}"
        for ext in (".jpg", ".png", ".webp"):
            fpath = issue_dir / f"page_{page_num:03d}{ext}"
            if fpath.exists():
                return str(fpath)
        return None

    # ── Progress ────────────────────────────────────────────
    def update_progress(self, order_num, current_page=None, is_read=None):
        c = self._conn()
        now = datetime.now().isoformat()
        with self._write_lock:
            existing = c.execute(
                "SELECT * FROM reading_progress WHERE issue_order = ?", (order_num,)
            ).fetchone()
            if existing:
                updates, params = [], []
                if current_page is not None:
                    updates.append("current_page = ?")
                    params.append(current_page)
                if is_read is not None:
                    updates.append("is_read = ?")
                    params.append(int(is_read))
                updates.append("last_read_at = ?")
                params.append(now)
                params.append(order_num)
                c.execute(
                    f"UPDATE reading_progress SET {', '.join(updates)} WHERE issue_order = ?",
                    params,
                )
            else:
                c.execute("""
                    INSERT INTO reading_progress (issue_order, current_page, is_read, last_read_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    order_num,
                    current_page or 1,
                    int(is_read) if is_read is not None else 0,
                    now,
                ))
            self._bump_version()
            c.commit()

    def mark_all_before_as_read(self, order_num):
        c = self._conn()
        now = datetime.now().isoformat()
        with self._write_lock:
            issues = c.execute(
                "SELECT order_num FROM issues WHERE order_num <= ?", (order_num,)
            ).fetchall()
            for iss in issues:
                c.execute("""
                    INSERT INTO reading_progress (issue_order, is_read, last_read_at)
                    VALUES (?, 1, ?)
                    ON CONFLICT(issue_order) DO UPDATE SET is_read = 1, last_read_at = ?
                """, (iss["order_num"], now, now))
            self._bump_version()
            c.commit()
            return len(issues)

    def toggle_read(self, order_num):
        c = self._conn()
        now = datetime.now().isoformat()
        with self._write_lock:
            existing = c.execute(
                "SELECT is_read FROM reading_progress WHERE issue_order = ?", (order_num,)
            ).fetchone()
            new_val = 0 if (existing and existing["is_read"]) else 1
            c.execute("""
                INSERT INTO reading_progress (issue_order, is_read, last_read_at)
                VALUES (?, ?, ?)
                ON CONFLICT(issue_order) DO UPDATE SET is_read = ?, last_read_at = ?
            """, (order_num, new_val, now, new_val, now))
            self._bump_version()
            c.commit()
            return bool(new_val)

    def get_bookmark(self):
        q = """
            SELECT i.order_num, i.title, i.issue, i.phase
            FROM issues i
            LEFT JOIN reading_progress rp ON rp.issue_order = i.order_num
            WHERE COALESCE(rp.is_read, 0) = 0
            ORDER BY i.order_num
            LIMIT 1
        """
        row = self._conn().execute(q).fetchone()
        return dict(row) if row else None

    def get_stats(self):
        c = self._conn()
        total = c.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
        read_count = c.execute(
            "SELECT COUNT(*) FROM reading_progress WHERE is_read = 1"
        ).fetchone()[0]
        downloaded = c.execute(
            "SELECT COUNT(DISTINCT i.order_num) FROM issues i "
            "JOIN pages p ON p.issue_order = i.order_num "
            "WHERE p.downloaded = 1"
        ).fetchone()[0]
        return {
            "total_issues": total,
            "read_issues": read_count,
            "unread_issues": total - read_count,
            "downloaded_issues": downloaded,
            "progress_percent": round(read_count / total * 100, 1) if total > 0 else 0,
        }

    # ── Sync ────────────────────────────────────────────────
    def _ensure_sync_table(self):
        c = self._conn()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS sync_meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        c.commit()
        row = c.execute("SELECT value FROM sync_meta WHERE key = 'version'").fetchone()
        if not row:
            with self._write_lock:
                c.execute(
                    "INSERT OR IGNORE INTO sync_meta (key, value) VALUES ('version', ?)",
                    (datetime.now().isoformat(),),
                )
                c.commit()

    def _bump_version(self):
        c = self._conn()
        now = datetime.now().isoformat()
        c.execute("UPDATE sync_meta SET value = ? WHERE key = 'version'", (now,))
        c.commit()
        return now

    def get_sync_version(self):
        row = self._conn().execute(
            "SELECT value FROM sync_meta WHERE key = 'version'"
        ).fetchone()
        return row["value"] if row else datetime.now().isoformat()

    def get_sync_state(self):
        """Return full sync state: version + all reading progress."""
        c = self._conn()
        version = self.get_sync_version()
        progress = [
            dict(r)
            for r in c.execute(
                "SELECT issue_order, current_page, is_read, last_read_at FROM reading_progress"
            ).fetchall()
        ]
        image_counts = [
            dict(r)
            for r in c.execute(
                "SELECT issue_order, COUNT(*) as page_count "
                "FROM pages WHERE downloaded = 1 GROUP BY issue_order"
            ).fetchall()
        ]
        return {
            "version": version,
            "progress": progress,
            "image_counts": image_counts,
        }

    def apply_sync_state(self, progress_list):
        """Overwrite all reading progress from a client push. Returns new version."""
        c = self._conn()
        with self._write_lock:
            for p in progress_list:
                c.execute("""
                    INSERT INTO reading_progress (issue_order, current_page, is_read, last_read_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(issue_order) DO UPDATE SET
                        current_page = excluded.current_page,
                        is_read = excluded.is_read,
                        last_read_at = excluded.last_read_at
                """, (
                    p["issue_order"],
                    p.get("current_page", 1),
                    int(p.get("is_read", 0)),
                    p.get("last_read_at", datetime.now().isoformat()),
                ))
            new_version = self._bump_version()
            c.commit()
        return new_version
