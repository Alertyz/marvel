"""
CLI — Command-line interface for the scrapping package.

Usage:
    python -m scrapping scrape               # Phase 1: extract URLs
    python -m scrapping download             # Phase 2: download images
    python -m scrapping run                  # Both phases in sequence
    python -m scrapping validate             # Check integrity
    python -m scrapping validate --fix       # Fix problems
    python -m scrapping status               # Progress overview
    python -m scrapping status --detail      # Per-issue detail
    python -m scrapping flags                # Show validation flags
    python -m scrapping list-phases          # List available phases
    python -m scrapping list-series          # List available series
    python -m scrapping rescrape             # Reset issues for re-scrape

Filters (work with scrape/download/run/status):
    --series "X-Men"        # Filter by series name
    --phase "Fall of X"     # Filter by phase
    --from-bookmark         # Only after the bookmark
    --order 10-50           # Specific order range
"""

import json
import argparse
import logging
from pathlib import Path

from .config import (
    DB_PATH, COMICS_DIR, READING_ORDER_PATH,
    DEFAULT_SCRAPE_WORKERS, DEFAULT_DOWNLOAD_WORKERS,
)
from .db import ComicDB
from .scraper import ParallelScraper
from .new_downloader import ParallelDownloader
from .validator import DownloadValidator

log = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
#  FILTER HELPERS
# ════════════════════════════════════════════════════════════

def _build_filters(args) -> dict | None:
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


def _load_db(args) -> ComicDB:
    db = ComicDB(args.db)
    db.load_and_populate()
    return db


# ════════════════════════════════════════════════════════════
#  COMMANDS
# ════════════════════════════════════════════════════════════

def cmd_scrape(args):
    db = _load_db(args)
    filters = _build_filters(args)
    headless = not args.no_headless
    scraper = ParallelScraper(db, num_workers=args.workers, headless=headless)
    scraper.scrape_all(filters)
    db.close()


def cmd_download(args):
    db = _load_db(args)
    filters = _build_filters(args)
    dl = ParallelDownloader(db, num_workers=args.workers, output_dir=args.output)
    dl.download_all(filters)
    db.close()


def cmd_run(args):
    db = _load_db(args)
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


def cmd_validate(args):
    db = ComicDB(args.db)
    v = DownloadValidator(db, output_dir=args.output)
    v.validate(fix=args.fix)
    db.close()


def cmd_clear_pages(args):
    """
    Delete all scraped image URLs (pages table) and reset scrape_status to
    'pending' for affected issues.  The issues table is untouched — comic
    URLs, phases, titles, etc. are all preserved.  Run `scrape` afterwards
    to re-collect image URLs.
    """
    db = ComicDB(args.db)
    filters = _build_filters(args)

    # Safety confirmation unless --yes is passed
    if not getattr(args, "yes", False):
        scope = "TODAS as issues" if not filters else f"issues filtradas ({filters})"
        confirm = input(
            f"\nIsso vai apagar TODAS as URLs de páginas para {scope} "
            f"e resetar o scrape_status para 'pending'.\n"
            f"Digite 'sim' para confirmar: "
        ).strip().lower()
        if confirm != "sim":
            print("Cancelado.")
            db.close()
            return

    db.clear_all_page_urls(filters)
    print("URLs de páginas removidas. Execute 'scrape' para re-coletar.")
    db.close()


def cmd_clear_flags(args):
    db = ComicDB(args.db)
    c = db._conn()
    count = c.execute("SELECT COUNT(*) FROM validation_flags WHERE resolved=0").fetchone()[0]
    c.execute("DELETE FROM validation_flags")
    c.commit()
    print(f"\n{count} flags removidas.")
    db.close()


def cmd_flags(args):
    db = ComicDB(args.db)
    show_resolved = getattr(args, "resolved", False)
    flags = db.get_flags(resolved=show_resolved)

    if not flags:
        label = "resolvidas" if show_resolved else "ativas"
        print(f"\nNenhuma flag {label}.")
        db.close()
        return

    label = "RESOLVIDAS" if show_resolved else "ATIVAS"
    print(f"\n{'=' * 55}")
    print(f"  FLAGS DE VALIDACAO — {label}")
    print(f"{'=' * 55}")
    for f in flags:
        icon = "✅" if f["resolved"] else "⚠️"
        print(f"  {icon} #{f['issue_order']} {f['title']} #{f['issue']} [{f['flag_type']}]")
        print(f"     {f['message']}")
    print(f"{'=' * 55}")
    print(f"  Total: {len(flags)} flags")

    db.close()


def cmd_status(args):
    db = _load_db(args)
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
        bar = "\u2588" * filled + "\u2591" * (bar_len - filled)
        print(f"  Progresso:           [{bar}] {pct:.1f}%")
    if st["active_flags"]:
        print(f"  ─────────────────────────────────")
        print(f"  Flags ativas:        {st['active_flags']} (use 'flags' para ver)")
    print("=" * 55)

    if getattr(args, "detail", False):
        print()
        rows = db.get_detail_status(filters)
        icons = {
            "pending": "\u23f3", "done": "\u2705", "failed": "\u274c",
            "captcha": "\U0001f512", "unavailable": "\u26d4",
        }
        for r in rows:
            icon = icons.get(r["scrape_status"], "?")
            dl_info = ""
            if r["url_pages"] > 0:
                dl_info = f" | {r['done_pages']}/{r['url_pages']} pags"
            print(
                f"  #{r['order_num']:>4} {icon} {r['title']} #{r['issue']}"
                f" [{r['phase']}]{dl_info}"
            )

    db.close()


