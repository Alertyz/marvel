"""
Phase 1 — Browser-based URL extraction (Selenium).

FIXES vs original:
  • Hard per-issue timeout  → travado nunca bloqueia para sempre
  • _stop_event global       → Ctrl+C encerra workers imediatamente
  • Cleanup por PID          → Chrome nunca fica aberto após saída
  • Abort on consecutive fails → capítulos ruins são pulados rápido
"""

import os
import sys
import time
import atexit
import signal
import logging
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, wait as futures_wait, FIRST_COMPLETED

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

# ── Configurações de timeout ────────────────────────────────
# Tempo máximo total por issue (segundos). Ajuste conforme a quantidade
# de páginas esperada. Issues que ultrapassarem isso são marcadas como falha.
ISSUE_HARD_TIMEOUT = int(os.environ.get("ISSUE_HARD_TIMEOUT", 300))  # 5 min default

# Quantas páginas consecutivas sem imagem antes de abortar o issue
MAX_CONSECUTIVE_FAILS = int(os.environ.get("MAX_CONSECUTIVE_FAILS", 5))

# ── Estado global de parada ─────────────────────────────────
_stop_event = threading.Event()

# ── Chrome lifecycle (track por PID) ────────────────────────
_driver_pids: dict[int, object] = {}   # {browser_pid: driver}
_drivers_lock = threading.Lock()


def _register_driver(driver):
    try:
        pid = driver.service.process.pid
        with _drivers_lock:
            _driver_pids[pid] = driver
    except Exception:
        pass


def _unregister_driver(driver):
    try:
        pid = driver.service.process.pid
        with _drivers_lock:
            _driver_pids.pop(pid, None)
    except Exception:
        pass


def _quit_driver_safe(driver):
    """Quit driver; se travar, mata o processo pelo PID."""
    pid = None
    try:
        pid = driver.service.process.pid
    except Exception:
        pass

    try:
        driver.quit()
    except Exception:
        pass

    # Garante que o chromedriver filho morreu
    if pid:
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                os.kill(pid, signal.SIGKILL)
        except Exception:
            pass

    _unregister_driver(driver)


