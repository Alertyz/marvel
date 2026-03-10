#!/usr/bin/env python3
"""
Auto Slug Finder
================
Tries auto-generated slug candidates via HTTP HEAD requests.
Only asks the user when all candidates fail.

Results saved to data/found_slugs.json (resume-safe).
At the end, auto-patches downloader.py with new mappings.

Usage:
    python tools/find_slugs.py             # auto-try + interactive fallback
    python tools/find_slugs.py --list      # just list what's missing
    python tools/find_slugs.py --apply     # apply found_slugs.json to downloader.py
"""

import json
import re
import sys
import time
import webbrowser
import argparse
from pathlib import Path
from urllib.parse import quote_plus

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

READING_ORDER = PROJECT_ROOT / "data" / "reading_order.json"
FOUND_SLUGS_FILE = PROJECT_ROOT / "data" / "found_slugs.json"
DOWNLOADER_FILE = PROJECT_ROOT / "tools" / "downloader.py"
BASE_URL = "https://readcomiconline.li"
SEARCH_URL = BASE_URL + "/Search/Comic"

# ── Import slug maps from downloader ──
from downloader import SLUG_MAP, SPECIAL_ISSUE_URL, UNAVAILABLE_TITLES

# Polite delay between HTTP checks (avoid hammering the server)
CHECK_DELAY = 1.5

# Common headers to look like a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ════════════════════════════════════════════════════════════
#  UTILITIES
# ════════════════════════════════════════════════════════════

def load_reading_order():
    with open(READING_ORDER, encoding="utf-8") as f:
        return json.load(f)


