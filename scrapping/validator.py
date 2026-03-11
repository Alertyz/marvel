"""
Post-download validation.

Checks:
  1. Missing files: pages marked as downloaded but file doesn't exist
  2. Corrupt files: files smaller than MIN_IMAGE_SIZE
  3. Incomplete scrapes: fewer URLs than expected page count
  4. Page count mismatch: files on disk don't match DB total_pages
  5. Orphaned files: files on disk not tracked in DB

Issues are flagged in the validation_flags table (not crashed).
"""

import os
import re
import logging
from pathlib import Path

from .config import MIN_IMAGE_SIZE, COMICS_DIR
from .db import ComicDB
from .slugs import safe_title

log = logging.getLogger(__name__)


class DownloadValidator:
    """Validates downloaded comics against the database and flags problems."""

    def __init__(self, db: ComicDB, output_dir: str | None = None):
        self.db = db
        self.output_dir = output_dir or str(COMICS_DIR)

    def validate(self, fix: bool = False) -> list[dict]:
        """
        Run all validation checks. Returns list of problems found.
        Problems are also saved as flags in the DB.
        If fix=True, resets problematic pages/issues for re-download.
        """
        problems: list[dict] = []

        problems.extend(self._check_downloaded_pages())
        problems.extend(self._check_scrape_completeness())
        problems.extend(self._check_disk_vs_db())

        if not problems:
            log.info("Validacao: tudo OK! Nenhum problema encontrado.")
            return problems

        # Report summary
        by_type: dict[str, int] = {}
        for p in problems:
            by_type[p["type"]] = by_type.get(p["type"], 0) + 1

        log.warning(f"Validacao: {len(problems)} problemas encontrados:")
        for t, c in sorted(by_type.items()):
            log.warning(f"  {t}: {c}")

        # Show first 20 details
        for prob in problems[:20]:
            self._log_problem(prob)
        if len(problems) > 20:
            log.warning(f"  ... e mais {len(problems) - 20} problemas")

        # Fix if requested
        if fix:
            self._fix_problems(problems)

        return problems

    def _check_downloaded_pages(self) -> list[dict]:
        """Check every page marked as downloaded exists and is valid."""
        c = self.db._conn()
        pages = c.execute(
            "SELECT p.*, i.title, i.issue FROM pages p "
            "JOIN issues i ON i.order_num = p.issue_order "
            "WHERE p.downloaded = 1"
        ).fetchall()

        problems = []
        for p in pages:
            fpath = p["file_path"]
            order = p["issue_order"]
            page_num = p["page_num"]

            if not fpath or not os.path.exists(fpath):
                problems.append({
                    "type": "missing_file",
                    "issue_order": order,
                    "page_num": page_num,
                    "title": p["title"],
                    "issue": p["issue"],
                    "expected_path": fpath,
                })
                self.db.set_flag(
                    order, f"missing_page_{page_num}",
                    f"Pagina {page_num} marcada como baixada mas arquivo nao existe: {fpath}",
                )
            elif os.path.getsize(fpath) < MIN_IMAGE_SIZE:
                problems.append({
                    "type": "corrupt_file",
                    "issue_order": order,
                    "page_num": page_num,
                    "title": p["title"],
                    "issue": p["issue"],
                    "file_size": os.path.getsize(fpath),
                    "path": fpath,
                })
                self.db.set_flag(
                    order, f"corrupt_page_{page_num}",
                    f"Pagina {page_num} corrompida ({os.path.getsize(fpath)} bytes)",
                )

        return problems

    def _check_scrape_completeness(self) -> list[dict]:
        """Check issues where scraped URL count < expected total_pages."""
        c = self.db._conn()
        issues = c.execute(
            "SELECT * FROM issues WHERE scrape_status='done' AND total_pages > 0"
        ).fetchall()

        problems = []
        for iss in issues:
            url_count = c.execute(
                "SELECT COUNT(*) FROM pages WHERE issue_order=?",
                (iss["order_num"],),
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
                self.db.set_flag(
                    iss["order_num"], "incomplete_scrape",
                    f"Scrape incompleto: {url_count}/{iss['total_pages']} paginas",
                )

        return problems

    def _check_disk_vs_db(self) -> list[dict]:
        """
        Check that files on disk match what the DB expects.
        Catches:
          - Issues where disk page count != DB total_pages
          - Pages in wrong directories (the old bug)
        """
        c = self.db._conn()
        issues = c.execute(
            "SELECT * FROM issues WHERE scrape_status='done' AND total_pages > 0"
        ).fetchall()

        problems = []
        for iss in issues:
            s_title = safe_title(iss["title"])
            issue_dir = os.path.join(
                self.output_dir, s_title, f"Issue_{iss['issue']:03d}"
            )

            if not os.path.isdir(issue_dir):
                # Directory doesn't exist — skip (it might not be downloaded yet)
                downloaded = c.execute(
                    "SELECT COUNT(*) FROM pages WHERE issue_order=? AND downloaded=1",
                    (iss["order_num"],),
                ).fetchone()[0]
                if downloaded > 0:
                    problems.append({
                        "type": "missing_directory",
                        "issue_order": iss["order_num"],
                        "title": iss["title"],
                        "issue": iss["issue"],
                        "expected_dir": issue_dir,
                        "claimed_downloaded": downloaded,
                    })
                    self.db.set_flag(
                        iss["order_num"], "missing_directory",
                        f"Diretorio nao existe mas {downloaded} paginas marcadas como baixadas",
                    )
                continue

            # Count actual image files on disk
            disk_files = [
                f for f in os.listdir(issue_dir)
                if f.endswith(('.jpg', '.png', '.webp'))
            ]
            disk_count = len(disk_files)
            db_total = iss["total_pages"]

            if disk_count != db_total:
                downloaded_in_db = c.execute(
                    "SELECT COUNT(*) FROM pages WHERE issue_order=? AND downloaded=1",
                    (iss["order_num"],),
                ).fetchone()[0]
                problems.append({
                    "type": "page_count_mismatch",
                    "issue_order": iss["order_num"],
                    "title": iss["title"],
                    "issue": iss["issue"],
                    "disk_pages": disk_count,
                    "db_total_pages": db_total,
                    "db_downloaded": downloaded_in_db,
                })
                self.db.set_flag(
                    iss["order_num"], "page_count_mismatch",
                    f"Disco: {disk_count}, DB total: {db_total}, DB baixadas: {downloaded_in_db}",
                )

        return problems

    def _log_problem(self, prob: dict):
        t = prob["type"]
        title = prob.get("title", "?")
        issue = prob.get("issue", "?")
        prefix = f"  {title} #{issue}"

        if t == "missing_file":
            log.warning(f"{prefix}: FALTANDO pagina {prob['page_num']}")
        elif t == "corrupt_file":
            log.warning(f"{prefix}: CORROMPIDA pagina {prob['page_num']} ({prob['file_size']}B)")
        elif t == "incomplete_scrape":
            log.warning(f"{prefix}: SCRAPE INCOMPLETO ({prob['scraped_pages']}/{prob['expected_pages']})")
        elif t == "missing_directory":
            log.warning(f"{prefix}: DIRETORIO FALTANDO ({prob['claimed_downloaded']} pags marcadas)")
        elif t == "page_count_mismatch":
            log.warning(
                f"{prefix}: CONTAGEM DIFERENTE disco={prob['disk_pages']} "
                f"db_total={prob['db_total_pages']} db_baixadas={prob['db_downloaded']}"
            )

    def _fix_problems(self, problems: list[dict]):
        """Reset problematic pages/issues for re-download."""
        fixed = 0
        # Track which issues were already processed to avoid double resets
        reset_scrape: set[int] = set()
        reset_dl: set[int] = set()

        for prob in problems:
            t = prob["type"]
            order = prob["issue_order"]

            if t in ("missing_file", "corrupt_file"):
                self.db.reset_page(order, prob["page_num"])
                if t == "corrupt_file" and "path" in prob:
                    try:
                        os.remove(prob["path"])
                    except OSError:
                        pass
                fixed += 1

            elif t == "missing_directory":
                # Files were deleted — URLs are still valid, just reset download flags
                if order not in reset_dl and order not in reset_scrape:
                    self.db.reset_issue_downloads(order)
                    reset_dl.add(order)
                    fixed += 1

            elif t == "incomplete_scrape":
                # Scrape was incomplete — must re-scrape to get all URLs
                if order not in reset_scrape:
                    self.db.reset_issue_scrape(order)
                    reset_scrape.add(order)
                    reset_dl.discard(order)
                    fixed += 1

        log.info(f"Fix: {fixed} itens resetados para re-download/re-scrape")
        if reset_scrape:
            log.info(f"  {len(reset_scrape)} issues precisam de re-scrape → execute 'scrape'")
        if reset_dl:
            log.info(f"  {len(reset_dl)} issues prontas para re-download → execute 'download'")
