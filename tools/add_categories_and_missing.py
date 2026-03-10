"""
Script to:
1. Add 'category' field to all existing issues (essencial / recomendado / completista)
2. Rename "Hellverine" -> "Hellverine Vol 2" for existing entries
3. Add Hellverine Vol 1 (4 issues) in proper position
4. Add missing crossover issues (King in Black, Eternals, Death of Doctor Strange, etc.)
5. Add missing Infinity Comics / Digital comics
6. Renumber all orders sequentially
7. Update total_issues
"""

import json
import copy

INPUT = "data/reading_order.json"
OUTPUT = "data/reading_order.json"
BACKUP = "data/reading_order_backup_before_categories.json"

# ─── Category Definitions ───
# "essencial" = Main X-Men storyline, core series, required events
# "recomendado" = Interesting supplementary series, worth reading
# "completista" = Everything else: crossovers, infinity comics, digital, minor tie-ins

# Core series per phase that are ESSENTIAL
ESSENCIAL_SERIES = {
    "House of X / Powers of X": {
        "House of X", "Powers of X"
    },
    "Dawn of X": {
        "X-Men", "Marauders", "Excalibur", "New Mutants", "X-Force", "Wolverine",
        "X-Factor", "Hellions", "Cable",
        "X of Swords: Creation", "X of Swords: Stasis", "X of Swords: Destruction",
        "X-Men/Fantastic Four",
    },
    "Reign of X": {
        "X-Men", "Marauders", "Excalibur", "New Mutants", "X-Force", "Wolverine",
        "X-Factor", "Hellions", "S.W.O.R.D.", "X-Corp", "Way of X",
        "X-Men (2021)", "X-Men: The Trial of Magneto", "X-Men: The Onslaught Revelation",
        "Planet-Size X-Men", "Children of the Atom",
        "Inferno",
    },
    "Destiny of X": {
        "X-Men (2021)", "Immortal X-Men", "X-Men Red (2022)", "Wolverine", "X-Force",
        "New Mutants", "Legion of X", "Marauders (2022)", "Knights of X",
        "X Lives of Wolverine", "X Deaths of Wolverine", "Sabretooth",
        "A.X.E.: Eve of Judgment", "A.X.E.: Judgment Day", "A.X.E.: Death to the Mutants",
        "A.X.E.: Judgment Day Omega",
        "Sins of Sinister", "Sins of Sinister: Dominion",
        "Immoral X-Men", "Storm and the Brotherhood of Mutants", "Nightcrawlers",
        "X-Terminators", "Betsy Braddock: Captain Britain", "Secret X-Men",
    },
    "Fall of X": {
        "X-Men (2021)", "Immortal X-Men", "X-Men Red (2022)", "X-Force", "Wolverine",
        "Invincible Iron Man", "Uncanny Avengers (2023)",
        "Fall of the House of X", "Rise of the Powers of X",
        "Dead X-Men", "Resurrection of Magneto", "X-Men Forever (2024)",
        "Jean Grey", "Dark X-Men",
        "X-Men: Hellfire Gala (2023)",
        "Cable (2024)",
    },
    "From the Ashes": {
        "X-Men (2024)", "Uncanny X-Men (2024)", "X-Force (2024)", "Exceptional X-Men",
        "Wolverine (2024)", "Storm (2024)", "Phoenix", "NYX", "X-Factor (2024)",
        "Psylocke (2024)", "Laura Kinney: Wolverine", "Magik", "Weapon X-Men",
        "X-Manhunt Omega",
        "X-Men: Age of Revelation Overture", "X-Men: Age of Revelation Finale",
        "World of Revelation", "Amazing X-Men (2025)",
        "X-Men: Book of Revelation",
        "Giant-Size X-Men (2025)",
    },
    "Shadows of Tomorrow": {
        "X-Men (2024)", "Uncanny X-Men (2024)", "Wolverine (2024)",
        "X-Men United", "Inglorious X-Force", "Generation: X-23",
        "Storm: Earth's Mightiest Mutant",
    },
}

