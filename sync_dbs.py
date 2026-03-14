import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path("c:/Users/alec_/Downloads/marvel")))

from server.database import ReaderDB
from scrapping.db import ComicDB

print("Sincronizando banco de dados do Leitor (ReaderDB)...")
db2 = ReaderDB()
print(" ReaderDB sincronizado com sucesso!")

print("Sincronizando banco de dados do Scraper (ComicDB)...")
db1 = ComicDB()
db1.load_and_populate()
print(" ScraperDB sincronizado com sucesso!")

print("Fim da sincronizacao. Duplicatas excluidas!")
