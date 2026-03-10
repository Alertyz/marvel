#!/usr/bin/env python3
"""
X-Men Comic Downloader v2 — Parallel & Persistent
===================================================
Two-phase architecture with SQLite URL database:

  Phase 1 (scrape):   N browser workers extract image URLs → SQLite
  Phase 2 (download): M HTTP workers download images from saved URLs

Commands:
  python downloader.py scrape                        # Scrape all pending URLs
  python downloader.py scrape --workers 4            # 4 parallel browsers
  python downloader.py download                      # Download all pending images
  python downloader.py download --workers 30         # 30 parallel HTTP downloads
  python downloader.py run                           # Scrape + Download in sequence
  python downloader.py verify                        # Check for missing/corrupt pages
  python downloader.py verify --fix                  # Reset missing pages for re-download
  python downloader.py status                        # Show progress overview
  python downloader.py status --detail               # Detailed per-issue status
  python downloader.py list-phases                   # List all phases
  python downloader.py list-series                   # List all series

Filters (work with scrape/download/run/status):
  --series "X-Men"        # Filter by series name
  --phase "Fall of X"     # Filter by phase
  --from-bookmark         # Only after the bookmark
  --order 10-50           # Specific order range
"""

import json
import os
import re
import sys
import time
import atexit
import signal
import sqlite3
import argparse
import logging
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Config ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://readcomiconline.li"
ISSUE_URL = BASE_URL + "/Comic/{slug}/Issue-{issue}?quality=hq"
COMIC_URL = BASE_URL + "/Comic/{slug}"
OUTPUT_DIR = str(PROJECT_ROOT / "comics")
DB_FILE = str(PROJECT_ROOT / "comics.db")
DELAY_BETWEEN_ISSUES = 2.0
MIN_IMAGE_SIZE = 1000  # bytes — below this it's corrupt/empty

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Chrome cleanup ──────────────────────────────────────────
_active_drivers = []
_drivers_lock = threading.Lock()

def _register_driver(driver):
    with _drivers_lock:
        _active_drivers.append(driver)

def _unregister_driver(driver):
    with _drivers_lock:
        try:
            _active_drivers.remove(driver)
        except ValueError:
            pass

def _cleanup_all_chrome():
    """Quit all tracked drivers, then kill any remaining chrome/chromedriver."""
    with _drivers_lock:
        for d in _active_drivers:
            try:
                d.quit()
            except Exception:
                pass
        _active_drivers.clear()
    # Force-kill any leftover chromedriver/chrome spawned by this session
    for proc_name in ("chromedriver.exe", "chrome.exe"):
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", proc_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

def _signal_handler(sig, frame):
    log.info("\nInterrompido — fechando browsers...")
    _cleanup_all_chrome()
    sys.exit(1)

atexit.register(_cleanup_all_chrome)
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# ── Slug mapping ────────────────────────────────────────────
SLUG_MAP = {
    "House of X": "House-of-X",
    "Powers of X": "Powers-of-X",
    "X-Men": "X-Men-2019",
    "X-Men (2021)": "X-Men-2021",
    "X-Men (2024)": "X-Men-2024",
    "Marauders": "Marauders",
    "Marauders (2022)": "Marauders-2022",
    "Excalibur": "Excalibur-2019",
    "New Mutants": "New-Mutants-2019",
    "X-Force": "X-Force-2019-2",
    "X-Force (2024)": "X-Force-2024",
    "Fallen Angels": "Fallen-Angels",
    "Wolverine": "Wolverine-2020",
    "Wolverine (2024)": "Wolverine-2024",
    "Cable": "Cable-2020",
    "Cable (2024)": "Cable-2024",
    "X-Men/Fantastic Four": "X-Men-Fantastic-Four",
    "X-Factor": "X-Factor-2020",
    "X-Factor (2024)": "X-Factor-2024",
    "Hellions": "Hellions",
    "S.W.O.R.D.": "S-W-O-R-D-2020",
    "Children of the Atom": "Children-of-the-Atom",
    "Way of X": "Way-of-X",
    "X-Corp": "X-Corp",
    "Inferno": "Inferno-2021",
    "X-Men: The Onslaught Revelation": "X-Men-Onslaught-Revelation",
    "X of Swords: Stasis": "X-Of-Swords-Stasis",
    "X of Swords: Destruction": "X-Of-Swords-Destruction",
    "Immortal X-Men": "Immortal-X-Men",
    "X-Men Red (2022)": "X-Men-Red-2022",
    "Knights of X": "Knights-of-X",
    "Legion of X": "Legion-of-X",
    "X-Terminators": "X-Terminators-2022",
    "Sabretooth": "Sabretooth-2022",
    "Invincible Iron Man": "The-Invincible-Iron-Man-2022",
    "A.X.E.: Eve of Judgment": "A-X-E-Eve-Of-Judgment",
    "A.X.E.: Judgment Day": "A-X-E-Judgment-Day",
    "A.X.E.: Death to the Mutants": "A-X-E-Death-to-the-Mutants",
    "A.X.E.: Judgment Day Omega": "A-X-E-Judgment-Day-Omega",
    "Uncanny Avengers (2023)": "Uncanny-Avengers-2023",
    "Children of the Vault (2023)": "Children-of-the-Vault",
    "Dark X-Men": "Dark-X-Men-2023",
    "Alpha Flight (2023)": "Alpha-Flight-2023",
    "Realm of X": "Realm-of-X",
    "Jean Grey": "Jean-Grey-2023",
    "Ms. Marvel: The New Mutant": "Ms-Marvel-The-New-Mutant",
    "Storm and the Brotherhood of Mutants": "Storm-the-Brotherhood-of-Mutants",
    "Fall of the House of X": "Fall-of-the-House-of-X",
    "Rise of the Powers of X": "Rise-of-the-Powers-of-X",
    "Dead X-Men": "Dead-X-Men",
    "Resurrection of Magneto": "Resurrection-of-Magneto",
    "X-Men Forever (2024)": "X-Men-Forever-2024",
    "Phoenix": "Phoenix-2024",
    "NYX": "NYX-2024",
    "Uncanny X-Men (2024)": "Uncanny-X-Men-2024",
    "Exceptional X-Men": "Exceptional-X-Men",
    "Storm (2024)": "Storm-2024",
    "Dazzler (2024)": "Dazzler-2024",
    "Mystique (2024)": "Mystique-2024",
    "Sentinels (2024)": "Sentinels-2024",
    "Psylocke (2024)": "Psylocke-2024",
    "Laura Kinney: Wolverine": "Laura-Kinney-Wolverine",
    "Magik": "Magik-2025",
    "Weapon X-Men": "Weapon-X-Men-Existed",
    "Storm: Earth's Mightiest Mutant": "Storm-Earth-s-Mightiest-Mutant",
    "Secret X-Men": "The-Secret-X-Men",
    "Giant-Size X-Men (2025)": "Giant-Size-X-Men-2025",
    "Deadpool/Wolverine": "Deadpool-Wolverine",
    "Sinister's Six": "Sinister-s-Six",
    # ── Auto-added by find_slugs.py ──
    "Amazing X-Men (2025)": "Amazing-X-Men-2025",
    "Astonishing Iceman": "Astonishing-Iceman",
    "Betsy Braddock: Captain Britain": "Betsy-Braddock-Captain-Britain",
    "Binary": "Binary",
    "Bishop: War College": "Bishop-War-College",
    "Cable: Love and Chrome": "Cable-Love-and-Chrome",
    "Champions (2020)": "Champions-2020",
    "Cloak or Dagger": "Cloak-or-Dagger",
    "Dark Web: X-Men": "Dark-Web-X-Men",
    "Devil's Reign: X-Men": "Devil-s-Reign-X-Men",
    "Empyre: X-Men": "Empyre-X-Men",
    "Eternals (2021)": "Eternals-2021",
    "Expatriate X-Men": "Expatriate-X-Men",
    "Hellverine Vol 1": "Hellverine",
    "Hellverine Vol 2": "Hellverine-Vol-2",
    "Immoral X-Men": "Immoral-X-Men",
    "Iron & Frost": "Iron-Frost",
    "King in Black": "King-in-Black",
    "Laura Kinney: Sabretooth": "Laura-Kinney-Sabretooth",
    "Life of Wolverine Infinity Comic": "Life-of-Wolverine-Infinity-Comic",
    "Longshots": "Longshots",
    "Love Unlimited Infinity Comic": "Love-Unlimited-Infinity-Comic",
    "Ms. Marvel: Mutant Menace": "Ms-Marvel-Mutant-Menace",
    "New Mutants: Lethal Legion": "New-Mutants-Lethal-Legion",
    "Nightcrawlers": "Nightcrawlers",
    "Omega Kids": "Omega-Kids",
    "Radioactive Spider-Man": "Radioactive-Spider-Man",
    "Rogue & Gambit": "Rogue-Gambit",
    "Rogue Storm": "Rogue-Storm",
    "Sabretooth & The Exiles": "Sabretooth-The-Exiles",
    "Sabretooth & the Exiles": "Sabretooth-the-Exiles",
    "The Last Wolverine": "The-Last-Wolverine",
    "Unbreakable X-Men": "Unbreakable-X-Men",
    "Uncanny Spider-Man": "Uncanny-Spider-Man",
    "Undeadpool": "Undeadpool",
    "X Deaths of Wolverine": "X-Deaths-of-Wolverine",
    "X Lives of Wolverine": "X-Lives-of-Wolverine",
    "X-Men Unlimited Infinity Comic": "X-Men-Unlimited-Infinity-Comic",
    "X-Men: Book of Revelation": "X-Men-Book-of-Revelation",
    "X-Men: The Trial of Magneto": "X-Men-The-Trial-of-Magneto",
    "X-Vengers": "X-Vengers",
}