# Recommended (interesting but not strictly required)
RECOMENDADO_SERIES = {
    "Dawn of X": {
        "Fallen Angels",
        "Giant-Size X-Men: Jean Grey and Emma Frost",
        "Giant-Size X-Men: Nightcrawler",
        "Giant-Size X-Men: Magneto",
        "Giant-Size X-Men: Fantomex",
        "Giant-Size X-Men: Storm",
    },
    "Reign of X": set(),
    "Destiny of X": {
        "Invincible Iron Man",
    },
    "Fall of X": {
        "Children of the Vault (2023)", "Alpha Flight (2023)", "Realm of X",
        "Ms. Marvel: The New Mutant", "Astonishing Iceman",
    },
    "From the Ashes": {
        "Hellverine Vol 2", "Hellverine Vol 1",
        "Timeslide", "Deadpool/Wolverine",
        "Dazzler (2024)", "Mystique (2024)", "Sentinels (2024)",
        "Cable: Love and Chrome",
        "X-Men: Xavier's Secret", "X-Men: Hellfire Vigil",
        "X-Men: Tooth and Claw", "X-Men: Demons and Death",
        "Giant-Size Dark Phoenix Saga", "Giant-Size Age of Apocalypse",
        "Giant-Size House of M",
        "Binary", "Laura Kinney: Sabretooth", "Longshots",
        "Unbreakable X-Men", "Rogue Storm", "Iron & Frost",
        "Sinister's Six", "The Last Wolverine", "Omega Kids",
        "Radioactive Spider-Man", "Cloak or Dagger",
        "Expatriate X-Men", "Undeadpool", "X-Vengers",
    },
    "Shadows of Tomorrow": {
        "Wade Wilson: Deadpool", "Moonstar", "Magik and Colossus",
        "Cyclops (2026)", "Rogue (2026)",
    },
}


def categorize_existing(issue):
    """Determine category for an existing issue."""
    title = issue["title"]
    phase = issue["phase"]

    # Check essential
    ess = ESSENCIAL_SERIES.get(phase, set())
    if title in ess:
        return "essencial"

    # Check recommended
    rec = RECOMENDADO_SERIES.get(phase, set())
    if title in rec:
        return "recomendado"

    # Event tie-ins that are essential
    event = issue.get("event", "")
    if event in ("X of Swords", "Hellfire Gala 2021", "Hellfire Gala 2023",
                 "A.X.E. Judgment Day", "Sins of Sinister", "Inferno",
                 "Fall of the House of X", "X-Manhunt", "Raid on Graymalkin",
                 "Age of Revelation", "Giant-Size X-Men Anniversary"):
        # If it's an event tie-in and the series is in essential, already handled
        # Otherwise check if it's a core event book
        if title in ess:
            return "essencial"
        # Event tie-in issues from non-essential series are recommended
        return "recomendado"

    # Default: anything not classified
    return "completista"


