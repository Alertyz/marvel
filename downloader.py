#!/usr/bin/env python3
"""
X-Men Comic Downloader
Downloads comics from readcomiconline.li based on reading_order.json
Usage:
  python downloader.py                     # Download all issues
  python downloader.py --from-bookmark     # Download only unread (after bookmark)
  python downloader.py --dry-run           # Show URLs without downloading
  python downloader.py --series "X-Men"    # Download specific series only
  python downloader.py --phase "Fall of X" # Download specific phase only
"""

import json
import os
import re
import sys
import time
import argparse
import logging
from pathlib import Path
from urllib.parse import quote

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Config ──────────────────────────────────────────────────
BASE_URL = "https://readcomiconline.li"
COMIC_URL = BASE_URL + "/Comic/{slug}"
ISSUE_URL = BASE_URL + "/Comic/{slug}/Issue-{issue}?quality=hq"
OUTPUT_DIR = "comics"
DELAY_BETWEEN_PAGES = 1.5  # seconds
DELAY_BETWEEN_ISSUES = 3.0  # seconds
PROGRESS_FILE = "download_progress.json"

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# ── Title to URL slug mapping ───────────────────────────────
def title_to_slug(title, year=""):
    """Convert a comic title to the URL slug used by readcomiconline."""
    slug = title.strip()
    # Handle specific known mappings
    SLUG_MAP = {
        "House of X": "House-of-X",
        "Powers of X": "Powers-of-X",
        "X-Men": "X-Men-2019",
        "X-Men (2021)": "X-Men-2021",
        "X-Men (2024)": "X-Men-2024",
        "Marauders": "Marauders-2019",
        "Marauders (2022)": "Marauders-2022",
        "Excalibur": "Excalibur-2019",
        "New Mutants": "New-Mutants-2019",
        "X-Force": "X-Force-2019",
        "X-Force (2024)": "X-Force-2024",
        "Fallen Angels": "Fallen-Angels-2019",
        "Wolverine": "Wolverine-2020",
        "Wolverine (2024)": "Wolverine-2024",
        "Cable": "Cable-2020",
        "Cable (2024)": "Cable-2024",
        "X-Factor": "X-Factor-2020",
        "X-Factor (2024)": "X-Factor-2024",
        "Hellions": "Hellions-2020",
        "S.W.O.R.D.": "S-W-O-R-D-2020",
        "Children of the Atom": "Children-of-the-Atom",
        "Way of X": "Way-of-X",
        "X-Corp": "X-Corp-2021",
        "Inferno": "Inferno-2021",
        "Immortal X-Men": "Immortal-X-Men",
        "X-Men Red (2022)": "X-Men-Red-2022",
        "Knights of X": "Knights-of-X",
        "Legion of X": "Legion-of-X",
        "X-Terminators": "X-Terminators-2022",
        "Sabretooth": "Sabretooth-2022",
        "Invincible Iron Man": "Invincible-Iron-Man-2022",
        "Uncanny Avengers (2023)": "Uncanny-Avengers-2023",
        "Children of the Vault (2023)": "Children-of-the-Vault-2023",
        "Dark X-Men": "Dark-X-Men-2023",
        "Alpha Flight (2023)": "Alpha-Flight-2023",
        "Realm of X": "Realm-of-X",
        "Jean Grey": "Jean-Grey-2023",
        "Ms. Marvel: The New Mutant": "Ms-Marvel-The-New-Mutant",
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
        "Weapon X-Men": "Weapon-X-Men-2025",
        "X-Men United": "X-Men-United",
    }
    if slug in SLUG_MAP:
        return SLUG_MAP[slug]
    # Generic conversion: replace spaces and special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    return slug


def build_issue_url(title, issue, year=""):
    """Build the URL for a specific comic issue."""
    slug = title_to_slug(title, year)
    return ISSUE_URL.format(slug=slug, issue=issue)


def build_comic_url(title, year=""):
    """Build the URL for a comic series page."""
    slug = title_to_slug(title, year)
    return COMIC_URL.format(slug=slug)


# ── Progress tracking ───────────────────────────────────────
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"downloaded": []}


def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def is_downloaded(progress, order):
    return order in progress["downloaded"]


def mark_downloaded(progress, order):
    if order not in progress["downloaded"]:
        progress["downloaded"].append(order)
        save_progress(progress)


