"""
URL slug mappings and builders for readcomiconline.li.

To add a new series:
    1. Add to SLUG_MAP (multi-issue) or SPECIAL_ISSUE_URL (one-shots/named paths).
    2. Or run find_slugs.py to auto-discover and patch this file.
"""

import re
from .config import BASE_URL, ISSUE_URL, COMIC_URL

# ── Multi-issue series: title → URL slug ────────────────────
SLUG_MAP = {
    "House of X": "House-of-X",
    "Powers of X": "Powers-of-X",
    "X-Men": "X-Men-2019",
    "X-Men (2021)": "X-Men-2021",
    "X-Men (2024)": "X-Men-2024",
    "Marauders": "Marauders",
    "Marauders (2022)": "Marauders-2022",
    "Excalibur": "Excalibur-2019",
    "New Mutants": "New-Mutants-2019",
    "X-Force": "X-Force-2019-2",
    "X-Force (2024)": "X-Force-2024",
    "Fallen Angels": "Fallen-Angels",
    "Wolverine": "Wolverine-2020",
    "Wolverine (2024)": "Wolverine-2024",
    "Cable": "Cable-2020",
    "Cable (2024)": "Cable-2024",
    "X-Men/Fantastic Four": "X-Men-Fantastic-Four",
    "X-Factor": "X-Factor-2020",
    "X-Factor (2024)": "X-Factor-2024",
    "Hellions": "Hellions",
    "S.W.O.R.D.": "S-W-O-R-D-2020",
    "Children of the Atom": "Children-of-the-Atom",
    "Way of X": "Way-of-X",
    "X-Corp": "X-Corp",
    "Inferno": "Inferno-2021",
    "X-Men: The Onslaught Revelation": "X-Men-Onslaught-Revelation",
    "X of Swords: Stasis": "X-Of-Swords-Stasis",
    "X of Swords: Destruction": "X-Of-Swords-Destruction",
    "Immortal X-Men": "Immortal-X-Men",
    "X-Men Red (2022)": "X-Men-Red-2022",
    "Knights of X": "Knights-of-X",
    "Legion of X": "Legion-of-X",
    "X-Terminators": "X-Terminators-2022",
    "Sabretooth": "Sabretooth-2022",
    "Invincible Iron Man": "The-Invincible-Iron-Man-2022",
    "A.X.E.: Eve of Judgment": "A-X-E-Eve-Of-Judgment",
    "A.X.E.: Judgment Day": "A-X-E-Judgment-Day",
    "A.X.E.: Death to the Mutants": "A-X-E-Death-to-the-Mutants",
    "A.X.E.: Judgment Day Omega": "A-X-E-Judgment-Day-Omega",
    "Uncanny Avengers (2023)": "Uncanny-Avengers-2023",
    "Children of the Vault (2023)": "Children-of-the-Vault",
    "Dark X-Men": "Dark-X-Men-2023",
    "Alpha Flight (2023)": "Alpha-Flight-2023",
    "Realm of X": "Realm-of-X",
    "Jean Grey": "Jean-Grey-2023",
    "Ms. Marvel: The New Mutant": "Ms-Marvel-The-New-Mutant",
    "Storm and the Brotherhood of Mutants": "Storm-the-Brotherhood-of-Mutants",
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
    "Weapon X-Men": "Weapon-X-Men-Existed",
    "Storm: Earth's Mightiest Mutant": "Storm-Earth-s-Mightiest-Mutant",
    "Secret X-Men": "The-Secret-X-Men",
    "Giant-Size X-Men (2025)": "Giant-Size-X-Men-2025",
    "Deadpool/Wolverine": "Deadpool-Wolverine",
    "Sinister's Six": "Sinister-s-Six",
    # ── Auto-added by find_slugs.py ──
    "Amazing X-Men (2025)": "Amazing-X-Men-2025",
    "Astonishing Iceman": "Astonishing-Iceman",
    "Betsy Braddock: Captain Britain": "Betsy-Braddock-Captain-Britain",
    "Binary": "Binary",
    "Bishop: War College": "Bishop-War-College",
    "Cable: Love and Chrome": "Cable-Love-and-Chrome",
    "Champions (2020)": "Champions-2020",
    "Cloak or Dagger": "Cloak-or-Dagger",
    "Dark Web: X-Men": "Dark-Web-X-Men",
    "Deadpool": "Deadpool-2020",
    "Devil's Reign: X-Men": "Devil-s-Reign-X-Men",
    "Empyre: X-Men": "Empyre-X-Men",
    "Eternals (2021)": "Eternals-2021",
    "Expatriate X-Men": "Expatriate-X-Men",
    "Hellverine Vol 1": "Hellverine",
    "Hellverine Vol 2": "Hellverine-Vol-2",
    "Immoral X-Men": "Immoral-X-Men",
    "Inglorious X-Force": "Inglorious-X-Force",
    "Iron & Frost": "Iron-Frost",
    "King in Black": "King-in-Black",
    "Laura Kinney: Sabretooth": "Laura-Kinney-Sabretooth",
    "Life of Wolverine Infinity Comic": "Life-of-Wolverine-Infinity-Comic",
    "Longshots": "Longshots",
    "Love Unlimited Infinity Comic": "Love-Unlimited-Infinity-Comic",
    "Ms. Marvel: Mutant Menace": "Ms-Marvel-Mutant-Menace",
    "New Mutants: Lethal Legion": "New-Mutants-Lethal-Legion",
    "Nightcrawlers": "Nightcrawlers",
    "Omega Kids": "Omega-Kids",
    "Radioactive Spider-Man": "Radioactive-Spider-Man",
    "Rogue & Gambit": "Rogue-Gambit",
    "Rogue Storm": "Rogue-Storm",
    "Sabretooth & The Exiles": "Sabretooth-The-Exiles",
    "Sabretooth & the Exiles": "Sabretooth-the-Exiles",
    "The Last Wolverine": "The-Last-Wolverine",
    "Unbreakable X-Men": "Unbreakable-X-Men",
    "Uncanny Spider-Man": "Uncanny-Spider-Man",
    "Undeadpool": "Undeadpool",
    "X Deaths of Wolverine": "X-Deaths-of-Wolverine",
    "X Lives of Wolverine": "X-Lives-of-Wolverine",
    "X-Men Unlimited Infinity Comic": "X-Men-Unlimited-Infinity-Comic",
    "X-Men: Book of Revelation": "X-Men-Book-of-Revelation",
    "X-Men: The Trial of Magneto": "X-Men-The-Trial-of-Magneto",
    "Magik and Colossus": "Magik-and-Colossus",
    "X-Vengers": "X-Vengers",
    "Generation: X-23": "Generation-X-23",
    "Cyclops (2026)": "Cyclops-2026",
}