# Titles whose URL uses a named path instead of /Issue-N
# Maps title -> full URL path after /Comic/
SPECIAL_ISSUE_URL = {
    "Giant-Size X-Men: Jean Grey and Emma Frost": "Giant-Size-X-Men-2020/Jean-Grey-And-Emma-Frost",
    "Giant-Size X-Men: Nightcrawler": "Giant-Size-X-Men-2020/Nightcrawler",
    "Giant-Size X-Men: Magneto": "Giant-Size-X-Men-2020/Magneto",
    "Giant-Size X-Men: Fantomex": "Giant-Size-X-Men-2020/Fantomex",
    "Giant-Size X-Men: Storm": "Giant-Size-X-Men-2020/Full",
    # One-shots that use /Full instead of /Issue-N
    "X of Swords: Stasis": "X-Of-Swords-Stasis/Full",
    "X of Swords: Destruction": "X-Of-Swords-Destruction/Full",
    "X-Men: The Onslaught Revelation": "X-Men-Onslaught-Revelation/Full",
    "A.X.E.: Judgment Day Omega": "A-X-E-Judgment-Day-Omega/Full",
    "X-Manhunt Omega": "X-Manhunt-Omega/Full",
    # Giant-Size 2025 one-shots
    "Giant-Size Age of Apocalypse": "Giant-Size-Age-of-Apocalypse/Full",
    "Giant-Size Dark Phoenix Saga": "Giant-Size-Dark-Phoenix-Saga/Full",
    "Giant-Size House of M": "Giant-Size-House-of-M/Full",
    # Other one-shots
    "Timeslide": "Timeslide/Full",
    "X-Men: Xavier's Secret": "X-Men-Xavier-s-Secret/Full",
    "X-Men: Demons and Death": "X-Men-From-the-Ashes-Demons-and-Death/Full",
    "X-Men: Age of Revelation Overture": "X-Men-Age-of-Revelation-Overture/Full",
    "X-Men: Age of Revelation Finale": "X-Men-Age-of-Revelation-Finale/Full",
    "World of Revelation": "World-of-Revelation/Full",
    "X-Men: Hellfire Vigil": "X-Men-Hellfire-Vigil/Full",
    "X-Men: Tooth and Claw": "X-Men-Tooth-and-Claw/Full",
    # ── Auto-added by find_slugs.py ──
    "Before the Fall: Heralds of Apocalypse": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=216472",
    "Before the Fall: Mutant First Strike": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=215834",
    "Before the Fall: Sinister Four": "X-Men-Before-the-Fall-Sons-of-X/The-Sinister-Four?id=216689",
    "Before the Fall: Sons of X": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=214579",
    "Cable: Reloaded": "Cable-Reloaded/Full",
    "Cyclops (2026)": "Cyclops-2026/Full",
    "Dark Web": "Dark-Web-2023/Full",
    "Dark Web: Finale": "Dark-Web-Finale/Full",
    "Deadpool": "Deadpool-2020/Full",
    "Death of Doctor Strange: X-Men/Black Knight": "Death-of-Doctor-Strange-One-Shots/X-Men-Black-Knight",
    "Generation: X-23": "Generation-X-23/Full",
    "Ghost Rider/Wolverine: Weapons of Vengeance Alpha": "Ghost-Rider-Wolverine-Weapons-of-Vengeance-Alpha/Full",
    "Ghost Rider/Wolverine: Weapons of Vengeance Omega": "Ghost-Rider-Wolverine-Weapons-of-Vengeance-Omega/Issue-1",
    "Giant-Size X-Men: Thunderbird": "Giant-Size-X-Men-Thunderbird/Full",
    "Inglorious X-Force": "Inglorious-X-Force/Full",
    "King in Black: Marauders": "King-In-Black-One-Shots/Marauders",
    "Magik and Colossus": "Magik-and-Colossus/Full",
    "Marauders Annual": "Marauders/Annual-1",
    "Marvel Voices: Community": "Marvel-s-Voices-Community/TPB",
    "Marvel Voices: Heritage": "Marvel-s-Voices-Heritage/Full",
    "Marvel Voices: Identity": "Marvel-s-Voices-Identity/Full",
    "Marvel Voices: Indigenous Voices": "Marvel-s-Voices-Indigenous-Voices/Full",
    "Marvel Voices: Legacy": "Marvel-s-Voices-Legacy/Full",
    "Marvel Voices: Pride": "Marvel-s-Voices-Pride-2022/Full",
    "Marvel's Voices: X-Men": "Marvel-s-Voices-X-Men/Issue-1",
    "Moonstar": "Moonstar/Issue-1",
    "Outlawed": "Outlawed/Full",
    "Planet-Size X-Men": "Planet-Size-X-Men/Issue-1",
    "Rogue (2026)": "Rogue-2026/Issue-1",
    "Sins of Sinister": "Sins-of-Sinister/Issue-1",
    "Sins of Sinister: Dominion": "Sins-Of-Sinister-Dominion/Issue-1",
    "Uncanny Avengers Annual (2023)": "Avengers-2023/Annual-1",
    "Wade Wilson: Deadpool": "Wade-Wilson-Deadpool/Issue-1",
    "X of Swords: Creation": "X-Of-Swords-Creation/Issue-1",
    "X-Force Annual": "X-Force-2019-2/Annual-1",
    "X-Men Annual (2022)": "X-Men-2021/Annual-1",
    "X-Men Blue: Origins": "X-Men-Blue-Origins/Full",
    "X-Men: Before the Fall - Heralds of Apocalypse": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=216472",
    "X-Men: Before the Fall - Mutant First Strike": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=215834",
    "X-Men: Before the Fall - Sinister Four": "X-Men-Before-the-Fall-Sons-of-X/The-Sinister-Four?id=216689",
    "X-Men: Before the Fall - Sons of X": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=214579",
    "X-Men: Curse of the Man-Thing": "Curse-Of-The-Man-Thing/X-Men",
    "X-Men: Hellfire Gala (2022)": "X-Men-Hellfire-Gala/Issue-1",
    "X-Men: Hellfire Gala (2023)": "X-Men-Hellfire-Gala-2023/Issue-1",
    "X-Men: The Wedding Special": "X-Men-The-Wedding-Special/TPB",
}