def cleanup_chrome():
    """Mata todos os drivers rastreados + qualquer chrome/chromedriver residual."""
    with _drivers_lock:
        drivers = list(_driver_pids.values())
        _driver_pids.clear()

    for d in drivers:
        try:
            d.quit()
        except Exception:
            pass

    # Força kill por nome de processo como fallback
    if sys.platform == "win32":
        for proc_name in ("chromedriver.exe", "chrome.exe"):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", proc_name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass
    else:
        for proc_name in ("chromedriver", "chromium", "google-chrome"):
            try:
                subprocess.run(
                    ["pkill", "-9", "-f", proc_name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass


def _setup_signal_handlers():
    def handler(sig, frame):
        if _stop_event.is_set():
            # Segunda vez: força saída imediata
            log.warning("\nForçando saída imediata...")
            cleanup_chrome()
            os._exit(1)

        log.info("\n[Ctrl+C] Sinalizando parada — aguarde workers terminarem...")
        _stop_event.set()

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


# ── JavaScript para extração de imagem ──────────────────────
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
    Abre um browser, navega todas as páginas, extrai URLs das imagens.
    Retorna dict {page_number: image_url} ou vazio em caso de falha.
    Chave especial "__captcha__" indica detecção de CAPTCHA.
    Respeita _stop_event para encerramento limpo.
    """
    driver = None
    try:
        driver = _create_browser(headless)
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "divImage"))
        )

        if _stop_event.is_set():
            return {}

        time.sleep(2)

        if "are you human" in driver.page_source.lower():
            log.warning("  [!!] CAPTCHA detectado")
            return {"__captcha__": True}

        # Detecta contagem de páginas
        total_pages = 0
        try:
            select_el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "selectPage"))
            )
            total_pages = len(Select(select_el).options)
        except Exception:
            for sel_el in driver.find_elements(By.TAG_NAME, "select"):
                try:
                    opts = [o.text.strip() for o in Select(sel_el).options]
                    if len(opts) > 5 and all(o.isdigit() for o in opts):
                        total_pages = len(opts)
                        break
                except Exception:
                    continue

        if total_pages == 0:
            log.warning("  [!!] Não encontrou seletor de páginas")
            return {}

        log.info(f"  [OK] {total_pages} páginas detectadas")

        def wait_for_image(page_num: int, prev_src: str,
                           timeout_s: int = IMAGE_WAIT_TIMEOUT) -> str | None:
            """
            Aguarda até a imagem visível em #divImage mudar de prev_src.
            Retorna None se timeout ou _stop_event ativado.
            """
            loading_src: str | None = None
            deadline = time.monotonic() + timeout_s

            while time.monotonic() < deadline:
                # ── Respeita Ctrl+C ──────────────────────────
                if _stop_event.is_set():
                    return None

                try:
                    result = driver.execute_script(JS_GET_VISIBLE_IMAGE)
                except Exception:
                    return None  # browser morreu

                if result is None:
                    time.sleep(0.5)
                    continue

                if result.startswith("__loading__:"):
                    loading_src = result[len("__loading__:"):]
                    time.sleep(0.5)
                    continue

                if result != prev_src:
                    return result.strip()

                if loading_src and loading_src == result:
                    log.debug(
                        f"    Página {page_num}: URL idêntica à anterior "
                        f"(página duplicada no site) — aceita assim mesmo"
                    )
                    return result.strip()

                time.sleep(0.5)

            # Timeout — tenta fallback JS (sem checagem de naturalWidth)
            try:
                fallback = driver.execute_script(JS_GET_FALLBACK)
            except Exception:
                return None

            if fallback and fallback != prev_src:
                log.warning(f"    Página {page_num}: timeout, usando fallback src")
                return fallback.strip()
            if fallback and fallback == prev_src and loading_src:
                log.warning(f"    Página {page_num}: timeout — aceitando URL duplicada via fallback")
                return fallback.strip()
            return None

        image_urls: dict[int, str] = {}
        consecutive_fails = 0

        # Página 1
        src = wait_for_image(1, "", timeout_s=20)
        if src:
            image_urls[1] = src
            consecutive_fails = 0
        else:
            consecutive_fails = 1

        # Páginas restantes
        for page_num in range(2, total_pages + 1):
            if _stop_event.is_set():
                break

            # ── Abort rápido se muitas páginas consecutivas falharam ──
            if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                log.warning(
                    f"  [ABORT] {consecutive_fails} páginas consecutivas sem imagem "
                    f"(página {page_num}/{total_pages}) — pulando issue"
                )
                break

            prev_src = image_urls.get(page_num - 1, "")
            try:
                select_el = driver.find_element(By.ID, "selectPage")
                Select(select_el).select_by_index(page_num - 1)
            except Exception as e:
                log.warning(f"    Página {page_num}: erro ao navegar: {e}")
                consecutive_fails += 1
                continue

            src = wait_for_image(page_num, prev_src, timeout_s=IMAGE_WAIT_TIMEOUT)
            if src:
                image_urls[page_num] = src
                consecutive_fails = 0
            else:
                log.warning(f"    Página {page_num}: imagem não encontrada ({consecutive_fails + 1}/{MAX_CONSECUTIVE_FAILS})")
                consecutive_fails += 1

            if page_num % 10 == 0:
                log.info(f"    ... {page_num}/{total_pages}")

        log.info(f"  [OK] {len(image_urls)}/{total_pages} URLs coletadas")
        return image_urls

    except Exception as e:
        log.error(f"  [ERRO] Extração falhou: {e}")
        return {}
    finally:
        if driver:
            _quit_driver_safe(driver)   # ← garante fechamento mesmo em crash


# ════════════════════════════════════════════════════════════
#  PARALLEL SCRAPER
# ════════════════════════════════════════════════════════════
class ParallelScraper:
    """
    Phase 1: scrape image URLs from the comic site using parallel browsers.

    Cada issue é tratada por um único browser. Os URLs são gravados
    no DB atomicamente por issue — sem estado compartilhado entre workers.
    """

    def __init__(self, db: ComicDB, num_workers: int = 3, headless: bool = True):
        if not HAS_SELENIUM:
            raise RuntimeError("Selenium não instalado. Execute: pip install selenium")
        self.db = db
        self.num_workers = num_workers
        self.headless = headless
        self._stats = {"ok": 0, "fail": 0, "captcha": 0, "aborted": 0}
        self._lock = threading.Lock()

    def scrape_all(self, filters: dict | None = None) -> dict:
        _setup_signal_handlers()
        _stop_event.clear()

        issues = self.db.get_issues_to_scrape(filters)
        if not issues:
            log.info("Scrape: nada pendente")
            return self._stats

        log.info(
            f"Scrape: {len(issues)} issues pendentes, "
            f"{self.num_workers} workers, "
            f"timeout por issue: {ISSUE_HARD_TIMEOUT}s"
        )

        with ThreadPoolExecutor(
            max_workers=self.num_workers,
            thread_name_prefix="scraper",
        ) as pool:
            futures = {pool.submit(self._scrape_one, iss): iss for iss in issues}

            try:
                for f in as_completed(futures):
                    if _stop_event.is_set():
                        # Cancela os futuros ainda pendentes
                        for pending in futures:
                            pending.cancel()
                        break

                    iss = futures[f]
                    try:
                        f.result()
                    except Exception as e:
                        log.error(
                            f"  Worker exception [{iss['title']} "
                            f"#{iss['issue']}]: {e}"
                        )
                        with self._lock:
                            self._stats["fail"] += 1

            except KeyboardInterrupt:
                log.info("\n[Ctrl+C] Aguardando workers encerrarem...")
                _stop_event.set()

        cleanup_chrome()   # garantia final — mata qualquer chrome restante

        log.info(
            f"Scrape finalizado: {self._stats['ok']} ok, "
            f"{self._stats['fail']} falhas, "
            f"{self._stats['captcha']} captchas, "
            f"{self._stats['aborted']} abortados"
        )
        return self._stats

    def _scrape_one(self, issue_row):
        """
        Scrape de um único issue com hard timeout.
        Se ultrapassar ISSUE_HARD_TIMEOUT, marca falha e retorna.
        """
        if _stop_event.is_set():
            return

        order   = issue_row["order_num"]
        title   = issue_row["title"]
        iss_num = issue_row["issue"]
        url     = issue_row["url"]

        print(f"\n{'─'*50}")
        print(f"  ISSUE   : {title} #{iss_num}")
        print(f"  URL     : {url}")
        print(f"{'─'*50}")

        # ── Hard timeout via thread auxiliar ────────────────
        # Usamos um Event interno para coordenar com o timer.
        _done = threading.Event()

        def _timeout_bomb():
            """Dispara após ISSUE_HARD_TIMEOUT se o issue não terminou."""
            if not _done.wait(ISSUE_HARD_TIMEOUT):
                log.warning(
                    f"  [TIMEOUT] {title} #{iss_num} travou por "
                    f"{ISSUE_HARD_TIMEOUT}s — abortando"
                )
                _stop_event.set()          # encerra wait_for_image loops
                # Dá 3s para o driver se fechar graciosamente, depois mata tudo
                time.sleep(3)
                cleanup_chrome()
                _stop_event.clear()        # reseta para próximas issues

        timer = threading.Thread(target=_timeout_bomb, daemon=True)
        timer.start()

        try:
            for attempt in range(1, MAX_RETRIES + 1):
                if _stop_event.is_set():
                    with self._lock:
                        self._stats["aborted"] += 1
                    return

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
                    save_path = self.db.save_scraped_urls(order, urls)
                    print(f"  SALVO   : {save_path}  ({len(urls)} páginas)")
                    with self._lock:
                        self._stats["ok"] += 1
                    time.sleep(DELAY_BETWEEN_ISSUES)
                    return

                if attempt < MAX_RETRIES and not _stop_event.is_set():
                    log.warning(f"  [RETRY #{order}] falhou, tentando novamente...")
                    time.sleep(2)

            self.db.mark_scrape_failed(order, "failed")
            print(f"  FALHOU  : {title} #{iss_num} após {MAX_RETRIES} tentativas")
            with self._lock:
                self._stats["fail"] += 1

        finally:
            _done.set()   # cancela o timer se o issue terminou normalmente