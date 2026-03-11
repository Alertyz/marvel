"""
Phase 2 — Parallel HTTP image downloader.

KEY FIX: Each download task is a self-contained DownloadTask with all
context (title, issue, target path) precomputed on the main thread.
Worker threads receive immutable tasks — no shared state, no DB lookups
in workers, no chance of saving images to the wrong folder.
"""

import os
import logging
import threading
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import MIN_IMAGE_SIZE, COMICS_DIR, DEFAULT_DOWNLOAD_WORKERS
from .db import ComicDB
from .slugs import safe_title

log = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass(frozen=True)
class DownloadTask:
    """
    Immutable download task — all context is resolved at creation time.
    Workers receive this and only write to the pre-determined file_path.
    This prevents the old bug where parallel downloads mixed up folders.
    """
    issue_order: int
    page_num: int
    image_url: str
    file_path: str       # Absolute path on disk
    series_title: str    # For logging only
    issue_num: int       # For logging only


class ParallelDownloader:
    """
    Phase 2: download images from scraped URLs.

    All file paths are resolved on the main thread BEFORE dispatching
    to workers. Each DownloadTask is frozen — workers cannot modify
    or confuse which folder an image belongs to.
    """

    def __init__(self, db: ComicDB, num_workers: int = DEFAULT_DOWNLOAD_WORKERS,
                 output_dir: str | None = None):
        if not HAS_REQUESTS:
            raise RuntimeError("Requests nao instalado. Execute: pip install requests")
        self.db = db
        self.num_workers = num_workers
        self.output_dir = output_dir or str(COMICS_DIR)
        self._session_local = threading.local()
        self._stats = {"ok": 0, "fail": 0, "skip": 0}
        self._lock = threading.Lock()

    def _get_session(self) -> "requests.Session":
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

    def download_all(self, filters: dict | None = None) -> dict:
        """Build all tasks on the main thread, then dispatch to workers."""
        pages = self.db.get_all_pending_pages(filters)
        if not pages:
            log.info("Download: nada pendente")
            return self._stats

        # ── MAIN THREAD: resolve every task's context before dispatching ──
        tasks = self._build_tasks(pages)

        if not tasks:
            log.info("Download: todos os arquivos ja existem no disco")
            return self._stats

        # Group for logging
        issues_in_batch = {t.issue_order for t in tasks}
        log.info(
            f"Download: {len(tasks)} imagens para baixar "
            f"em {len(issues_in_batch)} issues, {self.num_workers} workers"
        )

        # ── WORKER THREADS: only download + write, no DB queries ──
        done_count = 0
        with ThreadPoolExecutor(max_workers=self.num_workers) as pool:
            futures = {pool.submit(self._download_one, task): task for task in tasks}
            for f in as_completed(futures):
                task = futures[f]
                try:
                    f.result()
                except Exception as e:
                    log.error(
                        f"  Download exception [{task.series_title} #{task.issue_num} "
                        f"p{task.page_num}]: {e}"
                    )
                    with self._lock:
                        self._stats["fail"] += 1
                done_count += 1
                if done_count % 50 == 0:
                    log.info(f"  ... {done_count}/{len(tasks)} processadas")

        log.info(
            f"Download finalizado: {self._stats['ok']} ok, "
            f"{self._stats['fail']} falhas, {self._stats['skip']} ja existiam"
        )
        return self._stats

    def _build_tasks(self, pages: list) -> list[DownloadTask]:
        """
        Build immutable DownloadTask objects on the MAIN THREAD.

        Each task carries:
          - The exact file_path where the image must be saved
          - All identifying info (issue_order, page_num, title, issue)

        This is where the old bug was: if issue context was resolved
        inside worker threads, race conditions mixed up folders.
        Now all paths are frozen before any worker starts.
        """
        tasks: list[DownloadTask] = []
        # Cache issue lookups to avoid repeated queries
        issue_cache: dict[int, dict] = {}

        for p in pages:
            order = p["issue_order"]

            # Resolve issue info (cached, main thread only)
            if order not in issue_cache:
                issue_row = self.db.get_issue(order)
                if not issue_row:
                    log.warning(f"  Issue #{order} nao encontrada no DB, pulando")
                    continue
                issue_cache[order] = {
                    "title": issue_row["title"],
                    "issue": issue_row["issue"],
                }

            info = issue_cache[order]
            s_title = safe_title(info["title"])
            issue_dir = os.path.join(
                self.output_dir, s_title, f"Issue_{info['issue']:03d}"
            )
            os.makedirs(issue_dir, exist_ok=True)

            # Determine extension from URL
            ext = ".jpg"
            url_lower = p["image_url"].lower()
            if ".png" in url_lower:
                ext = ".png"
            elif ".webp" in url_lower:
                ext = ".webp"

            file_path = os.path.join(issue_dir, f"page_{p['page_num']:03d}{ext}")

            # Skip if already on disk and valid
            if os.path.exists(file_path) and os.path.getsize(file_path) > MIN_IMAGE_SIZE:
                self.db.mark_page_downloaded(
                    order, p["page_num"], file_path, os.path.getsize(file_path)
                )
                with self._lock:
                    self._stats["skip"] += 1
                continue

            tasks.append(DownloadTask(
                issue_order=order,
                page_num=p["page_num"],
                image_url=p["image_url"],
                file_path=file_path,
                series_title=info["title"],
                issue_num=info["issue"],
            ))

        return tasks

    def _download_one(self, task: DownloadTask) -> bool:
        """
        Download a single image. All context is in the frozen task.
        This method does NOT query the DB for issue info — that was
        already resolved in _build_tasks on the main thread.
        """
        try:
            s = self._get_session()
            resp = s.get(task.image_url, timeout=30)
            if resp.status_code == 200 and len(resp.content) > MIN_IMAGE_SIZE:
                with open(task.file_path, "wb") as f:
                    f.write(resp.content)
                self.db.mark_page_downloaded(
                    task.issue_order, task.page_num,
                    task.file_path, len(resp.content),
                )
                with self._lock:
                    self._stats["ok"] += 1
                return True
            else:
                log.warning(
                    f"    {task.series_title} #{task.issue_num} p{task.page_num}: "
                    f"status={resp.status_code}, size={len(resp.content)}"
                )
                with self._lock:
                    self._stats["fail"] += 1
                return False
        except Exception as e:
            log.error(
                f"    {task.series_title} #{task.issue_num} p{task.page_num}: {e}"
            )
            with self._lock:
                self._stats["fail"] += 1
            return False