# Titles not available on the site (too new or rare one-shots)
UNAVAILABLE_TITLES = {
    "X-Men United",
    # ── Auto-added by find_slugs.py ──
    "X-Men: Hellfire Gala (2024)",
}


def title_to_slug(title, year=""):
    slug = title.strip()
    if slug in SLUG_MAP:
        return SLUG_MAP[slug]
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    return slug


def build_issue_url(title, issue, year=""):
    # Special named-path issues (Giant-Size X-Men one-shots, etc.)
    if title in SPECIAL_ISSUE_URL:
        path = SPECIAL_ISSUE_URL[title]
        sep = "&" if "?" in path else "?"
        return BASE_URL + "/Comic/" + path + sep + "quality=hq"
    # Unavailable titles
    if title in UNAVAILABLE_TITLES:
        return None
    return ISSUE_URL.format(slug=title_to_slug(title, year), issue=issue)


def build_comic_url(title, year=""):
    if title in SPECIAL_ISSUE_URL:
        slug = SPECIAL_ISSUE_URL[title].split("/")[0]
        return COMIC_URL.format(slug=slug)
    return COMIC_URL.format(slug=title_to_slug(title, year))


def safe_title(title):
    return re.sub(r'[<>:"/\\|?*]', '_', title)


# ════════════════════════════════════════════════════════════
#  DATABASE
# ════════════════════════════════════════════════════════════
class ComicDB:
    """Thread-safe SQLite database for URL persistence."""

    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self._local = threading.local()
        self._write_lock = threading.Lock()
        self._init_schema()

    def _conn(self):
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
                order_num    INTEGER PRIMARY KEY,
                title        TEXT NOT NULL,
                issue        INTEGER NOT NULL,
                phase        TEXT,
                event        TEXT,
                year         TEXT,
                slug         TEXT,
                url          TEXT,
                total_pages  INTEGER DEFAULT 0,
                scrape_status TEXT DEFAULT 'pending',   -- pending | done | failed | captcha | unavailable
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
            CREATE INDEX IF NOT EXISTS idx_pages_pending
                ON pages(downloaded) WHERE downloaded = 0;
            CREATE INDEX IF NOT EXISTS idx_issues_scrape
                ON issues(scrape_status);
        """)
        c.commit()

    # ── Populate from reading_order.json ────────────────────
    def populate_issues(self, issues_list):
        """Upsert issues from reading_order.json (idempotent)."""
        c = self._conn()
        skipped = 0
        with self._write_lock:
            for iss in issues_list:
                url = build_issue_url(iss["title"], iss["issue"], iss.get("year", ""))
                if url is None:
                    # Title not available on site — mark as unavailable
                    slug = iss["title"]
                    scrape_status = "unavailable"
                else:
                    slug = title_to_slug(iss["title"], iss.get("year", ""))
                    scrape_status = None
                c.execute("""
                    INSERT INTO issues (order_num, title, issue, phase, event, year, slug, url, bookmark)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(order_num) DO UPDATE SET
                        title=excluded.title, issue=excluded.issue, phase=excluded.phase,
                        event=excluded.event, year=excluded.year, slug=excluded.slug,
                        url=excluded.url, bookmark=excluded.bookmark
                """, (
                    iss["order"], iss["title"], iss["issue"],
                    iss.get("phase", ""), iss.get("event", ""), iss.get("year", ""),
                    slug, url or "", int(iss.get("bookmark", False)),
                ))
                if scrape_status == "unavailable":
                    c.execute("UPDATE issues SET scrape_status = 'unavailable' WHERE order_num = ? AND scrape_status IN ('pending','failed')",
                              (iss["order"],))
                    skipped += 1
            c.commit()
        log.info(f"DB: {len(issues_list)} issues sincronizadas ({skipped} indisponiveis)")

    # ── Migrate old progress ────────────────────────────────
    def migrate_old_progress(self, progress_file="download_progress.json", output_dir=OUTPUT_DIR):
        """Import data from the old download_progress.json."""
        if not os.path.exists(progress_file):
            return 0
        with open(progress_file, "r") as f:
            old = json.load(f)
        done_orders = old.get("downloaded", [])
        if not done_orders:
            return 0
        c = self._conn()
        migrated = 0
        with self._write_lock:
            for order in done_orders:
                row = c.execute(
                    "SELECT title, issue, total_pages FROM issues WHERE order_num=?", (order,)
                ).fetchone()
                if not row:
                    continue
                title, issue, _ = row["title"], row["issue"], row["total_pages"]
                issue_dir = os.path.join(output_dir, safe_title(title), f"Issue_{issue:03d}")
                if not os.path.isdir(issue_dir):
                    continue
                files = [f for f in os.listdir(issue_dir) if f.endswith(('.jpg', '.png', '.webp'))]
                if files:
                    c.execute(
                        "UPDATE issues SET scrape_status='done', total_pages=? WHERE order_num=?",
                        (len(files), order),
                    )
                    for f_name in sorted(files):
                        try:
                            num = int(re.search(r'(\d+)', f_name).group(1))
                        except (AttributeError, ValueError):
                            continue
                        fpath = os.path.join(issue_dir, f_name)
                        fsize = os.path.getsize(fpath)
                        c.execute("""
                            INSERT OR IGNORE INTO pages (issue_order, page_num, image_url, file_path, downloaded, file_size)
                            VALUES (?, ?, ?, ?, 1, ?)
                        """, (order, num, "migrated", fpath, fsize))
                    migrated += 1
            c.commit()
        if migrated:
            log.info(f"DB: migradas {migrated} issues do progress antigo")
        return migrated

    # ── Queries ─────────────────────────────────────────────
    def get_issues_to_scrape(self, filters=None):
        """Return issues that still need URL scraping."""
        q = "SELECT * FROM issues WHERE scrape_status IN ('pending','failed')"
        params = []
        q, params = self._apply_filters(q, params, filters)
        q += " ORDER BY order_num"
        return self._conn().execute(q, params).fetchall()

    def get_issues_to_download(self, filters=None):
        """Return issues that have scraped URLs but pending page downloads."""
        q = """SELECT DISTINCT i.* FROM issues i
               JOIN pages p ON p.issue_order = i.order_num
               WHERE i.scrape_status = 'done' AND p.downloaded = 0"""
        params = []
        q, params = self._apply_filters(q, params, filters)
        q += " ORDER BY i.order_num"
        return self._conn().execute(q, params).fetchall()

    def get_pending_pages(self, order_num=None):
        """Return pages that haven't been downloaded yet."""
        if order_num:
            return self._conn().execute(
                "SELECT * FROM pages WHERE downloaded=0 AND issue_order=? ORDER BY page_num",
                (order_num,),
            ).fetchall()
        return self._conn().execute(
            "SELECT * FROM pages WHERE downloaded=0 ORDER BY issue_order, page_num"
        ).fetchall()

    def get_all_pending_pages(self, filters=None):
        """Return all pending pages matching filters."""
        q = """SELECT p.* FROM pages p
               JOIN issues i ON i.order_num = p.issue_order
               WHERE p.downloaded = 0"""
        params = []
        q, params = self._apply_filters(q, params, filters)
        q += " ORDER BY p.issue_order, p.page_num"
        return self._conn().execute(q, params).fetchall()

    def _apply_filters(self, q, params, filters):
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
    def save_scraped_urls(self, order_num, image_urls):
        """Save scraped image URLs for an issue.  image_urls = {page_num: url}"""
        c = self._conn()
        with self._write_lock:
            for page_num, url in image_urls.items():
                c.execute("""
                    INSERT INTO pages (issue_order, page_num, image_url)
                    VALUES (?, ?, ?)
                    ON CONFLICT(issue_order, page_num) DO UPDATE SET image_url=excluded.image_url
                """, (order_num, page_num, url))
            c.execute("""
                UPDATE issues SET scrape_status='done', total_pages=?, scraped_at=?
                WHERE order_num=?
            """, (len(image_urls), datetime.now().isoformat(), order_num))
            c.commit()

    def mark_scrape_failed(self, order_num, reason="failed"):
        c = self._conn()
        with self._write_lock:
            c.execute(
                "UPDATE issues SET scrape_status=? WHERE order_num=?", (reason, order_num)
            )
            c.commit()

    def mark_page_downloaded(self, issue_order, page_num, file_path, file_size):
        c = self._conn()
        with self._write_lock:
            c.execute("""
                UPDATE pages SET downloaded=1, file_path=?, file_size=?, downloaded_at=?
                WHERE issue_order=? AND page_num=?
            """, (file_path, file_size, datetime.now().isoformat(), issue_order, page_num))
            c.commit()

    def reset_page(self, issue_order, page_num):
        """Mark a page as not downloaded (for re-download)."""
        c = self._conn()
        with self._write_lock:
            c.execute(
                "UPDATE pages SET downloaded=0, file_size=0 WHERE issue_order=? AND page_num=?",
                (issue_order, page_num),
            )
            c.commit()

    def reset_issue_scrape(self, order_num):
        """Reset an issue so it will be re-scraped."""
        c = self._conn()
        with self._write_lock:
            c.execute("DELETE FROM pages WHERE issue_order=?", (order_num,))
            c.execute(
                "UPDATE issues SET scrape_status='pending', total_pages=0, scraped_at=NULL WHERE order_num=?",
                (order_num,),
            )
            c.commit()

    # ── Status ──────────────────────────────────────────────
    def get_status(self, filters=None):
        c = self._conn()
        base_filter = ""
        params = []
        if filters:
            if filters.get("series"):
                base_filter += " AND LOWER(title) LIKE ?"
                params.append(f"%{filters['series'].lower()}%")
            if filters.get("phase"):
                base_filter += " AND LOWER(phase) LIKE ?"
                params.append(f"%{filters['phase'].lower()}%")
            if filters.get("from_bookmark"):
                base_filter += " AND order_num >= (SELECT MIN(order_num) FROM issues WHERE bookmark=1)"

        total = c.execute(f"SELECT COUNT(*) FROM issues WHERE 1=1 {base_filter}", params).fetchone()[0]
        scraped = c.execute(f"SELECT COUNT(*) FROM issues WHERE scrape_status='done' {base_filter}", params).fetchone()[0]
        failed = c.execute(f"SELECT COUNT(*) FROM issues WHERE scrape_status='failed' {base_filter}", params).fetchone()[0]
        captcha = c.execute(f"SELECT COUNT(*) FROM issues WHERE scrape_status='captcha' {base_filter}", params).fetchone()[0]
        unavailable = c.execute(f"SELECT COUNT(*) FROM issues WHERE scrape_status='unavailable' {base_filter}", params).fetchone()[0]

        total_pages = c.execute(
            f"SELECT COUNT(*) FROM pages p JOIN issues i ON i.order_num=p.issue_order WHERE 1=1 {base_filter.replace('title','i.title').replace('phase','i.phase').replace('order_num','i.order_num')}",
            params,
        ).fetchone()[0]
        downloaded_pages = c.execute(
            f"SELECT COUNT(*) FROM pages p JOIN issues i ON i.order_num=p.issue_order WHERE p.downloaded=1 {base_filter.replace('title','i.title').replace('phase','i.phase').replace('order_num','i.order_num')}",
            params,
        ).fetchone()[0]

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
        }

    def get_detail_status(self, filters=None):
        """Per-issue detail."""
        q = """SELECT i.order_num, i.title, i.issue, i.phase, i.scrape_status, i.total_pages,
                      COUNT(CASE WHEN p.downloaded=1 THEN 1 END) as done_pages,
                      COUNT(p.page_num) as url_pages
               FROM issues i
               LEFT JOIN pages p ON p.issue_order = i.order_num
               WHERE 1=1"""
        params = []
        q, params = self._apply_filters(q, params, filters)
        q += " GROUP BY i.order_num ORDER BY i.order_num"
        return self._conn().execute(q, params).fetchall()

    def close(self):
        if hasattr(self._local, "conn"):
            self._local.conn.close()


