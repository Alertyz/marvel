"""
Phase 1 — Browser-based URL extraction (Selenium).

Each worker gets its own Chrome instance and scrapes one issue at a time.
Extracted image URLs are saved atomically per-issue to prevent cross-contamination.
"""

import sys
import time
import atexit
import signal
import logging
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import DELAY_BETWEEN_ISSUES, MAX_RETRIES, PAGE_LOAD_TIMEOUT, IMAGE_WAIT_TIMEOUT
from .db import ComicDB

log = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

# ── Chrome lifecycle ────────────────────────────────────────
_active_drivers: list = []
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


def cleanup_chrome():
    """Quit all tracked drivers, then kill any remaining chrome/chromedriver."""
    with _drivers_lock:
        for d in _active_drivers:
            try:
                d.quit()
            except Exception:
                pass
        _active_drivers.clear()
    if sys.platform == "win32":
        for proc_name in ("chromedriver.exe", "chrome.exe"):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", proc_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass


def _setup_signal_handlers():
    def handler(sig, frame):
        log.info("\nInterrompido — fechando browsers...")
        cleanup_chrome()
        sys.exit(1)
    atexit.register(cleanup_chrome)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


# ── Browser factory ─────────────────────────────────────────
def _create_browser(headless: bool = True):
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
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    _register_driver(driver)
    return driver


# ── JavaScript for image extraction ─────────────────────────
# Queries only the FIRST visible image inside #divImage that has a blogspot
# src AND whose natural dimensions indicate it is fully loaded.
# We avoid querySelectorAll + loop-over-all because the site may preload
# images from adjacent issues elsewhere in the DOM.
JS_GET_VISIBLE_IMAGE = """
    var container = document.getElementById('divImage');
    if (!container) return null;
    var imgs = container.querySelectorAll('img');
    for (var i = 0; i < imgs.length; i++) {
        var img = imgs[i];
        var style = window.getComputedStyle(img);
        if (style.display === 'none' || style.visibility === 'hidden') continue;
        if (parseFloat(style.opacity) < 0.1) continue;
        var src = img.src || '';
        if (!src || src.indexOf('blogspot') === -1 || src.length < 50) continue;
        if (img.complete && img.naturalWidth > 50 && img.naturalHeight > 50)
            return src;
        return '__loading__:' + src;
    }
    return null;
"""

JS_GET_FALLBACK = """
    var container = document.getElementById('divImage');
    if (!container) return null;
    var imgs = container.querySelectorAll('img');
    for (var i = 0; i < imgs.length; i++) {
        var img = imgs[i];
        var style = window.getComputedStyle(img);
        if (style.display === 'none' || style.visibility === 'hidden') continue;
        var src = img.src || '';
        if (src && src.indexOf('blogspot') !== -1 && src.length > 50)
            return src;
    }
    return null;
"""


def _extract_all_image_urls(url: str, headless: bool = True) -> dict[int, str]:
    """
    Open one browser, navigate all pages, extract image URLs.
    Returns dict {page_number: image_url} or empty dict on failure.
    Special key "__captcha__" indicates CAPTCHA detection.
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

        # Detect page count
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

        def wait_for_image(page_num: int, prev_src: str,
                           timeout_s: int = IMAGE_WAIT_TIMEOUT) -> str | None:
            """
            Wait until the visible image in #divImage changes from prev_src.

            The comparison against prev_src guards against the browser still
            showing the previous page while the new one loads.  However, some
            comics have genuinely duplicated page images (same URL on two
            consecutive pages).  To avoid waiting forever in that case, we
            track the URL that appears to be loading and accept it once it is
            fully loaded, regardless of whether it equals prev_src.
            """
            loading_src: str | None = None
            for tick in range(timeout_s * 2):
                result = driver.execute_script(JS_GET_VISIBLE_IMAGE)
                if result is None:
                    time.sleep(0.5)
                    continue

                if result.startswith("__loading__:"):
                    candidate = result[len("__loading__:"):]
                    loading_src = candidate
                    time.sleep(0.5)
                    continue

                # result is a fully-loaded src
                if result != prev_src:
                    return result.strip()

                # result == prev_src: could be a duplicate page or a stale image.
                # If we saw this same URL arrive via __loading__ it IS the new page
                # (a genuine duplicate), so accept it.
                if loading_src and loading_src == result:
                    log.debug(
                        f"    Página {page_num}: URL idêntica à anterior "
                        f"(página duplicada no site) — aceita assim mesmo"
                    )
                    return result.strip()

                time.sleep(0.5)

            # Timeout — try the fallback JS (no naturalWidth check)
            fallback = driver.execute_script(JS_GET_FALLBACK)
            if fallback and fallback != prev_src:
                log.warning(
                    f"    Página {page_num}: timeout aguardando imagem, "
                    f"usando fallback src"
                )
                return fallback.strip()
            if fallback and fallback == prev_src and loading_src:
                log.warning(
                    f"    Página {page_num}: timeout — aceitando URL duplicada via fallback"
                )
                return fallback.strip()
            return None

        image_urls: dict[int, str] = {}

        # Page 1
        src = wait_for_image(1, "", timeout_s=20)
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

            src = wait_for_image(page_num, prev_src, timeout_s=IMAGE_WAIT_TIMEOUT)
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
#  PARALLEL SCRAPER
# ════════════════════════════════════════════════════════════
class ParallelScraper:
    """
    Phase 1: scrape image URLs from the comic site using parallel browsers.

    Each issue is handled by a single browser instance. The scraped URLs
    are written to the DB atomically per-issue — no shared state between
    workers that could cause cross-contamination.
    """

    def __init__(self, db: ComicDB, num_workers: int = 3, headless: bool = True):
        if not HAS_SELENIUM:
            raise RuntimeError("Selenium nao instalado. Execute: pip install selenium")
        self.db = db
        self.num_workers = num_workers
        self.headless = headless
        self._stats = {"ok": 0, "fail": 0, "captcha": 0}
        self._lock = threading.Lock()

    def scrape_all(self, filters: dict | None = None) -> dict:
        _setup_signal_handlers()

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

    def _scrape_one(self, issue_row):
        """Scrape a single issue. All state is local to this call."""
        order = issue_row["order_num"]
        title = issue_row["title"]
        iss_num = issue_row["issue"]
        url = issue_row["url"]

        for attempt in range(1, MAX_RETRIES + 1):
            label = f"  [SCRAPE #{order}] {title} #{iss_num}"
            if attempt > 1:
                label += f" (tentativa {attempt}/{MAX_RETRIES})"
            log.info(label)

            urls = _extract_all_image_urls(url, self.headless)

            if urls.get("__captcha__"):
                self.db.mark_scrape_failed(order, "captcha")
                with self._lock:
                    self._stats["captcha"] += 1
                return

            if urls:
                # Atomic save: all URLs for this issue in one transaction
                self.db.save_scraped_urls(order, urls)
                with self._lock:
                    self._stats["ok"] += 1
                time.sleep(DELAY_BETWEEN_ISSUES)
                return

            if attempt < MAX_RETRIES:
                log.warning(f"  [RETRY #{order}] falhou, tentando novamente...")
                time.sleep(2)

        self.db.mark_scrape_failed(order, "failed")
        with self._lock:
            self._stats["fail"] += 1