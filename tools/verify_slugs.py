#!/usr/bin/env python3
"""
Verify comic URL slugs against readcomiconline.li
Tests the first issue of each unique series to check if the slug resolves.
Reports which slugs are wrong and tries to find the correct one via search.

Usage:
  python verify_slugs.py              # Check all slugs (headless)
  python verify_slugs.py --workers 5  # 5 parallel browsers
  python verify_slugs.py --visible    # Show browser windows
"""

import json
import os
import re
import sys
import time
import atexit
import signal
import argparse
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BASE_URL = "https://readcomiconline.li"

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
    with _drivers_lock:
        for d in _active_drivers:
            try:
                d.quit()
            except Exception:
                pass
        _active_drivers.clear()
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
    print("\nInterrompido — fechando browsers...")
    _cleanup_all_chrome()
    sys.exit(1)

atexit.register(_cleanup_all_chrome)
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# Current slug map from downloader.py
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


def title_to_slug(title):
    slug = title.strip()
    if slug in SLUG_MAP:
        return SLUG_MAP[slug]
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    return slug


def create_browser(headless=True):
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


def check_slug(title, headless=True):
    """Check if a slug resolves to a valid comic page.
    Returns dict with results."""
    slug = title_to_slug(title)
    # Try the comic series page first (not an issue page)
    url = f"{BASE_URL}/Comic/{slug}"
    issue_url = f"{BASE_URL}/Comic/{slug}/Issue-1?quality=hq"

    result = {
        "title": title,
        "slug": slug,
        "series_url": url,
        "issue_url": issue_url,
        "status": "unknown",
        "real_url": None,
        "issues_found": [],
        "has_annuals": False,
        "error": None,
    }

    driver = None
    try:
        driver = create_browser(headless)

        # Check the series page
        driver.get(url)
        time.sleep(2)

        current_url = driver.current_url
        page_source = driver.page_source.lower()

        # Check for "not found" or redirect to home
        if "page not found" in page_source or "comic not found" in page_source:
            result["status"] = "NOT_FOUND"
            # Try search to find the correct slug
            result["suggestion"] = _try_search(driver, title)
            return result

        if current_url.rstrip("/") != url.rstrip("/"):
            result["status"] = "REDIRECTED"
            result["real_url"] = current_url
            return result

        # Page loaded — check for issue list and annuals
        try:
            # Look for issue links in the page
            issue_links = driver.find_elements(By.CSS_SELECTOR, "table.listing a")
            issues = []
            has_annual = False
            for link in issue_links:
                href = link.get_attribute("href") or ""
                text = link.text.strip()
                if "/Annual-" in href or "Annual" in text:
                    has_annual = True
                if "/Issue-" in href or "/Annual-" in href or "/Full" in href:
                    issues.append(text)

            result["issues_found"] = issues[:5]  # First 5 for display
            result["total_issues"] = len(issues)
            result["has_annuals"] = has_annual
            result["status"] = "OK"
        except Exception:
            result["status"] = "OK"  # Page loaded but couldn't parse issues

        return result

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)[:200]
        return result
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            _unregister_driver(driver)


