import json
import re
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from .config import DB_PATH, READING_ORDER_PATH, COMICS_DIR


class ReaderDB:
    """Database for the comic reader: issues, reading progress, reports, sync."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or DB_PATH)
        self._local = threading.local()
        self._write_lock = threading.Lock()
        self._init_schema()
        self.sync_with_json()

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
                total_pages  INTEGER DEFAULT 0,
                bookmark     INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS reading_progress (
                issue_order  INTEGER PRIMARY KEY,
                current_page INTEGER DEFAULT 1,
                is_read      INTEGER DEFAULT 0,
                last_read_at TEXT,
                FOREIGN KEY (issue_order) REFERENCES issues(order_num)
            );
            CREATE TABLE IF NOT EXISTS reports (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_order  INTEGER NOT NULL,
                page_num     INTEGER,
                report_type  TEXT NOT NULL,
                description  TEXT,
                created_at   TEXT NOT NULL,
                resolved     INTEGER DEFAULT 0,
                resolved_at  TEXT,
                FOREIGN KEY (issue_order) REFERENCES issues(order_num)
            );
            CREATE TABLE IF NOT EXISTS sync_meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        c.commit()
        # Ensure sync version exists
        row = c.execute("SELECT value FROM sync_meta WHERE key = 'version'").fetchone()
        if not row:
            with self._write_lock:
                c.execute(
                    "INSERT OR IGNORE INTO sync_meta (key, value) VALUES ('version', ?)",
                    (datetime.now().isoformat(),),
                )
                c.commit()

    def sync_with_json(self):
        if not READING_ORDER_PATH.exists():
            return
        with open(str(READING_ORDER_PATH), "r", encoding="utf-8") as f:
            data = json.load(f)
        
        valid_orders = []
        c = self._conn()
        with self._write_lock:
            for iss in data["issues"]:
                valid_orders.append(iss["order"])
                c.execute("""
                    INSERT INTO issues
                        (order_num, title, issue, phase, event, year, bookmark)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(order_num) DO UPDATE SET
                        title=excluded.title, issue=excluded.issue,
                        phase=excluded.phase, event=excluded.event,
                        year=excluded.year, bookmark=excluded.bookmark
                """, (
                    iss["order"], iss["title"], iss["issue"],
                    iss.get("phase", ""), iss.get("event", ""),
                    iss.get("year", ""), int(iss.get("bookmark", False)),
                ))
            
            if valid_orders:
                existing_orders = [r[0] for r in c.execute("SELECT order_num FROM issues").fetchall()]
                to_delete = set(existing_orders) - set(valid_orders)
                for chunk in [list(to_delete)[i:i+500] for i in range(0, len(to_delete), 500)]:
                    if not chunk: continue
                    placeholders = ",".join("?" for _ in chunk)
                    c.execute(f"DELETE FROM reading_progress WHERE issue_order IN ({placeholders})", chunk)
                    c.execute(f"DELETE FROM reports WHERE issue_order IN ({placeholders})", chunk)
                    c.execute(f"DELETE FROM issues WHERE order_num IN ({placeholders})", chunk)
                    
            c.commit()

    def _bump_version(self):
        now = datetime.now().isoformat()
        self._conn().execute("UPDATE sync_meta SET value = ? WHERE key = 'version'", (now,))
        return now

    # ── Library queries ─────────────────────────────────────
    def get_library(self, phase=None, series=None, search=None):
        q = """
            SELECT i.order_num, i.title, i.issue, i.phase, i.event, i.year,
                   i.total_pages, i.bookmark,
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
                   i.total_pages, i.bookmark,
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
                   SUM(CASE WHEN rp.is_read = 1 THEN 1 ELSE 0 END) as read_count
            FROM issues i
            LEFT JOIN reading_progress rp ON rp.issue_order = i.order_num
            GROUP BY i.phase
            ORDER BY MIN(i.order_num)
        """
        return [dict(r) for r in self._conn().execute(q).fetchall()]

    def get_series_list(self):
        return [r["title"] for r in self._conn().execute(
            "SELECT DISTINCT title FROM issues ORDER BY title"
        ).fetchall()]

    def get_issue_page_path(self, order_num, page_num):
        """Get local file path for a page from the comics/ directory."""
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

    def get_issue_total_pages(self, order_num):
        """Count available pages on disk for an issue."""
        issue = self.get_issue(order_num)
        if not issue:
            return 0
        safe = re.sub(r'[<>:"/\\|?*]', '_', issue["title"])
        issue_dir = COMICS_DIR / safe / f"Issue_{issue['issue']:03d}"
        if not issue_dir.exists():
            return 0
        return sum(1 for f in issue_dir.iterdir()
                   if f.suffix.lower() in (".jpg", ".png", ".webp"))

    def get_available_issues(self):
        """Return list of issues that have images on disk."""
        result = []
        for row in self._conn().execute("SELECT order_num, title, issue FROM issues ORDER BY order_num").fetchall():
            safe = re.sub(r'[<>:"/\\|?*]', '_', row["title"])
            issue_dir = COMICS_DIR / safe / f"Issue_{row['issue']:03d}"
            if issue_dir.exists():
                pages = sum(1 for f in issue_dir.iterdir()
                            if f.suffix.lower() in (".jpg", ".png", ".webp"))
                if pages > 0:
                    result.append({"order_num": row["order_num"], "pages": pages})
        return result

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
        row = self._conn().execute("""
            SELECT i.order_num, i.title, i.issue, i.phase
            FROM issues i
            LEFT JOIN reading_progress rp ON rp.issue_order = i.order_num
            WHERE COALESCE(rp.is_read, 0) = 0
            ORDER BY i.order_num LIMIT 1
        """).fetchone()
        return dict(row) if row else None

    def get_stats(self):
        c = self._conn()
        total = c.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
        read_count = c.execute(
            "SELECT COUNT(*) FROM reading_progress WHERE is_read = 1"
        ).fetchone()[0]
        return {
            "total_issues": total,
            "read_issues": read_count,
            "unread_issues": total - read_count,
            "progress_percent": round(read_count / total * 100, 1) if total > 0 else 0,
        }

    # ── Reports ─────────────────────────────────────────────
    def add_report(self, issue_order, page_num, report_type, description=""):
        c = self._conn()
        now = datetime.now().isoformat()
        with self._write_lock:
            c.execute("""
                INSERT INTO reports (issue_order, page_num, report_type, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (issue_order, page_num, report_type, description, now))
            c.commit()
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_reports(self, resolved=None):
        q = """
            SELECT r.id, r.issue_order, r.page_num, r.report_type, r.description,
                   r.created_at, r.resolved, r.resolved_at, i.title, i.issue
            FROM reports r JOIN issues i ON i.order_num = r.issue_order
        """
        params = []
        if resolved is not None:
            q += " WHERE r.resolved = ?"
            params.append(int(resolved))
        q += " ORDER BY r.created_at DESC"
        return [dict(r) for r in self._conn().execute(q, params).fetchall()]

    def get_issue_reports(self, issue_order):
        return [dict(r) for r in self._conn().execute(
            "SELECT id, page_num, report_type, description, created_at, resolved "
            "FROM reports WHERE issue_order = ? ORDER BY created_at DESC",
            (issue_order,),
        ).fetchall()]

    def resolve_report(self, report_id):
        with self._write_lock:
            self._conn().execute(
                "UPDATE reports SET resolved = 1, resolved_at = ? WHERE id = ?",
                (datetime.now().isoformat(), report_id),
            )
            self._conn().commit()

    def delete_report(self, report_id):
        with self._write_lock:
            self._conn().execute("DELETE FROM reports WHERE id = ?", (report_id,))
            self._conn().commit()

    def get_flagged_issues(self):
        rows = self._conn().execute(
            "SELECT DISTINCT issue_order FROM reports WHERE resolved = 0"
        ).fetchall()
        return {r["issue_order"] for r in rows}

    # ── Sync (PC ↔ App) ────────────────────────────────────
    def get_sync_version(self):
        row = self._conn().execute(
            "SELECT value FROM sync_meta WHERE key = 'version'"
        ).fetchone()
        return row["value"] if row else datetime.now().isoformat()

    def get_sync_state(self):
        """Full state for sync: progress + reports + settings."""
        c = self._conn()
        return {
            "version": self.get_sync_version(),
            "progress": [dict(r) for r in c.execute(
                "SELECT issue_order, current_page, is_read, last_read_at FROM reading_progress"
            ).fetchall()],
            "reports": [dict(r) for r in c.execute(
                "SELECT id, issue_order, page_num, report_type, description, created_at, resolved "
                "FROM reports"
            ).fetchall()],
            "settings": {r["key"]: r["value"] for r in c.execute(
                "SELECT key, value FROM settings"
            ).fetchall()},
        }

    def apply_sync_state(self, progress_list, reports_list=None, settings_dict=None):
        """Merge sync state from the app. Last-write-wins on progress."""
        c = self._conn()
        with self._write_lock:
            for p in progress_list:
                c.execute("""
                    INSERT INTO reading_progress (issue_order, current_page, is_read, last_read_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(issue_order) DO UPDATE SET
                        current_page = CASE
                            WHEN excluded.last_read_at > COALESCE(reading_progress.last_read_at, '')
                            THEN excluded.current_page ELSE reading_progress.current_page END,
                        is_read = CASE
                            WHEN excluded.last_read_at > COALESCE(reading_progress.last_read_at, '')
                            THEN excluded.is_read ELSE reading_progress.is_read END,
                        last_read_at = MAX(excluded.last_read_at, COALESCE(reading_progress.last_read_at, ''))
                """, (
                    p["issue_order"],
                    p.get("current_page", 1),
                    int(p.get("is_read", 0)),
                    p.get("last_read_at", datetime.now().isoformat()),
                ))
            if reports_list:
                for r in reports_list:
                    # Only insert new reports (won't duplicate by checking existing)
                    existing = c.execute(
                        "SELECT id FROM reports WHERE issue_order = ? AND page_num = ? "
                        "AND report_type = ? AND created_at = ?",
                        (r["issue_order"], r.get("page_num"), r["report_type"], r["created_at"]),
                    ).fetchone()
                    if not existing:
                        c.execute("""
                            INSERT INTO reports (issue_order, page_num, report_type, description, created_at, resolved)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            r["issue_order"], r.get("page_num"), r["report_type"],
                            r.get("description", ""), r["created_at"], int(r.get("resolved", 0)),
                        ))
            if settings_dict:
                for k, v in settings_dict.items():
                    c.execute(
                        "INSERT INTO settings (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                        (str(k), str(v)),
                    )
            new_version = self._bump_version()
            c.commit()
        return new_version

    # ── Settings ────────────────────────────────────────────
    def get_settings(self):
        return {r["key"]: r["value"] for r in self._conn().execute(
            "SELECT key, value FROM settings"
        ).fetchall()}

    def set_setting(self, key, value):
        with self._write_lock:
            self._conn().execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(key), str(value)),
            )
            self._bump_version()
            self._conn().commit()