def cmd_list_phases(args):
    path = Path(READING_ORDER_PATH)
    with open(str(path), "r", encoding="utf-8") as f:
        data = json.load(f)
    phases: dict[str, int] = {}
    for iss in data["issues"]:
        p = iss["phase"]
        phases[p] = phases.get(p, 0) + 1
    print("\nFases disponiveis:")
    for p, c in phases.items():
        print(f"  \u2022 {p} ({c} edicoes)")


def cmd_list_series(args):
    path = Path(READING_ORDER_PATH)
    with open(str(path), "r", encoding="utf-8") as f:
        data = json.load(f)
    series: dict[str, int] = {}
    for iss in data["issues"]:
        t = iss["title"]
        series[t] = series.get(t, 0) + 1
    print(f"\nSeries disponiveis ({len(series)}):")
    for s in sorted(series):
        print(f"  \u2022 {s} ({series[s]} edicoes)")


def cmd_rescrape(args):
    db = ComicDB(args.db)
    if args.all_failed:
        c = db._conn()
        rows = c.execute(
            "SELECT order_num FROM issues WHERE scrape_status IN ('failed','captcha')"
        ).fetchall()
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


# ════════════════════════════════════════════════════════════
#  ARGUMENT PARSER
# ════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="X-Men Comic Scraper & Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--db", default=str(DB_PATH), help="Caminho do banco SQLite")
    parser.add_argument("--output", default=str(COMICS_DIR), help="Diretorio de saida")

    sub = parser.add_subparsers(dest="command", help="Comando")

    # ── scrape ──
    p_scrape = sub.add_parser("scrape", help="Fase 1: coletar URLs com browsers paralelos")
    p_scrape.add_argument("--workers", type=int, default=DEFAULT_SCRAPE_WORKERS)
    p_scrape.add_argument("--no-headless", action="store_true")
    p_scrape.add_argument("--series", type=str)
    p_scrape.add_argument("--phase", type=str)
    p_scrape.add_argument("--from-bookmark", action="store_true")
    p_scrape.add_argument("--order", type=str)

    # ── download ──
    p_dl = sub.add_parser("download", help="Fase 2: baixar imagens das URLs salvas")
    p_dl.add_argument("--workers", type=int, default=DEFAULT_DOWNLOAD_WORKERS)
    p_dl.add_argument("--series", type=str)
    p_dl.add_argument("--phase", type=str)
    p_dl.add_argument("--from-bookmark", action="store_true")
    p_dl.add_argument("--order", type=str)

    # ── run ──
    p_run = sub.add_parser("run", help="Scrape + Download em sequencia")
    p_run.add_argument("--scrape-workers", type=int, default=DEFAULT_SCRAPE_WORKERS)
    p_run.add_argument("--download-workers", type=int, default=DEFAULT_DOWNLOAD_WORKERS)
    p_run.add_argument("--no-headless", action="store_true")
    p_run.add_argument("--series", type=str)
    p_run.add_argument("--phase", type=str)
    p_run.add_argument("--from-bookmark", action="store_true")
    p_run.add_argument("--order", type=str)

    # ── validate ──
    p_val = sub.add_parser("validate", help="Verificar integridade dos downloads")
    p_val.add_argument("--fix", action="store_true", help="Resetar itens com problema")

    # ── flags ──
    p_flags = sub.add_parser("flags", help="Mostrar flags de validacao")
    p_flags.add_argument("--resolved", action="store_true", help="Mostrar flags resolvidas")

    # ── status ──
    p_status = sub.add_parser("status", help="Mostrar progresso geral")
    p_status.add_argument("--detail", action="store_true")
    p_status.add_argument("--series", type=str)
    p_status.add_argument("--phase", type=str)
    p_status.add_argument("--from-bookmark", action="store_true")
    p_status.add_argument("--order", type=str)

    # ── rescrape ──
    p_re = sub.add_parser("rescrape", help="Resetar issues para re-scrape")
    p_re.add_argument("--all-failed", action="store_true")
    p_re.add_argument("--order", type=str)

    # ── list ──
    sub.add_parser("list-phases", help="Listar fases disponiveis")
    sub.add_parser("list-series", help="Listar series disponiveis")

    # ── clear-pages ──
    p_cp = sub.add_parser(
        "clear-pages",
        help="Apagar todas as URLs de páginas (pages table) e resetar para re-scrape"
    )
    p_cp.add_argument("--yes", action="store_true", help="Pular confirmação interativa")
    p_cp.add_argument("--series", type=str)
    p_cp.add_argument("--phase", type=str)
    p_cp.add_argument("--order", type=str)

    # ── clear-flags ──
    sub.add_parser("clear-flags", help="Apagar todas as flags de validacao")

    return parser


COMMANDS = {
    "scrape": cmd_scrape,
    "download": cmd_download,
    "run": cmd_run,
    "validate": cmd_validate,
    "flags": cmd_flags,
    "clear-pages": cmd_clear_pages,
    "clear-flags": cmd_clear_flags,
    "status": cmd_status,
    "list-phases": cmd_list_phases,
    "list-series": cmd_list_series,
    "rescrape": cmd_rescrape,
}


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        COMMANDS[args.command](args)
    except KeyboardInterrupt:
        log.info("\nInterrompido pelo usuario. Progresso salvo no banco.")
    except Exception as e:
        log.error(f"Erro fatal: {e}")
        raise
    finally:
        from .scraper import cleanup_chrome
        cleanup_chrome()