# ── Parallel browser downloader ────────────────────────────
def _create_browser(headless=True):
    """Create a fresh Chrome browser instance."""
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1280,900')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def _get_page_count(driver):
    """Get total page count from the Page dropdown."""
    from selenium.webdriver.support.ui import Select
    try:
        select_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "selectPage"))
        )
        return len(Select(select_el).options)
    except Exception:
        # Fallback: look for numbered dropdown
        for sel_el in driver.find_elements(By.TAG_NAME, "select"):
            try:
                opts = [o.text.strip() for o in Select(sel_el).options]
                if len(opts) > 5 and all(o.isdigit() for o in opts):
                    return len(opts)
            except Exception:
                continue
    return 0


def _extract_all_image_urls(url, headless=True):
    """Open ONE browser and extract ALL image URLs for every page of the issue.
    
    The site uses obfuscated JS arrays + decoy images in #divImage.
    Each page shows 3 <img> tags: 2 hidden decoys + 1 visible real image.
    The auth tokens (rhlupa/rnvuka) in the URL are tied to the browser's UA.
    
    Strategy: Navigate page-by-page using the #selectPage dropdown,
    capturing the VISIBLE image src each time. Waits for each image to
    fully load before moving to next page.
    
    Returns dict {page_number: image_url}
    """
    from selenium.webdriver.support.ui import Select
    driver = None
    try:
        driver = _create_browser(headless)
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "divImage"))
        )
        time.sleep(2)
        
        # Check CAPTCHA
        if 'are you human' in driver.page_source.lower():
            log.warning("  [!!] CAPTCHA detectado - pulando")
            return {}
        
        # Get total pages from dropdown
        total_pages = _get_page_count(driver)
        if total_pages == 0:
            log.warning("  [!!] Nao encontrou seletor de paginas")
            return {}
        
        log.info(f"  [OK] {total_pages} paginas detectadas")
        
        def _get_visible_image_src_loaded():
            """Get the src of the visible image ONLY if it's fully loaded."""
            return driver.execute_script("""
                var imgs = document.querySelectorAll('#divImage img');
                for (var i = 0; i < imgs.length; i++) {
                    if (imgs[i].style.display !== 'none') {
                        var src = imgs[i].src || '';
                        if (src && src.indexOf('blogspot') !== -1 && src.length > 50) {
                            // Check if image is actually loaded (not just src set)
                            if (imgs[i].complete && imgs[i].naturalWidth > 100) {
                                return src;
                            }
                            // src is set but still loading — return special marker
                            return '__loading__:' + src;
                        }
                    }
                }
                return null;
            """)
        
        def _wait_for_loaded_image(page_num, prev_src, timeout_s=30):
            """Wait for the visible image to have a NEW src and be fully loaded."""
            for attempt in range(timeout_s * 2):  # check every 0.5s
                result = _get_visible_image_src_loaded()
                if result and result.startswith('__loading__:'):
                    # src changed but image still loading — keep waiting
                    new_src = result[len('__loading__:'):]
                    if new_src != prev_src:
                        # src already changed, just wait for complete
                        time.sleep(0.5)
                        continue
                elif result and result != prev_src:
                    # Fully loaded with new src
                    return result.strip()
                time.sleep(0.5)
            
            # Timeout — try to grab whatever src is there even if not fully loaded
            fallback = driver.execute_script("""
                var imgs = document.querySelectorAll('#divImage img');
                for (var i = 0; i < imgs.length; i++) {
                    if (imgs[i].style.display !== 'none') {
                        var src = imgs[i].src || '';
                        if (src && src.indexOf('blogspot') !== -1 && src.length > 50) {
                            return src;
                        }
                    }
                }
                return null;
            """)
            if fallback and fallback != prev_src:
                return fallback.strip()
            return None
        
        image_urls = {}
        
        # Capture first page (already loaded)
        src = _wait_for_loaded_image(1, '', timeout_s=20)
        if src:
            image_urls[1] = src
        else:
            log.warning("    Pagina 1: imagem nao encontrada")
        
        # Navigate through remaining pages via the selectPage dropdown
        for page_num in range(2, total_pages + 1):
            prev_src = image_urls.get(page_num - 1, '')
            
            try:
                select_el = driver.find_element(By.ID, "selectPage")
                Select(select_el).select_by_index(page_num - 1)
            except Exception as e:
                log.warning(f"    Pagina {page_num}: erro ao navegar: {e}")
                continue
            
            # Wait for image to fully load
            src = _wait_for_loaded_image(page_num, prev_src, timeout_s=30)
            if src:
                image_urls[page_num] = src
            else:
                log.warning(f"    Pagina {page_num}: imagem nao encontrada")
            
            # Progress log every 10 pages
            if page_num % 10 == 0:
                log.info(f"    ... {page_num}/{total_pages} paginas processadas")
        
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