# ════════════════════════════════════════════════════════════
#  BROWSER / SCRAPING
# ════════════════════════════════════════════════════════════
def _create_browser(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,900")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    _register_driver(driver)
    return driver


JS_GET_VISIBLE_IMAGE = """
    var imgs = document.querySelectorAll('#divImage img');
    for (var i = 0; i < imgs.length; i++) {
        if (imgs[i].style.display !== 'none') {
            var src = imgs[i].src || '';
            if (src && src.indexOf('blogspot') !== -1 && src.length > 50) {
                if (imgs[i].complete && imgs[i].naturalWidth > 100)
                    return src;
                return '__loading__:' + src;
            }
        }
    }
    return null;
"""

JS_GET_FALLBACK = """
    var imgs = document.querySelectorAll('#divImage img');
    for (var i = 0; i < imgs.length; i++) {
        if (imgs[i].style.display !== 'none') {
            var src = imgs[i].src || '';
            if (src && src.indexOf('blogspot') !== -1 && src.length > 50)
                return src;
        }
    }
    return null;
"""


def _extract_all_image_urls(url, headless=True):
    """Open ONE browser, navigate all pages, extract image URLs.
    Returns dict {page_number: image_url} or empty dict on failure.
    """
    driver = None
    try:
        driver = _create_browser(headless)
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "divImage"))
        )
        time.sleep(2)

        if "are you human" in driver.page_source.lower():
            log.warning("  [!!] CAPTCHA detectado")
            return {"__captcha__": True}

        # Page count
        try:
            select_el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "selectPage"))
            )
            total_pages = len(Select(select_el).options)
        except Exception:
            total_pages = 0
            for sel_el in driver.find_elements(By.TAG_NAME, "select"):
                try:
                    opts = [o.text.strip() for o in Select(sel_el).options]
                    if len(opts) > 5 and all(o.isdigit() for o in opts):
                        total_pages = len(opts)
                        break
                except Exception:
                    continue

        if total_pages == 0:
            log.warning("  [!!] Nao encontrou seletor de paginas")
            return {}

        log.info(f"  [OK] {total_pages} paginas detectadas")

        def wait_for_image(prev_src, timeout_s=30):
            for _ in range(timeout_s * 2):
                result = driver.execute_script(JS_GET_VISIBLE_IMAGE)
                if result and result.startswith("__loading__:"):
                    new_src = result[len("__loading__:"):]
                    if new_src != prev_src:
                        time.sleep(0.5)
                        continue
                elif result and result != prev_src:
                    return result.strip()
                time.sleep(0.5)
            fallback = driver.execute_script(JS_GET_FALLBACK)
            if fallback and fallback != prev_src:
                return fallback.strip()
            return None

        image_urls = {}

        # Page 1
        src = wait_for_image("", timeout_s=20)
        if src:
            image_urls[1] = src

        # Remaining pages
        for page_num in range(2, total_pages + 1):
            prev_src = image_urls.get(page_num - 1, "")
            try:
                select_el = driver.find_element(By.ID, "selectPage")
                Select(select_el).select_by_index(page_num - 1)
            except Exception as e:
                log.warning(f"    Pagina {page_num}: erro ao navegar: {e}")
                continue

            src = wait_for_image(prev_src, timeout_s=30)
            if src:
                image_urls[page_num] = src
            else:
                log.warning(f"    Pagina {page_num}: imagem nao encontrada")

            if page_num % 10 == 0:
                log.info(f"    ... {page_num}/{total_pages}")

        log.info(f"  [OK] {len(image_urls)}/{total_pages} URLs coletadas")
        return image_urls

    except Exception as e:
        log.error(f"  [ERRO] Extracao falhou: {e}")
        return {}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            _unregister_driver(driver)