def build_missing_issues():
    """
    Returns a list of new issues to insert, with approximate insertion points.
    Each entry: { ...issue_data..., "insert_after_order": N }
    where N is the order number after which to insert (-1 for renumber later)
    """
    new_issues = []

    # ═══════════════════════════════════════════════════
    # HELLVERINE VOL 1 (2024, 4 issues) - From the Ashes
    # Goes before Hellverine Vol 2 (currently orders 777-786)
    # ═══════════════════════════════════════════════════
    for i in range(1, 5):
        new_issues.append({
            "title": "Hellverine Vol 1",
            "issue": i,
            "phase": "From the Ashes",
            "event": "",
            "year": "2024",
            "category": "recomendado",
            "insert_after_order": 776  # before current Hellverine block
        })

    # ═══════════════════════════════════════════════════
    # CROSSOVERS NÃO-X (Dawn of X / Reign of X / Destiny of X)
    # ═══════════════════════════════════════════════════

    # --- King in Black tie-ins (Reign of X, 2021) ---
    # King in Black was a Venom event. Marauders #16 (order 128) ties in.
    # Insert King in Black: Marauders is already there. Add main event context:
    # King in Black #1-5 (completista, for context)
    for i in range(1, 6):
        new_issues.append({
            "title": "King in Black",
            "issue": i,
            "phase": "Reign of X",
            "event": "King in Black",
            "year": "2021",
            "category": "completista",
            "insert_after_order": 127  # before Marauders #16
        })

    # King in Black: Marauders #1 (completista)
    new_issues.append({
        "title": "King in Black: Marauders",
        "issue": 1,
        "phase": "Reign of X",
        "event": "King in Black",
        "year": "2021",
        "category": "completista",
        "insert_after_order": 132  # after King in Black, with other RoX issues
    })

    # --- Empyre tie-ins (Dawn of X, 2020) ---
    # Empyre: X-Men #1-4 (after X-Men #10, order ~95)
    for i in range(1, 5):
        new_issues.append({
            "title": "Empyre: X-Men",
            "issue": i,
            "phase": "Dawn of X",
            "event": "Empyre",
            "year": "2020",
            "category": "completista",
            "insert_after_order": 95
        })

    # --- Eternals tie-ins with AXE (Destiny of X, 2022) ---
    # Eternals #1-12 for AXE context
    for i in range(1, 13):
        new_issues.append({
            "title": "Eternals (2021)",
            "issue": i,
            "phase": "Destiny of X",
            "event": "",
            "year": "2022",
            "category": "completista",
            "insert_after_order": 295  # before AXE starts
        })

    # --- Death of Doctor Strange tie-in (Reign of X) ---
    # Death of Doctor Strange: X-Men/Black Knight #1
    new_issues.append({
        "title": "Death of Doctor Strange: X-Men/Black Knight",
        "issue": 1,
        "phase": "Reign of X",
        "event": "Death of Doctor Strange",
        "year": "2021",
        "category": "completista",
        "insert_after_order": 236  # end of Reign of X before Inferno
    })

    # --- S.W.O.R.D. #5 (King in Black) ---
    new_issues.append({
        "title": "S.W.O.R.D.",
        "issue": 5,
        "phase": "Reign of X",
        "event": "King in Black",
        "year": "2021",
        "category": "completista",
        "insert_after_order": 144  # after S.W.O.R.D. #4
    })

    # --- Dark Web crossover (Destiny of X, 2023) ---
    # Dark Web #1 (event one-shot)
    new_issues.append({
        "title": "Dark Web",
        "issue": 1,
        "phase": "Destiny of X",
        "event": "Dark Web",
        "year": "2023",
        "category": "completista",
        "insert_after_order": 321  # around X-Men (2021) #16
    })

    # Dark Web: X-Men #1-3
    for i in range(1, 4):
        new_issues.append({
            "title": "Dark Web: X-Men",
            "issue": i,
            "phase": "Destiny of X",
            "event": "Dark Web",
            "year": "2023",
            "category": "completista",
            "insert_after_order": 322 + i
        })

    # Dark Web: Finale #1
    new_issues.append({
        "title": "Dark Web: Finale",
        "issue": 1,
        "phase": "Destiny of X",
        "event": "Dark Web",
        "year": "2023",
        "category": "completista",
        "insert_after_order": 327
    })

    # --- Outlawed #1 (Dawn of X, 2020) ---
    # Tied to Champions / New Warriors mutant storyline
    new_issues.append({
        "title": "Outlawed",
        "issue": 1,
        "phase": "Dawn of X",
        "event": "",
        "year": "2020",
        "category": "completista",
        "insert_after_order": 67  # around New Mutants #11
    })

    # --- Champions #1-5 (Dawn of X, 2020) ---
    for i in range(1, 6):
        new_issues.append({
            "title": "Champions (2020)",
            "issue": i,
            "phase": "Dawn of X",
            "event": "",
            "year": "2020",
            "category": "completista",
            "insert_after_order": 68
        })

    # --- Sabretooth & the Exiles #1-5 (Destiny of X) ---
    for i in range(1, 6):
        new_issues.append({
            "title": "Sabretooth & the Exiles",
            "issue": i,
            "phase": "Destiny of X",
            "event": "",
            "year": "2023",
            "category": "completista",
            "insert_after_order": 356  # after Sins of Sinister: Dominion
        })

    # --- X-Men (2021) #4-8 (Reign of X, missing in sequence) ---
    # Already have X-Men (2021) #1-3 in Reign of X. Check #4-8
    # X-Men (2021) #4 = between issues, let me add
    for i in range(4, 9):
        new_issues.append({
            "title": "X-Men (2021)",
            "issue": i,
            "phase": "Reign of X",
            "event": "",
            "year": "2021",
            "category": "essencial",
            "insert_after_order": 211 + (i - 4)
        })

    # --- Wolverine/X-Force #30/33 crossover gap ---
    # X-Force #30 and #33 missing between existing
    new_issues.append({
        "title": "X-Force",
        "issue": 30,
        "phase": "Destiny of X",
        "event": "",
        "year": "2022",
        "category": "essencial",
        "insert_after_order": 263  # after X-Force #29
    })
    new_issues.append({
        "title": "X-Force",
        "issue": 33,
        "phase": "Destiny of X",
        "event": "",
        "year": "2022",
        "category": "essencial",
        "insert_after_order": 307  # after X-Force #32
    })

    # --- Excalibur #9-11 gap ---
    for i in range(9, 12):
        new_issues.append({
            "title": "Excalibur",
            "issue": i,
            "phase": "Dawn of X",
            "event": "",
            "year": "2020",
            "category": "essencial",
            "insert_after_order": 59 + (i - 9)
        })

    # --- X-Men: Before the Fall one-shots (Destiny of X, 2023) ---
    before_fall = [
        "X-Men: Before the Fall - Mutant First Strike",
        "X-Men: Before the Fall - Heralds of Apocalypse",
        "X-Men: Before the Fall - Sons of X",
        "X-Men: Before the Fall - Sinister Four",
    ]
    for idx, title in enumerate(before_fall):
        new_issues.append({
            "title": title,
            "issue": 1,
            "phase": "Destiny of X",
            "event": "",
            "year": "2023",
            "category": "recomendado",
            "insert_after_order": 390  # before Hellfire Gala 2023
        })

    # --- Invincible Iron Man #9 (missing between 8 and 10) ---
    new_issues.append({
        "title": "Invincible Iron Man",
        "issue": 9,
        "phase": "Fall of X",
        "event": "",
        "year": "2023",
        "category": "essencial",
        "insert_after_order": 394  # after #8
    })

    # --- Invincible Iron Man #19-20 ---
    new_issues.append({
        "title": "Invincible Iron Man",
        "issue": 19,
        "phase": "Fall of X",
        "event": "Fall of the House of X",
        "year": "2024",
        "category": "essencial",
        "insert_after_order": 496
    })
    new_issues.append({
        "title": "Invincible Iron Man",
        "issue": 20,
        "phase": "Fall of X",
        "event": "Fall of the House of X",
        "year": "2024",
        "category": "essencial",
        "insert_after_order": 497
    })

    # ═══════════════════════════════════════════════════
    # INFINITY COMICS / DIGITAL
    # ═══════════════════════════════════════════════════

    # X-Men Unlimited Infinity Comic #1-150 (Dawn of X through Destiny of X)
    # Adding in batches per era
    # Dawn of X batch: #1-10
    for i in range(1, 11):
        new_issues.append({
            "title": "X-Men Unlimited Infinity Comic",
            "issue": i,
            "phase": "Dawn of X",
            "event": "",
            "year": "2021",
            "category": "completista",
            "insert_after_order": 120  # end of Dawn of X
        })

    # Reign of X batch: #11-50
    for i in range(11, 51):
        new_issues.append({
            "title": "X-Men Unlimited Infinity Comic",
            "issue": i,
            "phase": "Reign of X",
            "event": "",
            "year": "2021",
            "category": "completista",
            "insert_after_order": 240  # end of Reign of X
        })

    # Destiny of X batch: #51-100
    for i in range(51, 101):
        new_issues.append({
            "title": "X-Men Unlimited Infinity Comic",
            "issue": i,
            "phase": "Destiny of X",
            "event": "",
            "year": "2022",
            "category": "completista",
            "insert_after_order": 390  # end of Destiny of X
        })

    # Destiny of X batch: #101-150
    for i in range(101, 151):
        new_issues.append({
            "title": "X-Men Unlimited Infinity Comic",
            "issue": i,
            "phase": "Destiny of X",
            "event": "",
            "year": "2023",
            "category": "completista",
            "insert_after_order": 390
        })

    # Marvel Voices: Indigenous Voices #1 (2020)
    new_issues.append({
        "title": "Marvel Voices: Indigenous Voices",
        "issue": 1,
        "phase": "Dawn of X",
        "event": "",
        "year": "2020",
        "category": "completista",
        "insert_after_order": 96
    })

    # Marvel Voices: Legacy #1 (2021)
    new_issues.append({
        "title": "Marvel Voices: Legacy",
        "issue": 1,
        "phase": "Reign of X",
        "event": "",
        "year": "2021",
        "category": "completista",
        "insert_after_order": 160
    })

    # Marvel Voices: Pride #1 (2021)
    new_issues.append({
        "title": "Marvel Voices: Pride",
        "issue": 1,
        "phase": "Reign of X",
        "event": "",
        "year": "2021",
        "category": "completista",
        "insert_after_order": 170
    })

    # Marvel Voices: Identity #1 (2021)
    new_issues.append({
        "title": "Marvel Voices: Identity",
        "issue": 1,
        "phase": "Reign of X",
        "event": "",
        "year": "2021",
        "category": "completista",
        "insert_after_order": 200
    })

    # Marvel Voices: Community #1 (2022)
    new_issues.append({
        "title": "Marvel Voices: Community",
        "issue": 1,
        "phase": "Destiny of X",
        "event": "",
        "year": "2022",
        "category": "completista",
        "insert_after_order": 260
    })

    # Marvel Voices: Heritage #1 (2022)
    new_issues.append({
        "title": "Marvel Voices: Heritage",
        "issue": 1,
        "phase": "Destiny of X",
        "event": "",
        "year": "2022",
        "category": "completista",
        "insert_after_order": 280
    })

    # Life of Wolverine Infinity Comic #1-6
    for i in range(1, 7):
        new_issues.append({
            "title": "Life of Wolverine Infinity Comic",
            "issue": i,
            "phase": "Reign of X",
            "event": "",
            "year": "2022",
            "category": "completista",
            "insert_after_order": 240
        })

    # Love Unlimited Infinity Comic (X-Men related) placeholder batch
    for i in range(1, 11):
        new_issues.append({
            "title": "Love Unlimited Infinity Comic",
            "issue": i,
            "phase": "Destiny of X",
            "event": "",
            "year": "2022",
            "category": "completista",
            "insert_after_order": 390
        })

    # X-Men: Hellfire Gala Guide #1 (2022) - completista
    new_issues.append({
        "title": "X-Men: Hellfire Gala (2022)",
        "issue": 1,
        "phase": "Destiny of X",
        "event": "Hellfire Gala 2022",
        "year": "2022",
        "category": "completista",
        "insert_after_order": 295  # between New Mutants #30 and AXE
    })

    # Realm of X #4 (if missing)
    # Sabretooth War specific issues from Wolverine are already included

    # Uncanny Avengers (2023) #4-5
    for i in range(4, 6):
        new_issues.append({
            "title": "Uncanny Avengers (2023)",
            "issue": i,
            "phase": "Fall of X",
            "event": "",
            "year": "2024",
            "category": "essencial",
            "insert_after_order": 418
        })

    # Uncanny Avengers (2023) Annual #1
    new_issues.append({
        "title": "Uncanny Avengers Annual (2023)",
        "issue": 1,
        "phase": "Fall of X",
        "event": "",
        "year": "2024",
        "category": "completista",
        "insert_after_order": 420
    })

    # X-Men (2021) #13 gap (between AXE issues)
    new_issues.append({
        "title": "X-Men (2021)",
        "issue": 13,
        "phase": "Destiny of X",
        "event": "A.X.E. Judgment Day",
        "year": "2022",
        "category": "essencial",
        "insert_after_order": 311
    })

    # X-Men Red (2022) #8-10 gap
    for i in range(8, 11):
        new_issues.append({
            "title": "X-Men Red (2022)",
            "issue": i,
            "phase": "Destiny of X",
            "event": "",
            "year": "2022",
            "category": "essencial",
            "insert_after_order": 318 + (i - 8)
        })

    # Immortal X-Men #4 gap
    new_issues.append({
        "title": "Immortal X-Men",
        "issue": 4,
        "phase": "Destiny of X",
        "event": "",
        "year": "2022",
        "category": "essencial",
        "insert_after_order": 266
    })

    # X-Men: Hellfire Gala 2024 #1
    new_issues.append({
        "title": "X-Men: Hellfire Gala (2024)",
        "issue": 1,
        "phase": "From the Ashes",
        "event": "Hellfire Gala 2024",
        "year": "2024",
        "category": "recomendado",
        "insert_after_order": 506  # after Fall of X ends
    })

    # Deadpool #6 (X-Men crossover, Dawn of X)
    new_issues.append({
        "title": "Deadpool",
        "issue": 6,
        "phase": "Dawn of X",
        "event": "",
        "year": "2020",
        "category": "completista",
        "insert_after_order": 76
    })

    # New Mutants #31-33 (Fall of X)
    for i in range(31, 34):
        new_issues.append({
            "title": "New Mutants",
            "issue": i,
            "phase": "Destiny of X",
            "event": "",
            "year": "2022",
            "category": "essencial",
            "insert_after_order": 295  # end of New Mutants in DoX
        })

    # Wolverine #50 Annual tie-in issues
    # Already have up to Wolverine #50

    return new_issues


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Backup
    with open(BACKUP, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Backup saved to {BACKUP}")

    issues = data["issues"]

    # ── Step 1: Rename Hellverine → Hellverine Vol 2 ──
    for issue in issues:
        if issue["title"] == "Hellverine":
            issue["title"] = "Hellverine Vol 2"
    print("Renamed 'Hellverine' -> 'Hellverine Vol 2'")

    # ── Step 2: Categorize all existing issues ──
    for issue in issues:
        issue["category"] = categorize_existing(issue)

    cats = {}
    for i in issues:
        c = i["category"]
        cats[c] = cats.get(c, 0) + 1
    print(f"Categorized existing issues: {cats}")

    # ── Step 3: Build new issues ──
    new_issues = build_missing_issues()
    print(f"New issues to add: {len(new_issues)}")

    # ── Step 4: Check for duplicates before inserting ──
    existing_set = set()
    for i in issues:
        existing_set.add((i["title"], i["issue"]))

    added = 0
    skipped = 0
    insertions = []  # (insert_after_order, issue_data)
    for ni in new_issues:
        key = (ni["title"], ni["issue"])
        if key in existing_set:
            skipped += 1
            continue
        existing_set.add(key)
        order_ref = ni.pop("insert_after_order")
        insertions.append((order_ref, ni))
        added += 1

    print(f"Will add {added} issues (skipped {skipped} duplicates)")

    # ── Step 5: Insert new issues ──
    # Sort insertions by reference order (descending) so we insert from end to start
    # to avoid shifting issues
    insertions.sort(key=lambda x: x[0], reverse=True)

    for ref_order, new_issue in insertions:
        # Find the index of the issue with this order
        idx = None
        for j, iss in enumerate(issues):
            if iss["order"] == ref_order:
                idx = j
                break
        if idx is None:
            # Find closest order <= ref_order
            idx = 0
            for j, iss in enumerate(issues):
                if iss["order"] <= ref_order:
                    idx = j
            # Insert after this index
        issues.insert(idx + 1, new_issue)

    # ── Step 6: Renumber all orders sequentially ──
    for idx, issue in enumerate(issues):
        issue["order"] = idx + 1

    # ── Step 7: Update totals ──
    data["total_issues"] = len(issues)
    data["issues"] = issues

    # Add category descriptions
    data["categories"] = {
        "essencial": "Historia principal e series obrigatorias. O minimo para entender a saga completa dos X-Men.",
        "recomendado": "Series interessantes que complementam e enriquecem a historia principal.",
        "completista": "Tudo - crossovers, infinity comics, digital, one-shots. Para quem nao quer perder nada."
    }

    # ── Step 8: Save ──
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ── Stats ──
    final_cats = {}
    for i in data["issues"]:
        c = i["category"]
        final_cats[c] = final_cats.get(c, 0) + 1

    print(f"\n=== RESULTADO FINAL ===")
    print(f"Total de issues: {len(data['issues'])}")
    print(f"Categorias:")
    for cat, count in sorted(final_cats.items()):
        print(f"  {cat}: {count}")

    # Check bookmark still exists
    bm = [i for i in data["issues"] if i.get("bookmark")]
    if bm:
        print(f"Bookmark preservado: order {bm[0]['order']} - {bm[0]['title']} #{bm[0]['issue']}")
    else:
        print("WARNING: Bookmark lost!")


if __name__ == "__main__":
    main()
