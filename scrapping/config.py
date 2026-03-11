"""Central configuration for the scrapping package."""

from pathlib import Path

# ── Paths ───────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COMICS_DIR = PROJECT_ROOT / "comics"
DB_PATH = PROJECT_ROOT / "comics.db"
READING_ORDER_PATH = DATA_DIR / "reading_order.json"

# ── Site ────────────────────────────────────────────────────
BASE_URL = "https://readcomiconline.li"
ISSUE_URL = BASE_URL + "/Comic/{slug}/Issue-{issue}?quality=hq"
COMIC_URL = BASE_URL + "/Comic/{slug}"

# ── Tuning ──────────────────────────────────────────────────
DELAY_BETWEEN_ISSUES = 2.0       # seconds between scrape tasks
MIN_IMAGE_SIZE = 1000            # bytes — below this is corrupt/empty
DEFAULT_SCRAPE_WORKERS = 3       # parallel browser instances
DEFAULT_DOWNLOAD_WORKERS = 50    # parallel HTTP downloads
MAX_RETRIES = 3                  # per-issue scrape retries
PAGE_LOAD_TIMEOUT = 30           # seconds for Selenium page load
IMAGE_WAIT_TIMEOUT = 30          # seconds waiting for an image src