# ════════════════════════════════════════════════════════════
#  PARALLEL SCRAPER  (Phase 1)
# ════════════════════════════════════════════════════════════
class ParallelScraper:
    def __init__(self, db, num_workers=3, headless=True):
        if not HAS_SELENIUM:
            raise RuntimeError("Selenium nao instalado. Execute: pip install selenium")
        self.db = db
        self.num_workers = num_workers
        self.headless = headless
        self._stats = {"ok": 0, "fail": 0, "captcha": 0}
        self._lock = threading.Lock()

    def scrape_all(self, filters=None):
        issues = self.db.get_issues_to_scrape(filters)
        if not issues:
            log.info("Scrape: nada pendente")
            return self._stats

        log.info(f"Scrape: {len(issues)} issues pendentes, {self.num_workers} workers")

        with ThreadPoolExecutor(max_workers=self.num_workers) as pool:
            futures = {}
            for iss in issues:
                f = pool.submit(self._scrape_one, iss)
                futures[f] = iss

            for f in as_completed(futures):
                iss = futures[f]
                try:
                    f.result()
                except Exception as e:
                    log.error(f"  Worker exception [{iss['title']} #{iss['issue']}]: {e}")
                    with self._lock:
                        self._stats["fail"] += 1

        log.info(
            f"Scrape finalizado: {self._stats['ok']} ok, "
            f"{self._stats['fail']} falhas, {self._stats['captcha']} captchas"
        )
        return self._stats

    def _scrape_one(self, issue_row, max_retries=3):
        order = issue_row["order_num"]
        title = issue_row["title"]
        iss_num = issue_row["issue"]
        url = issue_row["url"]

        for attempt in range(1, max_retries + 1):
            label = f"  [SCRAPE #{order}] {title} #{iss_num}"
            if attempt > 1:
                label += f" (tentativa {attempt}/{max_retries})"
            log.info(label)

            urls = _extract_all_image_urls(url, self.headless)

            if urls.get("__captcha__"):
                self.db.mark_scrape_failed(order, "captcha")
                with self._lock:
                    self._stats["captcha"] += 1
                return

            if urls:
                self.db.save_scraped_urls(order, urls)
                with self._lock:
                    self._stats["ok"] += 1
                time.sleep(DELAY_BETWEEN_ISSUES)
                return

            # Empty result — transient browser crash, retry
            if attempt < max_retries:
                wait =  0
                log.warning(f"  [RETRY #{order}] falhou, tentando novamente em {wait}s...")
                time.sleep(wait)

        # All retries exhausted
        self.db.mark_scrape_failed(order, "failed")
        with self._lock:
            self._stats["fail"] += 1