# ── One-shots / named paths: title → path after /Comic/ ────
SPECIAL_ISSUE_URL = {
    "Giant-Size X-Men: Jean Grey and Emma Frost": "Giant-Size-X-Men-2020/Jean-Grey-And-Emma-Frost",
    "Giant-Size X-Men: Nightcrawler": "Giant-Size-X-Men-2020/Nightcrawler",
    "Giant-Size X-Men: Magneto": "Giant-Size-X-Men-2020/Magneto",
    "Giant-Size X-Men: Fantomex": "Giant-Size-X-Men-2020/Giant-Size-X-Men-Fantomex",
    "Giant-Size X-Men: Storm": "Giant-Size-X-Men-2020/Full",
    "X of Swords: Stasis": "X-Of-Swords-Stasis/Full",
    "X of Swords: Destruction": "X-Of-Swords-Destruction/Full",
    "X-Men: The Onslaught Revelation": "X-Men-Onslaught-Revelation/Full",
    "A.X.E.: Judgment Day Omega": "A-X-E-Judgment-Day-Omega/Full",
    "X-Manhunt Omega": "X-Manhunt-Omega/Full",
    "Giant-Size Age of Apocalypse": "Giant-Size-Age-of-Apocalypse/Full",
    "Giant-Size Dark Phoenix Saga": "Giant-Size-Dark-Phoenix-Saga/Full",
    "Giant-Size House of M": "Giant-Size-House-of-M/Full",
    "Timeslide": "Timeslide/Full",
    "X-Men: Xavier's Secret": "X-Men-Xavier-s-Secret/Full",
    "X-Men: Demons and Death": "X-Men-From-the-Ashes-Demons-and-Death/Full",
    "X-Men: Age of Revelation Overture": "X-Men-Age-of-Revelation-Overture/Full",
    "X-Men: Age of Revelation Finale": "X-Men-Age-of-Revelation-Finale/Full",
    "World of Revelation": "World-of-Revelation/Full",
    "X-Men: Hellfire Vigil": "X-Men-Hellfire-Vigil/Full",
    "X-Men: Tooth and Claw": "X-Men-Tooth-and-Claw/Full",
    # ── Auto-added by find_slugs.py ──
    "Before the Fall: Heralds of Apocalypse": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=216472",
    "Before the Fall: Mutant First Strike": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=215834",
    "Before the Fall: Sinister Four": "X-Men-Before-the-Fall-Sons-of-X/The-Sinister-Four?id=216689",
    "Before the Fall: Sons of X": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=214579",
    "Cable: Reloaded": "Cable-Reloaded/Issue-1",
    "Dark Web": "Dark-Web-2023/TPB-Part-1",
    "Dark Web: Finale": "Dark-Web-Finale/Issue-1",
    "Death of Doctor Strange: X-Men/Black Knight": "Death-of-Doctor-Strange-One-Shots/X-Men-Black-Knight",
    "Ghost Rider/Wolverine: Weapons of Vengeance Alpha": "Ghost-Rider-Wolverine-Weapons-of-Vengeance-Alpha/Issue-1",
    "Ghost Rider/Wolverine: Weapons of Vengeance Omega": "Ghost-Rider-Wolverine-Weapons-of-Vengeance-Omega/Issue-1",
    "Giant-Size X-Men: Thunderbird": "Giant-Size-X-Men-Thunderbird/Issue-1",
    "King in Black: Marauders": "King-In-Black-One-Shots/Marauders",
    "Marauders Annual": "Marauders/Annual-1",
    "Marvel Voices: Community": "Marvel-s-Voices-Community/TPB",
    "Marvel Voices: Heritage": "Marvel-s-Voices-Heritage/Full",
    "Marvel Voices: Identity": "Marvel-s-Voices-Identity/Full",
    "Marvel Voices: Indigenous Voices": "Marvel-s-Voices-Indigenous-Voices/Full",
    "Marvel Voices: Legacy": "Marvel-s-Voices-Legacy/Full",
    "Marvel Voices: Pride": "Marvel-s-Voices-Pride-2022/Full",
    "Marvel's Voices: X-Men": "Marvel-s-Voices-X-Men/Issue-1",
    "Moonstar": "Moonstar/Issue-1",
    "Outlawed": "Outlawed/Full",
    "Planet-Size X-Men": "Planet-Size-X-Men/Issue-1",
    "Rogue (2026)": "Rogue-2026/Issue-1",
    "Sins of Sinister": "Sins-of-Sinister/Issue-1",
    "Sins of Sinister: Dominion": "Sins-Of-Sinister-Dominion/Issue-1",
    "Uncanny Avengers Annual (2023)": "Avengers-2023/Annual-1",
    "Wade Wilson: Deadpool": "Wade-Wilson-Deadpool/Issue-1",
    "X of Swords: Creation": "X-Of-Swords-Creation/Issue-1",
    "X-Force Annual": "X-Force-2019-2/Annual-1",
    "X-Men Annual (2022)": "X-Men-2021/Annual-1",
    "X-Men Blue: Origins": "X-Men-Blue-Origins/Full",
    "X-Men: Before the Fall - Heralds of Apocalypse": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=216472",
    "X-Men: Before the Fall - Mutant First Strike": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=215834",
    "X-Men: Before the Fall - Sinister Four": "X-Men-Before-the-Fall-Sons-of-X/The-Sinister-Four?id=216689",
    "X-Men: Before the Fall - Sons of X": "X-Men-Before-the-Fall-Sons-of-X/Issue-1?id=214579",
    "X-Men: Curse of the Man-Thing": "Curse-Of-The-Man-Thing/X-Men",
    "X-Men: Hellfire Gala (2022)": "X-Men-Hellfire-Gala/Issue-1",
    "X-Men: Hellfire Gala (2023)": "X-Men-Hellfire-Gala-2023/Issue-1",
    "X-Men: The Wedding Special": "X-Men-The-Wedding-Special/Full",
}