def load_found_slugs():
    if FOUND_SLUGS_FILE.exists():
        with open(FOUND_SLUGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_found_slugs(found):
    with open(FOUND_SLUGS_FILE, "w", encoding="utf-8") as f:
        json.dump(found, f, indent=2, ensure_ascii=False)


def get_missing_titles(data):
    """Return sorted list of (title, issue_count, is_oneshot) not in any map."""
    from collections import Counter
    counts = Counter()
    for iss in data["issues"]:
        counts[iss["title"]] += 1

    missing = []
    for title, count in sorted(counts.items()):
        if title in SLUG_MAP or title in SPECIAL_ISSUE_URL or title in UNAVAILABLE_TITLES:
            continue
        missing.append((title, count, count == 1))
    return missing


# ════════════════════════════════════════════════════════════
#  SLUG CANDIDATE GENERATION
# ════════════════════════════════════════════════════════════

def generate_slug_candidates(title):
    """Generate multiple plausible slug variants for a title.
    Returns list of slug strings to try, best guesses first."""
    candidates = []

    # --- Base: replace special chars with hyphens ---
    def _slugify(s):
        s = s.replace("'", "-s-").replace("'", "-s-")  # apostrophes
        s = s.replace("&", "and")
        s = s.replace(".", "-")
        s = s.replace("/", "-")
        s = s.replace(":", "")
        s = s.replace(",", "")
        s = s.replace("!", "")
        s = s.replace("?", "")
        s = s.replace("(", "").replace(")", "")
        s = re.sub(r'[^\w\s-]', '', s)
        s = re.sub(r'[\s]+', '-', s.strip())
        s = re.sub(r'-+', '-', s)
        return s.strip('-')

    base = _slugify(title)
    candidates.append(base)

    # Variant: apostrophe as just removal (no -s-)
    if "'" in title or "\u2019" in title:
        s2 = title.replace("'", "").replace("\u2019", "")
        candidates.append(_slugify(s2))
        # Also try with -s (no extra hyphens)
        s3 = title.replace("'s", "-s").replace("\u2019s", "-s")
        s3 = s3.replace("'", "").replace("\u2019", "")
        candidates.append(_slugify(s3))

    # Variant: with & as -
    if "&" in title:
        s4 = title.replace("&", "")
        candidates.append(_slugify(s4))
        s5 = title.replace(" & ", "-")
        candidates.append(_slugify(s5))

    # Extract year from title like "X-Men (2024)"
    year_match = re.search(r'\((\d{4})\)', title)
    bare_title = re.sub(r'\s*\(\d{4}\)\s*', '', title).strip()
    bare_slug = _slugify(bare_title)

    if year_match:
        year = year_match.group(1)
        # Title-YYYY
        candidates.append(f"{bare_slug}-{year}")
        # Just the bare title (some comics don't have year in slug)
        candidates.append(bare_slug)
    else:
        # Try adding common years if no year in title
        for y in ["2025", "2024", "2023", "2022"]:
            candidates.append(f"{base}-{y}")

    # Variant: colons → hyphen
    if ":" in title:
        no_colon = title.replace(": ", "-").replace(":", "-")
        candidates.append(_slugify(no_colon))

    # Variant: "Vol N" handling
    vol_match = re.search(r'Vol\.?\s*(\d+)', title)
    if vol_match:
        vol_num = vol_match.group(1)
        no_vol = re.sub(r'\s*Vol\.?\s*\d+', '', title).strip()
        candidates.append(_slugify(no_vol))
        candidates.append(f"{_slugify(no_vol)}-Vol-{vol_num}")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


# ════════════════════════════════════════════════════════════
#  HTTP SLUG VERIFICATION
# ════════════════════════════════════════════════════════════

def check_slug_exists(slug, session):
    """Check if a comic slug exists on the site. Returns True/False."""
    url = f"{BASE_URL}/Comic/{slug}"
    try:
        resp = session.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        # The site returns 200 even for missing comics but with different content.
        # A valid comic page contains the comic title; missing pages redirect or show error.
        if resp.status_code == 200:
            # Check if pages has actual comic content (issue list, etc.)
            text = resp.text
            if '/Comic/' + slug + '/Issue-' in text or 'class="listing"' in text or '/Comic/' + slug + '/Full' in text:
                return True
        return False
    except requests.RequestException:
        return False


def check_oneshot_exists(slug_path, session):
    """Check if a one-shot URL path exists (slug/Full or slug/Named-Path)."""
    url = f"{BASE_URL}/Comic/{slug_path}?quality=hq"
    try:
        resp = session.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code == 200 and ('id="divImage"' in resp.text or 'lstImages' in resp.text):
            return True
        return False
    except requests.RequestException:
        return False


def auto_find_slug(title, count, is_oneshot, session):
    """Try all candidate slugs via HTTP. Returns (type, value) or None."""
    candidates = generate_slug_candidates(title)

    for slug in candidates:
        if is_oneshot:
            # Try /Full and /Issue-1 endpoints
            for suffix in ("/Full", "/Issue-1"):
                path = f"{slug}{suffix}"
                if check_oneshot_exists(path, session):
                    return ("special", path)
                time.sleep(CHECK_DELAY)
        else:
            if check_slug_exists(slug, session):
                return ("slug", slug)
            time.sleep(CHECK_DELAY)
        continue

    return None


# ════════════════════════════════════════════════════════════
#  URL PARSING
# ════════════════════════════════════════════════════════════

def extract_slug_from_url(url):
    """Extract slug/path from a readcomiconline URL."""
    url = url.strip()
    if "?" in url:
        url = url.split("?")[0]

    m = re.search(r'/Comic/(.+)', url)
    if m:
        path = m.group(1).rstrip("/")
        return path

    if "/" in url and not url.startswith("http"):
        return url.strip("/")
    return url


def classify_slug(raw_path, title, issue_count):
    """Determine if this should go in SLUG_MAP or SPECIAL_ISSUE_URL."""
    parts = raw_path.split("/")
    if issue_count == 1:
        if len(parts) >= 2:
            return ("special", title, raw_path)
        else:
            return ("special", title, raw_path + "/Full")
    else:
        # For multi-issue titles, strip issue path to get base slug
        return ("slug", title, parts[0])


# ════════════════════════════════════════════════════════════
#  INTERACTIVE FALLBACK
# ════════════════════════════════════════════════════════════

def open_search(title):
    """Open browser with search on readcomiconline + Google."""
    search_query = quote_plus(title.replace(":", "").replace("'", ""))
    webbrowser.open(f"{SEARCH_URL}?keyword={search_query}")
    google_q = quote_plus(f"site:readcomiconline.li {title}")
    webbrowser.open(f"https://www.google.com/search?q={google_q}")


def ask_user_for_slug(title, count, is_oneshot):
    """Interactive fallback: open browser search and ask user for URL."""
    tipo = "ONE-SHOT" if is_oneshot else f"{count} issues"
    print(f"  ❌ Auto-check falhou — abrindo busca no navegador...")
    open_search(title)

    while True:
        resp = input(f"  URL ou slug (s=skip, u=unavailable, q=quit): ").strip()

        if resp.lower() == 'q':
            return "quit", None, None
        if resp.lower() == 's':
            return "skip", None, None
        if resp.lower() == 'u':
            return "unavailable", None, None
        if not resp:
            continue

        raw_path = extract_slug_from_url(resp)
        map_type, _, value = classify_slug(raw_path, title, count)

        if map_type == "slug":
            print(f'  → SLUG_MAP["{title}"] = "{value}"')
        else:
            print(f'  → SPECIAL_ISSUE_URL["{title}"] = "{value}"')

        confirm = input(f"  Correto? (Enter=sim, n=não): ").strip()
        if confirm.lower() == 'n':
            continue

        return map_type, title, value


# ════════════════════════════════════════════════════════════
#  APPLY TO DOWNLOADER.PY
# ════════════════════════════════════════════════════════════

def apply_to_downloader(found):
    """Patch downloader.py with new slug mappings from found_slugs.json."""
    src = DOWNLOADER_FILE.read_text(encoding="utf-8")

    new_slugs = {}
    new_specials = {}
    new_unavailable = set()

    for title, entry in found.items():
        t = entry.get("type")
        v = entry.get("value", "")
        if t == "slug" and title not in SLUG_MAP:
            new_slugs[title] = v
        elif t == "special" and title not in SPECIAL_ISSUE_URL:
            new_specials[title] = v
        elif t == "unavailable" and title not in UNAVAILABLE_TITLES:
            new_unavailable.add(title)

    if not new_slugs and not new_specials and not new_unavailable:
        print("Nada novo para aplicar.")
        return

    if new_slugs:
        slug_block = "\n".join(f'    "{t}": "{s}",' for t, s in sorted(new_slugs.items()))
        slug_map_end = src.find("}\n\n# Titles whose URL uses a named path")
        if slug_map_end == -1:
            slug_map_end = src.find("}\n\nSPECIAL_ISSUE_URL")
        if slug_map_end != -1:
            src = src[:slug_map_end] + "    # ── Auto-added by find_slugs.py ──\n" + slug_block + "\n" + src[slug_map_end:]
            print(f"  + {len(new_slugs)} entradas no SLUG_MAP")

    if new_specials:
        special_block = "\n".join(f'    "{t}": "{p}",' for t, p in sorted(new_specials.items()))
        special_end = src.find("}\n\n# Titles not available")
        if special_end == -1:
            special_end = src.find("}\n\nUNAVAILABLE_TITLES")
        if special_end != -1:
            src = src[:special_end] + "    # ── Auto-added by find_slugs.py ──\n" + special_block + "\n" + src[special_end:]
            print(f"  + {len(new_specials)} entradas no SPECIAL_ISSUE_URL")

    if new_unavailable:
        unavail_block = "\n".join(f'    "{t}",' for t in sorted(new_unavailable))
        unavail_end = src.find("}\n\n\ndef title_to_slug")
        if unavail_end != -1:
            src = src[:unavail_end] + "    # ── Auto-added by find_slugs.py ──\n" + unavail_block + "\n" + src[unavail_end:]
            print(f"  + {len(new_unavailable)} entradas no UNAVAILABLE_TITLES")

    DOWNLOADER_FILE.write_text(src, encoding="utf-8")
    print("✓ downloader.py atualizado!")


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Auto-find missing comic slugs")
    parser.add_argument("--list", action="store_true", help="List missing titles")
    parser.add_argument("--apply", action="store_true", help="Apply found_slugs.json to downloader.py")
    parser.add_argument("--manual-only", action="store_true", help="Skip auto-check, go straight to interactive")
    args = parser.parse_args()

    data = load_reading_order()
    found = load_found_slugs()
    missing = get_missing_titles(data)

    if args.apply:
        apply_to_downloader(found)
        return

    if args.list:
        print(f"\n{len(missing)} títulos faltando:\n")
        for title, count, is_oneshot in missing:
            status = "✓" if title in found else " "
            tipo = "ONE-SHOT" if is_oneshot else f"{count} issues"
            print(f"  [{status}] {title}  ({tipo})")
        already = len([t for t, _, _ in missing if t in found])
        print(f"\n  {already}/{len(missing)} já encontrados")
        return

    if not missing:
        print("✓ Todos os títulos já têm slug mapeado!")
        return

    already_found = len([t for t, _, _ in missing if t in found])
    to_process = [(t, c, o) for t, c, o in missing if t not in found]

    print(f"\n{'='*60}")
    print(f"  SLUG FINDER — {len(missing)} títulos faltando")
    print(f"{'='*60}")
    print(f"  Já encontrados: {already_found}")
    print(f"  Restantes:      {len(to_process)}")
    print(f"{'='*60}")

    if not args.manual_only:
        print(f"\n── FASE 1: Auto-check via HTTP ──")
        print(f"  Testando slugs gerados automaticamente...")
        print(f"  (delay de {CHECK_DELAY}s entre requests)\n")

    session = requests.Session()
    auto_ok = []
    auto_fail = []

    for i, (title, count, is_oneshot) in enumerate(to_process):
        tipo = "ONE-SHOT" if is_oneshot else f"{count} issues"
        candidates = generate_slug_candidates(title)

        if args.manual_only:
            auto_fail.append((title, count, is_oneshot))
            continue

        print(f"  [{i+1}/{len(to_process)}] {title}  ({tipo})")
        print(f"    Candidatos: {', '.join(candidates[:4])}{'...' if len(candidates) > 4 else ''}")

        result = auto_find_slug(title, count, is_oneshot, session)

        if result:
            map_type, value = result
            found[title] = {"type": map_type, "value": value}
            auto_ok.append((title, map_type, value))
            save_found_slugs(found)
            print(f"    ✅ ENCONTRADO: {value}")
        else:
            auto_fail.append((title, count, is_oneshot))
            print(f"    ❌ não encontrado automaticamente")

    print(f"\n── Resultado auto-check ──")
    print(f"  ✅ Encontrados: {len(auto_ok)}")
    print(f"  ❌ Falharam:    {len(auto_fail)}")

    if not auto_fail:
        print(f"\n✓ Todos resolvidos automaticamente!")
        save_found_slugs(found)
        resp = input("\nAplicar ao downloader.py? (s/n): ").strip()
        if resp.lower() == 's':
            apply_to_downloader(found)
        return

    # ── FASE 2: Interactive fallback ──
    print(f"\n── FASE 2: Busca manual ({len(auto_fail)} restantes) ──")
    print("  Cole a URL correta, ou:")
    print("    's' = pular    'u' = indisponível    'q' = sair e salvar\n")

    manual_ok = 0
    skipped = 0

    for i, (title, count, is_oneshot) in enumerate(auto_fail):
        tipo = "ONE-SHOT" if is_oneshot else f"{count} issues"
        remaining = len(auto_fail) - i
        print(f"\n[{i+1}/{len(auto_fail)}] (restam {remaining}) {title}  ({tipo})")

        result_type, _, value = ask_user_for_slug(title, count, is_oneshot)

        if result_type == "quit":
            save_found_slugs(found)
            print(f"\n✓ Progresso salvo! Execute novamente para continuar.")
            break
        elif result_type == "skip":
            skipped += 1
            continue
        elif result_type == "unavailable":
            found[title] = {"type": "unavailable"}
            save_found_slugs(found)
            print(f"  → Marcado como INDISPONÍVEL")
            manual_ok += 1
        elif result_type in ("slug", "special"):
            found[title] = {"type": result_type, "value": value}
            save_found_slugs(found)
            print(f"  ✓ Salvo!")
            manual_ok += 1

    save_found_slugs(found)
    total_found = len(auto_ok) + manual_ok
    print(f"\n{'='*60}")
    print(f"  RESUMO")
    print(f"{'='*60}")
    print(f"  Auto-encontrados:  {len(auto_ok)}")
    print(f"  Manual:            {manual_ok}")
    print(f"  Pulados:           {skipped}")
    print(f"  Total novos:       {total_found}")
    print(f"{'='*60}")

    if total_found > 0:
        resp = input("\nAplicar ao downloader.py? (s/n): ").strip()
        if resp.lower() == 's':
            apply_to_downloader(found)


if __name__ == "__main__":
    main()