# ════════════════════════════════════════════════════════════
#  PARALLEL DOWNLOADER  (Phase 2)
# ════════════════════════════════════════════════════════════
class ParallelDownloader:
    def __init__(self, db, num_workers=100, output_dir=OUTPUT_DIR):
        if not HAS_REQUESTS:
            raise RuntimeError("Requests nao instalado. Execute: pip install requests")
        self.db = db
        self.num_workers = num_workers
        self.output_dir = output_dir
        self._session_local = threading.local()
        self._stats = {"ok": 0, "fail": 0, "skip": 0}
        self._lock = threading.Lock()

    def _get_session(self):
        if not hasattr(self._session_local, "s"):
            s = requests.Session()
            s.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                "Referer": "https://readcomiconline.li/",
                "Accept-Language": "en-US,en;q=0.9",
                "Sec-Fetch-Dest": "image",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "cross-site",
            })
            self._session_local.s = s
        return self._session_local.s

    def download_all(self, filters=None):
        pages = self.db.get_all_pending_pages(filters)
        if not pages:
            log.info("Download: nada pendente")
            return self._stats

        # Group by issue for logging
        by_issue = {}
        for p in pages:
            by_issue.setdefault(p["issue_order"], []).append(p)

        total_pages = len(pages)
        log.info(
            f"Download: {total_pages} paginas pendentes em "
            f"{len(by_issue)} issues, {self.num_workers} workers"
        )

        # Build tasks: (issue_order, page_num, image_url, file_path)
        tasks = []
        for p in pages:
            issue_row = self.db._conn().execute(
                "SELECT title, issue FROM issues WHERE order_num=?", (p["issue_order"],)
            ).fetchone()
            if not issue_row:
                continue
            s_title = safe_title(issue_row["title"])
            issue_dir = os.path.join(self.output_dir, s_title, f"Issue_{issue_row['issue']:03d}")
            os.makedirs(issue_dir, exist_ok=True)

            ext = ".jpg"
            url_lower = p["image_url"].lower()
            if ".png" in url_lower:
                ext = ".png"
            elif ".webp" in url_lower:
                ext = ".webp"
            file_path = os.path.join(issue_dir, f"page_{p['page_num']:03d}{ext}")

            # Skip if file already on disk
            if os.path.exists(file_path) and os.path.getsize(file_path) > MIN_IMAGE_SIZE:
                self.db.mark_page_downloaded(
                    p["issue_order"], p["page_num"], file_path, os.path.getsize(file_path)
                )
                with self._lock:
                    self._stats["skip"] += 1
                continue

            tasks.append((p["issue_order"], p["page_num"], p["image_url"], file_path))

        if not tasks:
            log.info("Download: todos os arquivos ja existem no disco")
            return self._stats

        log.info(f"Download: {len(tasks)} imagens para baixar")
        done_count = 0

        with ThreadPoolExecutor(max_workers=self.num_workers) as pool:
            futures = {pool.submit(self._download_one, t): t for t in tasks}
            for f in as_completed(futures):
                t = futures[f]
                try:
                    ok = f.result()
                    done_count += 1
                    if done_count % 50 == 0:
                        log.info(f"  ... {done_count}/{len(tasks)} baixadas")
                except Exception as e:
                    log.error(f"  Download exception: {e}")
                    with self._lock:
                        self._stats["fail"] += 1

        log.info(
            f"Download finalizado: {self._stats['ok']} ok, "
            f"{self._stats['fail']} falhas, {self._stats['skip']} ja existiam"
        )
        return self._stats

    def _download_one(self, task):
        issue_order, page_num, image_url, file_path = task
        try:
            s = self._get_session()
            resp = s.get(image_url, timeout=30)
            if resp.status_code == 200 and len(resp.content) > MIN_IMAGE_SIZE:
                with open(file_path, "wb") as f:
                    f.write(resp.content)
                self.db.mark_page_downloaded(issue_order, page_num, file_path, len(resp.content))
                with self._lock:
                    self._stats["ok"] += 1
                return True
            else:
                log.warning(
                    f"    Pagina {page_num} (issue #{issue_order}): "
                    f"status={resp.status_code}, size={len(resp.content)}"
                )
                with self._lock:
                    self._stats["fail"] += 1
                return False
        except Exception as e:
            log.error(f"    Pagina {page_num} (issue #{issue_order}): {e}")
            with self._lock:
                self._stats["fail"] += 1
            return False