# ── Titles not available on the site ────────────────────────
UNAVAILABLE_TITLES = {
    "X-Men United",
    "X-Men: Hellfire Gala (2024)",
}


# ════════════════════════════════════════════════════════════
#  URL BUILDERS
# ════════════════════════════════════════════════════════════

def title_to_slug(title: str) -> str:
    """Convert a series title to its URL slug."""
    if title in SLUG_MAP:
        return SLUG_MAP[title]
    slug = re.sub(r'[^\w\s-]', '', title)
    slug = re.sub(r'[\s]+', '-', slug)
    return slug


def build_issue_url(title: str, issue: int) -> str | None:
    """Build the full scrape URL for an issue. Returns None if unavailable."""
    if title in SPECIAL_ISSUE_URL:
        path = SPECIAL_ISSUE_URL[title]
        sep = "&" if "?" in path else "?"
        return BASE_URL + "/Comic/" + path + sep + "quality=hq"
    if title in UNAVAILABLE_TITLES:
        return None
    return ISSUE_URL.format(slug=title_to_slug(title), issue=issue)


def build_comic_url(title: str) -> str:
    """Build the series overview URL (for browsing, not scraping)."""
    if title in SPECIAL_ISSUE_URL:
        slug = SPECIAL_ISSUE_URL[title].split("/")[0]
        return COMIC_URL.format(slug=slug)
    return COMIC_URL.format(slug=title_to_slug(title))


def safe_title(title: str) -> str:
    """Sanitize a title for use as a filesystem directory name."""
    return re.sub(r'[<>:"/\\|?*]', '_', title)