def _try_search(driver, title):
    """Try to search for the comic and return suggested slug."""
    try:
        # Clean search term
        search_term = re.sub(r'\s*\(\d{4}\)\s*', '', title).strip()
        search_url = f"{BASE_URL}/Search/Comic"
        driver.get(search_url)
        time.sleep(1)

        search_box = driver.find_element(By.ID, "keyword")
        search_box.clear()
        search_box.send_keys(search_term)

        # Submit
        driver.find_element(By.CSS_SELECTOR, "input[type='image']").click()
        time.sleep(3)

        # Look for results
        links = driver.find_elements(By.CSS_SELECTOR, "table.listing a")
        suggestions = []
        for link in links:
            href = link.get_attribute("href") or ""
            text = link.text.strip()
            if "/Comic/" in href and text:
                # Extract slug from URL
                match = re.search(r'/Comic/([^/?]+)', href)
                if match:
                    suggestions.append({"name": text, "slug": match.group(1), "url": href})

        return suggestions[:5]
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="Verify comic URL slugs")
    parser.add_argument("--workers", type=int, default=3, help="Parallel browsers")
    parser.add_argument("--visible", action="store_true", help="Show browser windows")
    parser.add_argument("--title", type=str, help="Check a single title")
    args = parser.parse_args()

    # Load all unique titles
    with open(PROJECT_ROOT / "data" / "reading_order.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    if args.title:
        titles = [args.title]
    else:
        seen = set()
        titles = []
        for iss in data["issues"]:
            t = iss["title"]
            if t not in seen:
                seen.add(t)
                titles.append(t)

    print(f"\nVerificando {len(titles)} series...\n")

    headless = not args.visible
    results = []
    lock = threading.Lock()
    done = [0]

    def check_one(title):
        r = check_slug(title, headless)
        with lock:
            done[0] += 1
            status_icon = {"OK": "✅", "NOT_FOUND": "❌", "REDIRECTED": "↪️", "ERROR": "⚠️"}.get(r["status"], "?")
            extra = ""
            if r["has_annuals"]:
                extra += " [HAS ANNUALS]"
            if r["status"] == "NOT_FOUND" and r.get("suggestion"):
                names = [s["slug"] for s in r["suggestion"][:3]]
                extra += f" → sugestoes: {', '.join(names)}"
            if r["status"] == "REDIRECTED":
                extra += f" → {r['real_url']}"
            print(f"  [{done[0]:>3}/{len(titles)}] {status_icon} {title}")
            print(f"           slug: {r['slug']}{extra}")
            if r.get("error"):
                print(f"           erro: {r['error'][:100]}")
        time.sleep(1)
        return r

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(check_one, t): t for t in titles}
        for f in as_completed(futures):
            results.append(f.result())

    # Summary
    ok = [r for r in results if r["status"] == "OK"]
    not_found = [r for r in results if r["status"] == "NOT_FOUND"]
    redirected = [r for r in results if r["status"] == "REDIRECTED"]
    errors = [r for r in results if r["status"] == "ERROR"]
    with_annuals = [r for r in results if r["has_annuals"]]

    print(f"\n{'='*60}")
    print(f"  RESULTADO")
    print(f"{'='*60}")
    print(f"  ✅ OK:         {len(ok)}")
    print(f"  ❌ Not Found:  {len(not_found)}")
    print(f"  ↪️  Redirected: {len(redirected)}")
    print(f"  ⚠️  Errors:     {len(errors)}")
    print(f"  📚 Com Annuals: {len(with_annuals)}")

    if not_found:
        print(f"\n{'─'*60}")
        print("  SLUGS ERRADOS (não encontrados):")
        for r in not_found:
            print(f"    ❌ \"{r['title']}\" → slug atual: {r['slug']}")
            if r.get("suggestion"):
                for s in r["suggestion"][:3]:
                    print(f"       sugestão: {s['name']} → {s['slug']}")

    if redirected:
        print(f"\n{'─'*60}")
        print("  REDIRECIONADOS:")
        for r in redirected:
            print(f"    ↪️  \"{r['title']}\" → {r['real_url']}")

    if with_annuals:
        print(f"\n{'─'*60}")
        print("  SÉRIES COM ANNUALS:")
        for r in with_annuals:
            print(f"    📚 {r['title']} ({r['slug']})")

    # Save full results
    output = {
        "results": [
            {
                "title": r["title"],
                "slug": r["slug"],
                "status": r["status"],
                "has_annuals": r["has_annuals"],
                "real_url": r["real_url"],
                "suggestion": r.get("suggestion", []),
                "total_issues": r.get("total_issues", 0),
            }
            for r in results
        ]
    }
    out_path = PROJECT_ROOT / "data" / "slug_verification.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResultados salvos em {out_path}")


if __name__ == "__main__":
    main()