# ════════════════════════════════════════════════════════════
#  VERIFIER
# ════════════════════════════════════════════════════════════
class DownloadVerifier:
    def __init__(self, db, output_dir=OUTPUT_DIR):
        self.db = db
        self.output_dir = output_dir

    def verify(self, fix=False):
        """Check every page marked as downloaded. Returns list of problems."""
        c = self.db._conn()
        pages = c.execute(
            "SELECT p.*, i.title, i.issue FROM pages p JOIN issues i ON i.order_num=p.issue_order WHERE p.downloaded=1"
        ).fetchall()

        problems = []
        for p in pages:
            fpath = p["file_path"]
            issue_order = p["issue_order"]
            page_num = p["page_num"]

            if not fpath or not os.path.exists(fpath):
                problems.append({
                    "type": "missing",
                    "issue_order": issue_order,
                    "page_num": page_num,
                    "title": p["title"],
                    "issue": p["issue"],
                    "expected_path": fpath,
                })
            elif os.path.getsize(fpath) < MIN_IMAGE_SIZE:
                problems.append({
                    "type": "corrupt",
                    "issue_order": issue_order,
                    "page_num": page_num,
                    "title": p["title"],
                    "issue": p["issue"],
                    "file_size": os.path.getsize(fpath),
                    "path": fpath,
                })

        # Also check issues where page count doesn't match
        issues = c.execute(
            "SELECT * FROM issues WHERE scrape_status='done' AND total_pages > 0"
        ).fetchall()
        for iss in issues:
            url_count = c.execute(
                "SELECT COUNT(*) FROM pages WHERE issue_order=?", (iss["order_num"],)
            ).fetchone()[0]
            if url_count < iss["total_pages"]:
                problems.append({
                    "type": "incomplete_scrape",
                    "issue_order": iss["order_num"],
                    "title": iss["title"],
                    "issue": iss["issue"],
                    "expected_pages": iss["total_pages"],
                    "scraped_pages": url_count,
                })

        if not problems:
            log.info("Verificacao: tudo OK!")
            return problems

        # Report
        missing = [p for p in problems if p["type"] == "missing"]
        corrupt = [p for p in problems if p["type"] == "corrupt"]
        incomplete = [p for p in problems if p["type"] == "incomplete_scrape"]

        log.warning(
            f"Verificacao: {len(problems)} problemas encontrados "
            f"({len(missing)} faltando, {len(corrupt)} corrompidas, {len(incomplete)} scrapes incompletos)"
        )

        for prob in problems[:20]:  # Show first 20
            if prob["type"] == "missing":
                log.warning(f"  FALTANDO: {prob['title']} #{prob['issue']} pag {prob['page_num']}")
            elif prob["type"] == "corrupt":
                log.warning(
                    f"  CORROMPIDA: {prob['title']} #{prob['issue']} pag {prob['page_num']} "
                    f"({prob['file_size']}B)"
                )
            elif prob["type"] == "incomplete_scrape":
                log.warning(
                    f"  SCRAPE INCOMPLETO: {prob['title']} #{prob['issue']} "
                    f"({prob['scraped_pages']}/{prob['expected_pages']} pags)"
                )

        if len(problems) > 20:
            log.warning(f"  ... e mais {len(problems) - 20} problemas")

        # Fix
        if fix:
            fixed = 0
            for prob in problems:
                if prob["type"] in ("missing", "corrupt"):
                    self.db.reset_page(prob["issue_order"], prob["page_num"])
                    if prob["type"] == "corrupt" and "path" in prob:
                        try:
                            os.remove(prob["path"])
                        except OSError:
                            pass
                    fixed += 1
                elif prob["type"] == "incomplete_scrape":
                    self.db.reset_issue_scrape(prob["issue_order"])
                    fixed += 1
            log.info(f"Fix: {fixed} itens resetados para re-download/re-scrape")
            log.info("Execute 'scrape' e depois 'download' para corrigir")

        return problems


# ════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════
def _build_filters(args):
    filters = {}
    if getattr(args, "series", None):
        filters["series"] = args.series
    if getattr(args, "phase", None):
        filters["phase"] = args.phase
    if getattr(args, "from_bookmark", False):
        filters["from_bookmark"] = True
    if getattr(args, "order", None):
        parts = args.order.split("-")
        if len(parts) == 2:
            filters["order_min"] = int(parts[0])
            filters["order_max"] = int(parts[1])
        else:
            filters["order_min"] = int(parts[0])
            filters["order_max"] = int(parts[0])
    return filters or None


def _load_reading_order():
    json_path = PROJECT_ROOT / "data" / "reading_order.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_scrape(args):
    data = _load_reading_order()
    db = ComicDB(args.db)
    db.populate_issues(data["issues"])
    db.migrate_old_progress(output_dir=args.output)

    filters = _build_filters(args)
    headless = not args.no_headless

    scraper = ParallelScraper(db, num_workers=args.workers, headless=headless)
    scraper.scrape_all(filters)
    db.close()


def cmd_download(args):
    data = _load_reading_order()
    db = ComicDB(args.db)
    db.populate_issues(data["issues"])
    db.migrate_old_progress(output_dir=args.output)

    filters = _build_filters(args)
    dl = ParallelDownloader(db, num_workers=args.workers, output_dir=args.output)
    dl.download_all(filters)
    db.close()


def cmd_run(args):
    data = _load_reading_order()
    db = ComicDB(args.db)
    db.populate_issues(data["issues"])
    db.migrate_old_progress(output_dir=args.output)

    filters = _build_filters(args)
    headless = not args.no_headless

    log.info("=" * 60)
    log.info("FASE 1: Scraping URLs")
    log.info("=" * 60)
    scraper = ParallelScraper(db, num_workers=args.scrape_workers, headless=headless)
    scraper.scrape_all(filters)

    log.info("")
    log.info("=" * 60)
    log.info("FASE 2: Downloading Images")
    log.info("=" * 60)
    dl = ParallelDownloader(db, num_workers=args.download_workers, output_dir=args.output)
    dl.download_all(filters)

    db.close()


def cmd_verify(args):
    db = ComicDB(args.db)
    v = DownloadVerifier(db, output_dir=args.output)
    v.verify(fix=args.fix)
    db.close()


