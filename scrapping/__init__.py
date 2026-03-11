"""
scrapping — X-Men Comic Scraper & Downloader
=============================================
Modular package for scraping comic image URLs and downloading them.

Architecture:
    config.py      - Paths, constants, tuning
    slugs.py       - URL slug mappings & builders
    db.py          - Thread-safe SQLite persistence
    scraper.py     - Phase 1: browser-based URL extraction
    downloader.py  - Phase 2: parallel HTTP image downloads
    validator.py   - Post-download integrity checks
    cli.py         - Command-line interface
"""
