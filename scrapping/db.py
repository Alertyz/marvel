"""
Thread-safe SQLite database for scraping persistence.

Stores issue metadata, scraped image URLs, and download status.
Separate from the server's ReaderDB — this DB tracks scraping state.
"""

import json
import os
import re
import sqlite3
import logging
import threading
from datetime import datetime
from pathlib import Path

from .config import DB_PATH, READING_ORDER_PATH, COMICS_DIR
from .slugs import build_issue_url, title_to_slug, safe_title, UNAVAILABLE_TITLES

log = logging.getLogger(__name__)


class ComicDB:
    """Thread-safe SQLite database for URL persistence and download tracking."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(DB_PATH)
        self._local = threading.local()
        self._write_lock = threading.Lock()
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        """One connection per thread."""
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
                order_num     INTEGER PRIMARY KEY,
                title         TEXT NOT NULL,
                issue         INTEGER NOT NULL,
                phase         TEXT,
                event         TEXT,
                year          TEXT,
                slug          TEXT,
                url           TEXT,
                total_pages   INTEGER DEFAULT 0,
                scrape_status TEXT DEFAULT 'pending',
                scraped_at    TEXT,
                bookmark      INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS pages (
                issue_order   INTEGER NOT NULL,
                page_num      INTEGER NOT NULL,
                image_url     TEXT NOT NULL,
                file_path     TEXT,
                downloaded    INTEGER DEFAULT 0,
                file_size     INTEGER DEFAULT 0,
                downloaded_at TEXT,
                PRIMARY KEY (issue_order, page_num),
                FOREIGN KEY (issue_order) REFERENCES issues(order_num)
            );
            CREATE TABLE IF NOT EXISTS validation_flags (
                issue_order   INTEGER NOT NULL,
                flag_type     TEXT NOT NULL,
                message       TEXT,
                created_at    TEXT NOT NULL,
                resolved      INTEGER DEFAULT 0,
                PRIMARY KEY (issue_order, flag_type)
            );
            CREATE INDEX IF NOT EXISTS idx_pages_pending
                ON pages(downloaded) WHERE downloaded = 0;
            CREATE INDEX IF NOT EXISTS idx_issues_scrape
                ON issues(scrape_status);
        """)
        c.commit()

    # ── Populate from reading_order.json ────────────────────
    def populate_issues(self, issues_list: list[dict]):
        """Upsert issues from reading_order.json (idempotent).

        scrape_status is included in the INSERT so that unavailable titles are
        correctly marked on first insertion.  The ON CONFLICT clause deliberately
        does NOT update scrape_status, so any status set by the user (e.g. via
        `rescrape`) is never silently overwritten by a subsequent load.
        """
        c = self._conn()
        skipped = 0
        valid_orders = []
        with self._write_lock:
            for iss in issues_list:
                valid_orders.append(iss["order"])
                url = build_issue_url(iss["title"], iss["issue"])
                if url is None:
                    slug = iss["title"]
                    initial_status = "unavailable"
                    skipped += 1
                else:
                    slug = title_to_slug(iss["title"])
                    initial_status = "pending"

                # scrape_status is part of the INSERT so it is set correctly
                # when a row is first created.  The ON CONFLICT UPDATE intentionally
                # omits scrape_status — existing rows keep whatever status they have,
                # including a 'pending' set by `rescrape`.
                c.execute("""
                    INSERT INTO issues (order_num, title, issue, phase, event, year,
                                        slug, url, bookmark, scrape_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(order_num) DO UPDATE SET
                        title=excluded.title, issue=excluded.issue,
                        phase=excluded.phase, event=excluded.event,
                        year=excluded.year, slug=excluded.slug,
                        url=CASE WHEN excluded.url != '' THEN excluded.url ELSE issues.url END,
                        bookmark=excluded.bookmark
                """, (
                    iss["order"], iss["title"], iss["issue"],
                    iss.get("phase", ""), iss.get("event", ""),
                    iss.get("year", ""), slug, url or "",
                    int(iss.get("bookmark", False)),
                    initial_status,
                ))

            if valid_orders:
                existing_orders = [r[0] for r in c.execute("SELECT order_num FROM issues").fetchall()]
                to_delete = set(existing_orders) - set(valid_orders)
                for chunk in [list(to_delete)[i:i+500] for i in range(0, len(to_delete), 500)]:
                    if not chunk: continue
                    placeholders = ",".join("?" for _ in chunk)
                    c.execute(f"DELETE FROM pages WHERE issue_order IN ({placeholders})", chunk)
                    c.execute(f"DELETE FROM validation_flags WHERE issue_order IN ({placeholders})", chunk)
                    c.execute(f"DELETE FROM issues WHERE order_num IN ({placeholders})", chunk)

            c.commit()
        log.info(f"DB: {len(issues_list)} issues sincronizadas ({skipped} indisponiveis)")

    def load_and_populate(self):
        """Load reading_order.json and populate DB."""
        path = Path(READING_ORDER_PATH)
        if not path.exists():
            log.error(f"reading_order.json nao encontrado: {path}")
            return
        with open(str(path), "r", encoding="utf-8") as f:
            data = json.load(f)
        self.populate_issues(data["issues"])

    # ── Queries ─────────────────────────────────────────────
    def get_issues_to_scrape(self, filters: dict | None = None) -> list:
        q = "SELECT * FROM issues WHERE scrape_status IN ('pending','failed')"
        params: list = []
        q, params = self._apply_filters(q, params, filters)
        q += " ORDER BY order_num"
        return self._conn().execute(q, params).fetchall()

    def get_issues_to_download(self, filters: dict | None = None) -> list:
        q = """SELECT DISTINCT i.* FROM issues i
               JOIN pages p ON p.issue_order = i.order_num
               WHERE i.scrape_status = 'done' AND p.downloaded = 0"""
        params: list = []
        q, params = self._apply_filters(q, params, filters)
        q += " ORDER BY i.order_num"
        return self._conn().execute(q, params).fetchall()

    def get_all_pending_pages(self, filters: dict | None = None) -> list:
        q = """SELECT p.* FROM pages p
               JOIN issues i ON i.order_num = p.issue_order
               WHERE p.downloaded = 0"""
        params: list = []
        q, params = self._apply_filters(q, params, filters)
        q += " ORDER BY p.issue_order, p.page_num"
        return self._conn().execute(q, params).fetchall()

    def get_issue(self, order_num: int):
        return self._conn().execute(
            "SELECT * FROM issues WHERE order_num=?", (order_num,)
        ).fetchone()

    def get_issue_pages(self, order_num: int) -> list:
        return self._conn().execute(
            "SELECT * FROM pages WHERE issue_order=? ORDER BY page_num",
            (order_num,),
        ).fetchall()

    def _apply_filters(self, q: str, params: list, filters: dict | None):
        if not filters:
            return q, params
        if filters.get("series"):
            q += " AND LOWER(i.title) LIKE ?"
            params.append(f"%{filters['series'].lower()}%")
        if filters.get("phase"):
            q += " AND LOWER(i.phase) LIKE ?"
            params.append(f"%{filters['phase'].lower()}%")
        if filters.get("from_bookmark"):
            q += " AND i.order_num >= (SELECT MIN(order_num) FROM issues WHERE bookmark=1)"
        if filters.get("order_min"):
            q += " AND i.order_num >= ?"
            params.append(filters["order_min"])
        if filters.get("order_max"):
            q += " AND i.order_num <= ?"
            params.append(filters["order_max"])
        return q, params

    # ── Writes ──────────────────────────────────────────────
    def save_scraped_urls(self, order_num: int, image_urls: dict[int, str]):
        """Atomically save all scraped image URLs for one issue."""
        c = self._conn()
        with self._write_lock:
            for page_num, url in image_urls.items():
                c.execute("""
                    INSERT INTO pages (issue_order, page_num, image_url)
                    VALUES (?, ?, ?)
                    ON CONFLICT(issue_order, page_num) DO UPDATE SET
                        image_url=excluded.image_url
                """, (order_num, page_num, url))
            c.execute("""
                UPDATE issues
                SET scrape_status='done', total_pages=?, scraped_at=?
                WHERE order_num=?
            """, (len(image_urls), datetime.now().isoformat(), order_num))
            c.commit()
        return self.db_path

    def mark_scrape_failed(self, order_num: int, reason: str = "failed"):
        c = self._conn()
        with self._write_lock:
            c.execute(
                "UPDATE issues SET scrape_status=? WHERE order_num=?",
                (reason, order_num),
            )
            c.commit()

    def mark_page_downloaded(self, issue_order: int, page_num: int,
                             file_path: str, file_size: int):
        c = self._conn()
        with self._write_lock:
            c.execute("""
                UPDATE pages
                SET downloaded=1, file_path=?, file_size=?, downloaded_at=?
                WHERE issue_order=? AND page_num=?
            """, (file_path, file_size, datetime.now().isoformat(),
                  issue_order, page_num))
            c.commit()

    def reset_page(self, issue_order: int, page_num: int):
        c = self._conn()
        with self._write_lock:
            c.execute(
                "UPDATE pages SET downloaded=0, file_size=0 "
                "WHERE issue_order=? AND page_num=?",
                (issue_order, page_num),
            )
            c.commit()

    def reset_issue_scrape(self, order_num: int):
        """Full reset: delete all scraped URLs and mark for re-scrape."""
        c = self._conn()
        with self._write_lock:
            c.execute("DELETE FROM pages WHERE issue_order=?", (order_num,))
            c.execute(
                "UPDATE issues SET scrape_status='pending', total_pages=0, "
                "scraped_at=NULL WHERE order_num=?",
                (order_num,),
            )
            c.commit()

    def clear_all_page_urls(self, filters: dict | None = None):
        """
        Delete all rows from the pages table (scraped image URLs) and reset
        scrape_status to 'pending' for affected issues.

        The issues table itself is untouched — titles, issue numbers, phases,
        and the original comic URLs are all preserved.  Only the scraped image
        URLs and download state are cleared so the scrape phase can run again.

        If filters are provided (series/phase/order_min/order_max), only the
        matching issues are cleared.  Without filters, everything is cleared.
        """
        c = self._conn()
        with self._write_lock:
            if not filters:
                c.execute("DELETE FROM pages")
                c.execute(
                    "UPDATE issues SET scrape_status='pending', total_pages=0, "
                    "scraped_at=NULL WHERE scrape_status NOT IN ('unavailable')"
                )
                log.info("clear_all_page_urls: todas as URLs de páginas removidas")
            else:
                # Build a subquery to get the matching order_nums
                sub = "SELECT order_num FROM issues WHERE 1=1"
                params: list = []
                if filters.get("series"):
                    sub += " AND LOWER(title) LIKE ?"
                    params.append(f"%{filters['series'].lower()}%")
                if filters.get("phase"):
                    sub += " AND LOWER(phase) LIKE ?"
                    params.append(f"%{filters['phase'].lower()}%")
                if filters.get("order_min"):
                    sub += " AND order_num >= ?"
                    params.append(filters["order_min"])
                if filters.get("order_max"):
                    sub += " AND order_num <= ?"
                    params.append(filters["order_max"])

                count = c.execute(
                    f"SELECT COUNT(*) FROM pages WHERE issue_order IN ({sub})", params
                ).fetchone()[0]
                c.execute(f"DELETE FROM pages WHERE issue_order IN ({sub})", params)
                c.execute(
                    f"UPDATE issues SET scrape_status='pending', total_pages=0, "
                    f"scraped_at=NULL WHERE order_num IN ({sub}) "
                    f"AND scrape_status NOT IN ('unavailable')",
                    params,
                )
                log.info(f"clear_all_page_urls: {count} URLs removidas (filtro aplicado)")
            c.commit()

    def reset_issue_downloads(self, order_num: int):
        """Reset only download flags — keeps scraped URLs intact for re-download."""
        c = self._conn()
        with self._write_lock:
            c.execute(
                "UPDATE pages SET downloaded=0, file_size=0, downloaded_at=NULL "
                "WHERE issue_order=?",
                (order_num,),
            )
            c.commit()

    # ── Validation flags ────────────────────────────────────
    def set_flag(self, issue_order: int, flag_type: str, message: str):
        c = self._conn()
        with self._write_lock:
            c.execute("""
                INSERT INTO validation_flags (issue_order, flag_type, message, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(issue_order, flag_type) DO UPDATE SET
                    message=excluded.message, created_at=excluded.created_at, resolved=0
            """, (issue_order, flag_type, message, datetime.now().isoformat()))
            c.commit()

    def resolve_flag(self, issue_order: int, flag_type: str):
        c = self._conn()
        with self._write_lock:
            c.execute(
                "UPDATE validation_flags SET resolved=1 WHERE issue_order=? AND flag_type=?",
                (issue_order, flag_type),
            )
            c.commit()

    def get_flags(self, resolved: bool = False) -> list:
        c = self._conn()
        return c.execute(
            "SELECT vf.*, i.title, i.issue FROM validation_flags vf "
            "JOIN issues i ON i.order_num = vf.issue_order "
            "WHERE vf.resolved = ? ORDER BY vf.issue_order",
            (int(resolved),),
        ).fetchall()

    # ── Status ──────────────────────────────────────────────
    def get_status(self, filters: dict | None = None) -> dict:
        c = self._conn()
        bf = ""
        params: list = []
        if filters:
            if filters.get("series"):
                bf += " AND LOWER(title) LIKE ?"
                params.append(f"%{filters['series'].lower()}%")
            if filters.get("phase"):
                bf += " AND LOWER(phase) LIKE ?"
                params.append(f"%{filters['phase'].lower()}%")
            if filters.get("from_bookmark"):
                bf += " AND order_num >= (SELECT MIN(order_num) FROM issues WHERE bookmark=1)"

        total = c.execute(f"SELECT COUNT(*) FROM issues WHERE 1=1 {bf}", params).fetchone()[0]
        scraped = c.execute(f"SELECT COUNT(*) FROM issues WHERE scrape_status='done' {bf}", params).fetchone()[0]
        failed = c.execute(f"SELECT COUNT(*) FROM issues WHERE scrape_status='failed' {bf}", params).fetchone()[0]
        captcha = c.execute(f"SELECT COUNT(*) FROM issues WHERE scrape_status='captcha' {bf}", params).fetchone()[0]
        unavailable = c.execute(f"SELECT COUNT(*) FROM issues WHERE scrape_status='unavailable' {bf}", params).fetchone()[0]

        # Page-level stats (need alias replacement for join)
        pf = bf.replace("title", "i.title").replace("phase", "i.phase").replace("order_num", "i.order_num")
        total_pages = c.execute(
            f"SELECT COUNT(*) FROM pages p JOIN issues i ON i.order_num=p.issue_order WHERE 1=1 {pf}",
            params,
        ).fetchone()[0]
        downloaded_pages = c.execute(
            f"SELECT COUNT(*) FROM pages p JOIN issues i ON i.order_num=p.issue_order WHERE p.downloaded=1 {pf}",
            params,
        ).fetchone()[0]

        flags = c.execute("SELECT COUNT(*) FROM validation_flags WHERE resolved=0").fetchone()[0]

        return {
            "total_issues": total,
            "scraped": scraped,
            "scrape_failed": failed,
            "scrape_captcha": captcha,
            "scrape_unavailable": unavailable,
            "scrape_pending": total - scraped - failed - captcha - unavailable,
            "total_pages": total_pages,
            "downloaded_pages": downloaded_pages,
            "pending_pages": total_pages - downloaded_pages,
            "active_flags": flags,
        }

    def get_detail_status(self, filters: dict | None = None) -> list:
        q = """SELECT i.order_num, i.title, i.issue, i.phase, i.scrape_status,
                      i.total_pages,
                      COUNT(CASE WHEN p.downloaded=1 THEN 1 END) as done_pages,
                      COUNT(p.page_num) as url_pages
               FROM issues i
               LEFT JOIN pages p ON p.issue_order = i.order_num
               WHERE 1=1"""
        params: list = []
        q, params = self._apply_filters(q, params, filters)
        q += " GROUP BY i.order_num ORDER BY i.order_num"
        return self._conn().execute(q, params).fetchall()

    def close(self):
        if hasattr(self._local, "conn"):
            self._local.conn.close()