def cmd_status(args):
    data = _load_reading_order()
    db = ComicDB(args.db)
    db.populate_issues(data["issues"])

    filters = _build_filters(args)
    st = db.get_status(filters)

    print()
    print("=" * 55)
    print("  X-MEN COMIC DOWNLOADER — STATUS")
    print("=" * 55)
    print(f"  Issues totais:       {st['total_issues']}")
    print(f"  URLs coletadas:      {st['scraped']} issues")
    print(f"  Scrape pendente:     {st['scrape_pending']} issues")
    if st["scrape_failed"]:
        print(f"  Scrape falhou:       {st['scrape_failed']} issues")
    if st["scrape_captcha"]:
        print(f"  Captcha:             {st['scrape_captcha']} issues")
    if st["scrape_unavailable"]:
        print(f"  Indisponiveis:       {st['scrape_unavailable']} issues")
    print(f"  ─────────────────────────────────")
    print(f"  Paginas no banco:    {st['total_pages']}")
    print(f"  Paginas baixadas:    {st['downloaded_pages']}")
    print(f"  Paginas pendentes:   {st['pending_pages']}")
    if st["total_pages"] > 0:
        pct = st["downloaded_pages"] / st["total_pages"] * 100
        bar_len = 30
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"  Progresso:           [{bar}] {pct:.1f}%")
    print("=" * 55)

    if getattr(args, "detail", False):
        print()
        rows = db.get_detail_status(filters)
        for r in rows:
            status_icon = {"pending": "⏳", "done": "✅", "failed": "❌", "captcha": "🔒", "unavailable": "⛔"}.get(
                r["scrape_status"], "?"
            )
            dl_info = ""
            if r["url_pages"] > 0:
                dl_info = f" | {r['done_pages']}/{r['url_pages']} pags"
            print(
                f"  #{r['order_num']:>3} {status_icon} {r['title']} #{r['issue']}"
                f" [{r['phase']}]{dl_info}"
            )

    db.close()


def cmd_list_phases(args):
    data = _load_reading_order()
    phases = {}
    for iss in data["issues"]:
        p = iss["phase"]
        phases[p] = phases.get(p, 0) + 1
    print("\nFases disponíveis:")
    for p, c in phases.items():
        print(f"  • {p} ({c} edições)")


def cmd_list_series(args):
    data = _load_reading_order()
    series = {}
    for iss in data["issues"]:
        t = iss["title"]
        series[t] = series.get(t, 0) + 1
    print(f"\nSéries disponíveis ({len(series)}):")
    for s in sorted(series):
        print(f"  • {s} ({series[s]} edições)")


def cmd_rescrape(args):
    """Reset specific issues for re-scraping (URLs may have expired)."""
    db = ComicDB(args.db)
    if args.all_failed:
        c = db._conn()
        rows = c.execute("SELECT order_num FROM issues WHERE scrape_status IN ('failed','captcha')").fetchall()
        for r in rows:
            db.reset_issue_scrape(r["order_num"])
        log.info(f"Reset {len(rows)} issues com falha/captcha para re-scrape")
    elif args.order:
        parts = args.order.split("-")
        if len(parts) == 2:
            for o in range(int(parts[0]), int(parts[1]) + 1):
                db.reset_issue_scrape(o)
            log.info(f"Reset issues {parts[0]}-{parts[1]} para re-scrape")
        else:
            db.reset_issue_scrape(int(parts[0]))
            log.info(f"Reset issue #{parts[0]} para re-scrape")
    else:
        log.warning("Especifique --all-failed ou --order N ou --order N-M")
    db.close()


def main():
    parser = argparse.ArgumentParser(
        description="X-Men Comic Downloader v2 — Parallel & Persistent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--db", default=DB_FILE, help="Caminho do banco SQLite")
    parser.add_argument("--output", default=OUTPUT_DIR, help="Diretório de saída")

    sub = parser.add_subparsers(dest="command", help="Comando")

    # ── scrape ──
    p_scrape = sub.add_parser("scrape", help="Fase 1: coletar URLs com browsers paralelos")
    p_scrape.add_argument("--workers", type=int, default=3, help="Browsers paralelos (default: 3)")
    p_scrape.add_argument("--no-headless", action="store_true", help="Mostrar janela do browser")
    p_scrape.add_argument("--series", type=str)
    p_scrape.add_argument("--phase", type=str)
    p_scrape.add_argument("--from-bookmark", action="store_true")
    p_scrape.add_argument("--order", type=str, help="Ordem: N ou N-M")

    # ── download ──
    p_dl = sub.add_parser("download", help="Fase 2: baixar imagens das URLs salvas")
    p_dl.add_argument("--workers", type=int, default=100, help="Downloads paralelos (default: 100)")
    p_dl.add_argument("--series", type=str)
    p_dl.add_argument("--phase", type=str)
    p_dl.add_argument("--from-bookmark", action="store_true")
    p_dl.add_argument("--order", type=str, help="Ordem: N ou N-M")

    # ── run (scrape + download) ──
    p_run = sub.add_parser("run", help="Scrape + Download em sequência")
    p_run.add_argument("--scrape-workers", type=int, default=3, help="Browsers paralelos (default: 3)")
    p_run.add_argument("--download-workers", type=int, default=20, help="Downloads paralelos (default: 20)")
    p_run.add_argument("--no-headless", action="store_true")
    p_run.add_argument("--series", type=str)
    p_run.add_argument("--phase", type=str)
    p_run.add_argument("--from-bookmark", action="store_true")
    p_run.add_argument("--order", type=str, help="Ordem: N ou N-M")

    # ── verify ──
    p_verify = sub.add_parser("verify", help="Verificar downloads (páginas faltando/corrompidas)")
    p_verify.add_argument("--fix", action="store_true", help="Resetar itens com problema para re-download")

    # ── status ──
    p_status = sub.add_parser("status", help="Mostrar progresso geral")
    p_status.add_argument("--detail", action="store_true", help="Mostrar status por issue")
    p_status.add_argument("--series", type=str)
    p_status.add_argument("--phase", type=str)
    p_status.add_argument("--from-bookmark", action="store_true")
    p_status.add_argument("--order", type=str)

    # ── rescrape ──
    p_rescrape = sub.add_parser("rescrape", help="Resetar issues para re-scrape de URLs")
    p_rescrape.add_argument("--all-failed", action="store_true", help="Reset todas com falha/captcha")
    p_rescrape.add_argument("--order", type=str, help="Ordem: N ou N-M")

    # ── list-phases / list-series ──
    sub.add_parser("list-phases", help="Listar fases disponíveis")
    sub.add_parser("list-series", help="Listar séries disponíveis")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "scrape": cmd_scrape,
        "download": cmd_download,
        "run": cmd_run,
        "verify": cmd_verify,
        "status": cmd_status,
        "list-phases": cmd_list_phases,
        "list-series": cmd_list_series,
        "rescrape": cmd_rescrape,
    }
    try:
        commands[args.command](args)
    except KeyboardInterrupt:
        log.info("\nInterrompido pelo usuario. Progresso salvo no banco.")
    except Exception as e:
        log.error(f"Erro fatal: {e}")
        raise
    finally:
        _cleanup_all_chrome()


if __name__ == "__main__":
    main()
