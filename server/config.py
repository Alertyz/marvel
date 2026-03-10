from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
COMICS_DIR = BASE_DIR / "comics"
DB_PATH = BASE_DIR / "comics.db"
READING_ORDER_PATH = DATA_DIR / "reading_order.json"

# Server settings
HOST = "0.0.0.0"
PORT = 8080