class ComicDownloader:
    def __init__(self, headless=True, output_dir=OUTPUT_DIR, chunk_size=10):
        if not HAS_SELENIUM:
            raise RuntimeError("Selenium nao esta instalado. Execute: pip install selenium")
        if not HAS_REQUESTS:
            raise RuntimeError("Requests nao esta instalado. Execute: pip install requests")
        
        self.output_dir = output_dir
        self.headless = headless
        self.chunk_size = chunk_size
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        })
    
    def close(self):
        pass  # No persistent browser to close
    
    def _download_image(self, src, path):
        """Download image via requests."""
        try:
            resp = self.session.get(src, timeout=30, headers={
                'Referer': 'https://readcomiconline.li/',
                'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
            })
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(path, 'wb') as f:
                    f.write(resp.content)
                return len(resp.content)
        except Exception as e:
            log.error(f"      Download erro: {e}")
        return 0
    
    def download_issue(self, title, issue, order, year=""):
        """Download all pages of a comic issue using a single browser."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        url = build_issue_url(title, issue, year)
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        issue_dir = os.path.join(self.output_dir, safe_title, f"Issue_{issue:03d}")
        os.makedirs(issue_dir, exist_ok=True)
        
        # Check if already downloaded
        existing = [f for f in os.listdir(issue_dir) if f.endswith(('.jpg', '.png', '.webp'))] if os.path.exists(issue_dir) else []
        if len(existing) > 10:
            log.info(f"  [OK] Ja baixado ({len(existing)} paginas)")
            return True
        
        log.info(f"  [->] Abrindo: {url}")
        
        # Step 1: Extract ALL image URLs using a single browser
        all_image_urls = _extract_all_image_urls(url, self.headless)
        
        if not all_image_urls:
            log.warning(f"  [!!] Nenhuma imagem encontrada")
            return False
        
        total_pages = len(all_image_urls)
        log.info(f"  [OK] {total_pages} URLs de imagens coletadas")
        
        # Step 2: Figure out which pages we still need
        pages_to_download = {}
        for page_num, src in all_image_urls.items():
            # Check all possible extensions
            found = False
            for ext in ('.jpg', '.png', '.webp'):
                page_path = os.path.join(issue_dir, f"page_{page_num:03d}{ext}")
                if os.path.exists(page_path) and os.path.getsize(page_path) > 1000:
                    found = True
                    break
            if not found:
                pages_to_download[page_num] = src
        
        if not pages_to_download:
            log.info(f"  [OK] Todas as {total_pages} paginas ja baixadas")
            return True
        
        log.info(f"  [>>] Baixando {len(pages_to_download)} paginas...")
        
        # Step 3: Download images in parallel via requests (fast!)
        downloaded = total_pages - len(pages_to_download)
        
        with ThreadPoolExecutor(max_workers=min(10, len(pages_to_download))) as executor:
            def dl(page_num, src):
                ext = '.jpg'
                if '.png' in src.lower(): ext = '.png'
                elif '.webp' in src.lower(): ext = '.webp'
                path = os.path.join(issue_dir, f"page_{page_num:03d}{ext}")
                return page_num, self._download_image(src, path)
            
            futures = {executor.submit(dl, p, s): p for p, s in pages_to_download.items()}
            for future in as_completed(futures):
                page_num, size = future.result()
                if size > 0:
                    downloaded += 1
                    log.info(f"    Pagina {page_num}/{total_pages} ({size//1024}KB)")
                else:
                    log.warning(f"    Pagina {page_num} falhou no download")
        
        log.info(f"  [OK] {title} #{issue}: {downloaded}/{total_pages} paginas em {issue_dir}")
        return downloaded > 0


# ── Main ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='X-Men Comic Downloader - readcomiconline.li')
    parser.add_argument('--from-bookmark', action='store_true', help='Download somente edições após o bookmark (2º Hellfire Gala)')
    parser.add_argument('--dry-run', action='store_true', help='Mostra URLs sem baixar')
    parser.add_argument('--series', type=str, help='Filtra por nome da série')
    parser.add_argument('--phase', type=str, help='Filtra por fase (ex: "Fall of X")')
    parser.add_argument('--headless', action='store_true', default=True, help='Executar navegador em modo headless')
    parser.add_argument('--no-headless', action='store_true', help='Mostrar janela do navegador')
    parser.add_argument('--chunk-size', type=int, default=10, help='Browsers paralelos por chunk (default: 10)')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR, help='Diretório de saída')
    parser.add_argument('--list-phases', action='store_true', help='Lista todas as fases disponíveis')
    parser.add_argument('--list-series', action='store_true', help='Lista todas as séries disponíveis')
    parser.add_argument('--reset-progress', action='store_true', help='Reseta progresso de downloads anteriores')
    
    args = parser.parse_args()
    
    # Load reading order
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reading_order.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    issues = data['issues']
    
    # List modes
    if args.list_phases:
        phases = sorted(set(i['phase'] for i in issues))
        print("\n📋 Fases disponíveis:")
        for p in phases:
            count = sum(1 for i in issues if i['phase'] == p)
            print(f"  • {p} ({count} edições)")
        return
    
    if args.list_series:
        series = sorted(set(i['title'] for i in issues))
        print(f"\n📋 Séries disponíveis ({len(series)}):")
        for s in series:
            count = sum(1 for i in issues if i['title'] == s)
            print(f"  • {s} ({count} edições)")
        return
    
    if args.reset_progress:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            log.info("Progresso resetado!")
        return
    
    # Filter issues
    if args.from_bookmark:
        bookmark_order = next((i['order'] for i in issues if i.get('bookmark')), None)
        if bookmark_order:
            issues = [i for i in issues if i['order'] >= bookmark_order]
            log.info(f"📍 Filtrando a partir do bookmark (ordem #{bookmark_order}): {len(issues)} edições")
    
    if args.series:
        issues = [i for i in issues if args.series.lower() in i['title'].lower()]
        log.info(f"🔍 Filtrando série '{args.series}': {len(issues)} edições")
    
    if args.phase:
        issues = [i for i in issues if args.phase.lower() in i['phase'].lower()]
        log.info(f"🔍 Filtrando fase '{args.phase}': {len(issues)} edições")
    
    if not issues:
        log.warning("⚠ Nenhuma edição encontrada com os filtros aplicados.")
        return
    
    # Dry run - just show URLs
    if args.dry_run:
        print(f"\n🔗 URLs para {len(issues)} edições:\n")
        for issue in issues:
            url = build_issue_url(issue['title'], issue['issue'], issue.get('year', ''))
            bookmark = " 📍 BOOKMARK" if issue.get('bookmark') else ""
            event = f" [{issue['event']}]" if issue.get('event') else ""
            print(f"  #{issue['order']:>3} | {issue['title']} #{issue['issue']}{event}{bookmark}")
            print(f"        {url}")
        print(f"\n📊 Total: {len(issues)} edições")
        print(f"🔗 URL da série (exemplo): {build_comic_url(issues[0]['title'], issues[0].get('year', ''))}")
        return
    
    # Actual download
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    progress = load_progress()
    headless = not args.no_headless
    
    log.info(f"Iniciando download de {len(issues)} edicoes")
    log.info(f"Diretorio de saida: {os.path.abspath(output_dir)}")
    
    downloader = None
    try:
        downloader = ComicDownloader(headless=headless, output_dir=output_dir, chunk_size=args.chunk_size)
        
        success = 0
        failed = 0
        skipped = 0
        
        for idx, issue in enumerate(issues):
            order = issue['order']
            
            if is_downloaded(progress, order):
                skipped += 1
                continue
            
            log.info(f"\n[{idx+1}/{len(issues)}] {issue['title']} #{issue['issue']} (ordem #{order})")
            
            if downloader.download_issue(issue['title'], issue['issue'], order, issue.get('year', '')):
                mark_downloaded(progress, order)
                success += 1
            else:
                failed += 1
            
            time.sleep(DELAY_BETWEEN_ISSUES)
        
        log.info(f"\n{'='*50}")
        log.info(f"✅ Download concluído!")
        log.info(f"  Sucesso: {success}")
        log.info(f"  Falhou:  {failed}")
        log.info(f"  Pulados: {skipped}")
        
    except KeyboardInterrupt:
        log.info("\n⏹ Download interrompido pelo usuário. Progresso salvo.")
    except Exception as e:
        log.error(f"\n✗ Erro fatal: {e}")
    finally:
        if downloader:
            downloader.close()


if __name__ == '__main__':
    main()
