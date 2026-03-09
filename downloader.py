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


def _extract_image_from_page(url, headless=True):
    """Open a browser, load ONE page, extract the image URL, close browser."""
    driver = None
    try:
        driver = _create_browser(headless)
        driver.get(url)
        
        # Wait for #divImage to exist
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "divImage"))
        )
        
        # Wait for an image with a blogspot src to appear (even if display:none)
        # In one-page mode images have display:none but src IS set
        for attempt in range(10):  # wait up to 5 seconds
            # Use JavaScript to get ALL img srcs inside divImage (works even for hidden imgs)
            srcs = driver.execute_script("""
                var imgs = document.querySelectorAll('#divImage img');
                var urls = [];
                for (var i = 0; i < imgs.length; i++) {
                    var src = imgs[i].src || '';
                    if (src && src.indexOf('blogspot') !== -1) {
                        urls.push(src);
                    }
                }
                return urls;
            """)
            if srcs:
                # Return the last blogspot URL (usually the higher quality one)
                return srcs[-1]
            time.sleep(0.5)
        
        return None
    except Exception:
        return None
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
            })
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(path, 'wb') as f:
                    f.write(resp.content)
                return len(resp.content)
        except Exception as e:
            log.error(f"      Download erro: {e}")
        return 0
    
    def download_issue(self, title, issue, order, year=""):
        """Download all pages of a comic issue using parallel browsers."""
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
        
        # Step 1: Scout — open one browser to get page count
        scout = None
        try:
            scout = _create_browser(self.headless)
            scout.get(url)
            time.sleep(3)
            
            # Check CAPTCHA
            if 'are you human' in scout.page_source.lower():
                log.warning(f"  [!!] CAPTCHA detectado - pulando")
                return False
            
            total_pages = _get_page_count(scout)
            if total_pages == 0:
                log.warning(f"  [!!] Nao encontrou seletor de paginas")
                return False
            
            log.info(f"  [OK] {total_pages} paginas detectadas")
        except Exception as e:
            log.error(f"  [ERRO] Scout falhou: {e}")
            return False
        finally:
            if scout:
                try:
                    scout.quit()
                except Exception:
                    pass
        
        # Step 2: Figure out which pages we still need
        pages_needed = []
        for p in range(1, total_pages + 1):
            page_path = os.path.join(issue_dir, f"page_{p:03d}.jpg")
            if os.path.exists(page_path) and os.path.getsize(page_path) > 1000:
                continue
            pages_needed.append(p)
        
        if not pages_needed:
            log.info(f"  [OK] Todas as {total_pages} paginas ja baixadas")
            return True
        
        log.info(f"  [>>] Baixando {len(pages_needed)} paginas ({self.chunk_size} browsers por vez)...")
        
        # Step 3: Process in chunks — open N browsers in parallel
        downloaded = total_pages - len(pages_needed)  # already existing
        
        for chunk_start in range(0, len(pages_needed), self.chunk_size):
            chunk = pages_needed[chunk_start:chunk_start + self.chunk_size]
            
            # Build URLs for this chunk: each page gets URL#pageNum
            page_urls = {p: f"{url}#{p}" for p in chunk}
            
            # Open browsers in parallel, each extracts one image URL
            image_urls = {}
            with ThreadPoolExecutor(max_workers=len(chunk)) as executor:
                futures = {
                    executor.submit(_extract_image_from_page, page_urls[p], self.headless): p 
                    for p in chunk
                }
                for future in as_completed(futures):
                    page_num = futures[future]
                    try:
                        src = future.result()
                        if src:
                            image_urls[page_num] = src
                        else:
                            log.warning(f"    Pagina {page_num}: imagem nao encontrada")
                    except Exception as e:
                        log.error(f"    Pagina {page_num}: erro: {e}")
            
            # Download collected images (parallel with requests, very fast)
            with ThreadPoolExecutor(max_workers=len(image_urls) or 1) as executor:
                def dl(page_num, src):
                
                    ext = '.jpg'
                    if '.png' in src.lower(): ext = '.png'
                    elif '.webp' in src.lower(): ext = '.webp'
                    path = os.path.join(issue_dir, f"page_{page_num:03d}{ext}")
                    return page_num, self._download_image(src, path)
                futures = {executor.submit(dl, p, s): p for p, s in image_urls.items()}
                for future in as_completed(futures):
                    page_num, size = future.result()
                    if size > 0:
                        downloaded += 1
                        log.info(f"    Pagina {page_num}/{total_pages} ({size//1024}KB)")
                    else:
                        log.warning(f"    Pagina {page_num} falhou no download")
            
            # Small delay between chunks to be polite
            if chunk_start + self.chunk_size < len(pages_needed):
                time.sleep(1)
        
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
