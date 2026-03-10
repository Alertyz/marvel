"""
Script to add missing issues identified from ultimatexmenreadingorder.com
to the reading_order.json file.

Each insertion is defined as (after_order, list_of_issues) where after_order
is the ORIGINAL order number after which the new issues should be inserted.
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'reading_order.json')

def make_issue(title, issue, phase, event, year):
    entry = {
        "title": title,
        "issue": issue,
        "phase": phase,
        "event": event,
        "year": str(year),
    }
    return entry

# Define all insertions: (after_original_order, [list of new issue dicts])
# Issues will be inserted AFTER the issue with the given original order number.
insertions = [
    # ========== DAWN OF X ==========
    # X-Force #11-12: after Cable #4 (order 75)
    (75, [
        make_issue("X-Force", 11, "Dawn of X", "", "2020"),
        make_issue("X-Force", 12, "Dawn of X", "", "2020"),
    ]),
    # Empyre: X-Men #1-4: after X-Men #9 (order 94)
    (94, [
        make_issue("Empyre: X-Men", 1, "Dawn of X", "", "2020"),
        make_issue("Empyre: X-Men", 2, "Dawn of X", "", "2020"),
        make_issue("Empyre: X-Men", 3, "Dawn of X", "", "2020"),
        make_issue("Empyre: X-Men", 4, "Dawn of X", "", "2020"),
    ]),
    # Excalibur #9-11: after X-Men #11 (order 96)
    (96, [
        make_issue("Excalibur", 9, "Dawn of X", "", "2020"),
        make_issue("Excalibur", 10, "Dawn of X", "", "2020"),
        make_issue("Excalibur", 11, "Dawn of X", "", "2020"),
    ]),

    # ========== REIGN OF X ==========
    # Hellions #9-11: after Hellions #8 (order 125)
    (125, [
        make_issue("Hellions", 9, "Reign of X", "", "2021"),
        make_issue("Hellions", 10, "Reign of X", "", "2021"),
        make_issue("Hellions", 11, "Reign of X", "", "2021"),
    ]),
    # Excalibur #18-20: after Excalibur #17 (order 138)
    (138, [
        make_issue("Excalibur", 18, "Reign of X", "", "2021"),
        make_issue("Excalibur", 19, "Reign of X", "", "2021"),
        make_issue("Excalibur", 20, "Reign of X", "", "2021"),
    ]),
    # King in Black: Marauders #1: after S.W.O.R.D. #2 (order 142)
    (142, [
        make_issue("King in Black: Marauders", 1, "Reign of X", "", "2021"),
    ]),
    # S.W.O.R.D. #5 + X-Men: Curse of the Man-Thing: after S.W.O.R.D. #4 (order 144)
    (144, [
        make_issue("S.W.O.R.D.", 5, "Reign of X", "", "2021"),
        make_issue("X-Men: Curse of the Man-Thing", 1, "Reign of X", "", "2021"),
    ]),
    # Cable #11-12: after Cable #10 (order 157)
    (157, [
        make_issue("Cable", 11, "Reign of X", "", "2021"),
        make_issue("Cable", 12, "Reign of X", "", "2021"),
    ]),
    # Cable: Reloaded #1: after S.W.O.R.D. #7 (order 189)
    (189, [
        make_issue("Cable: Reloaded", 1, "Reign of X", "", "2021"),
    ]),
    # X-Men (2021) #4-8: after X-Men (2021) #3 (order 211)
    (211, [
        make_issue("X-Men (2021)", 4, "Reign of X", "", "2021"),
        make_issue("X-Men (2021)", 5, "Reign of X", "", "2022"),
        make_issue("X-Men (2021)", 6, "Reign of X", "", "2022"),
        make_issue("X-Men (2021)", 7, "Reign of X", "", "2022"),
        make_issue("X-Men (2021)", 8, "Reign of X", "", "2022"),
    ]),
    # Devil's Reign: X-Men #1-3: after S.W.O.R.D. #11 (order 222)
    (222, [
        make_issue("Devil's Reign: X-Men", 1, "Reign of X", "", "2022"),
        make_issue("Devil's Reign: X-Men", 2, "Reign of X", "", "2022"),
        make_issue("Devil's Reign: X-Men", 3, "Reign of X", "", "2022"),
    ]),

    # ========== DESTINY OF X ==========
    # Sabretooth & The Exiles #1-5: after Sabretooth #5 (order 255)
    (255, [
        make_issue("Sabretooth & The Exiles", 1, "Destiny of X", "", "2022"),
        make_issue("Sabretooth & The Exiles", 2, "Destiny of X", "", "2022"),
        make_issue("Sabretooth & The Exiles", 3, "Destiny of X", "", "2023"),
        make_issue("Sabretooth & The Exiles", 4, "Destiny of X", "", "2023"),
        make_issue("Sabretooth & The Exiles", 5, "Destiny of X", "", "2023"),
    ]),
    # X-Force Annual #1: after Secret X-Men #1 (order 256)
    (256, [
        make_issue("X-Force Annual", 1, "Destiny of X", "", "2022"),
    ]),
    # X-Force #30: after X-Force #29 (order 263)
    (263, [
        make_issue("X-Force", 30, "Destiny of X", "", "2022"),
    ]),
    # Immortal X-Men #4: after Immortal X-Men #3 (order 266)
    (266, [
        make_issue("Immortal X-Men", 4, "Destiny of X", "", "2022"),
    ]),
    # Giant-Size X-Men: Thunderbird #1: after X-Men Red (2022) #2 (order 268)
    (268, [
        make_issue("Giant-Size X-Men: Thunderbird", 1, "Destiny of X", "", "2022"),
    ]),
    # Marauders Annual #1: after Knights of X #5 (order 274)
    (274, [
        make_issue("Marauders Annual", 1, "Destiny of X", "", "2022"),
    ]),
    # X-Men: Hellfire Gala (2022) #1: after X-Men (2021) #12 (order 282)
    (282, [
        make_issue("X-Men: Hellfire Gala (2022)", 1, "Destiny of X", "Hellfire Gala 2022", "2022"),
    ]),
    # X-Men (2021) #13: after A.X.E.: Death to the Mutants #1 (order 301)
    (301, [
        make_issue("X-Men (2021)", 13, "Destiny of X", "A.X.E. Judgment Day", "2022"),
    ]),
    # X-Force #33: after X-Force #32 (order 307)
    (307, [
        make_issue("X-Force", 33, "Destiny of X", "A.X.E. Judgment Day", "2022"),
    ]),
    # Legion of X #6: after A.X.E.: Judgment Day #4 (order 311)
    (311, [
        make_issue("Legion of X", 6, "Destiny of X", "A.X.E. Judgment Day", "2022"),
    ]),
    # Post-AXE block: after Judgment Day Omega (order 318)
    (318, [
        make_issue("X-Men Annual (2022)", 1, "Destiny of X", "", "2022"),
        make_issue("X-Men Red (2022)", 8, "Destiny of X", "", "2022"),
        make_issue("X-Men Red (2022)", 9, "Destiny of X", "", "2023"),
        make_issue("X-Men Red (2022)", 10, "Destiny of X", "", "2023"),
        make_issue("New Mutants", 31, "Destiny of X", "", "2023"),
        make_issue("New Mutants", 32, "Destiny of X", "", "2023"),
        make_issue("New Mutants", 33, "Destiny of X", "", "2023"),
        make_issue("New Mutants: Lethal Legion", 1, "Destiny of X", "", "2023"),
        make_issue("New Mutants: Lethal Legion", 2, "Destiny of X", "", "2023"),
        make_issue("New Mutants: Lethal Legion", 3, "Destiny of X", "", "2023"),
        make_issue("New Mutants: Lethal Legion", 4, "Destiny of X", "", "2023"),
        make_issue("New Mutants: Lethal Legion", 5, "Destiny of X", "", "2023"),
    ]),
    # Dark Web: X-Men #1-3: after X-Terminators #5 (order 327)
    (327, [
        make_issue("Dark Web: X-Men", 1, "Destiny of X", "", "2023"),
        make_issue("Dark Web: X-Men", 2, "Destiny of X", "", "2023"),
        make_issue("Dark Web: X-Men", 3, "Destiny of X", "", "2023"),
    ]),
    # Legion of X #7-10: after X-Men (2021) #21 (order 330)
    (330, [
        make_issue("Legion of X", 7, "Destiny of X", "", "2023"),
        make_issue("Legion of X", 8, "Destiny of X", "", "2023"),
        make_issue("Legion of X", 9, "Destiny of X", "", "2023"),
        make_issue("Legion of X", 10, "Destiny of X", "", "2023"),
    ]),
    # Before the Fall: Sons of X #1: after Immortal X-Men #11 (order 356)
    (356, [
        make_issue("Before the Fall: Sons of X", 1, "Destiny of X", "", "2023"),
    ]),
    # Before the Fall: Heralds + Sinister Four: after X-Men (2021) #24 (order 385)
    (385, [
        make_issue("Before the Fall: Heralds of Apocalypse", 1, "Destiny of X", "", "2023"),
        make_issue("Before the Fall: Sinister Four", 1, "Destiny of X", "", "2023"),
    ]),

    # ========== FALL OF X ==========
    # Pre-Gala setup: after last Destiny of X issue (order 390)
    (390, [
        make_issue("Marvel's Voices: X-Men", 1, "Fall of X", "", "2023"),
        make_issue("Before the Fall: Mutant First Strike", 1, "Fall of X", "", "2023"),
        make_issue("Bishop: War College", 1, "Fall of X", "", "2023"),
        make_issue("Bishop: War College", 2, "Fall of X", "", "2023"),
        make_issue("Bishop: War College", 3, "Fall of X", "", "2023"),
        make_issue("Bishop: War College", 4, "Fall of X", "", "2023"),
        make_issue("Bishop: War College", 5, "Fall of X", "", "2023"),
        make_issue("Rogue & Gambit", 1, "Fall of X", "", "2023"),
        make_issue("Rogue & Gambit", 2, "Fall of X", "", "2023"),
        make_issue("Rogue & Gambit", 3, "Fall of X", "", "2023"),
        make_issue("Rogue & Gambit", 4, "Fall of X", "", "2023"),
        make_issue("Rogue & Gambit", 5, "Fall of X", "", "2023"),
    ]),
    # Uncanny Avengers #4-5: after #3 (order 418)
    (418, [
        make_issue("Uncanny Avengers (2023)", 4, "Fall of X", "", "2023"),
        make_issue("Uncanny Avengers (2023)", 5, "Fall of X", "", "2024"),
    ]),
    # Ms. Marvel: Mutant Menace #1-4: after Realm of X #4 (order 427)
    (427, [
        make_issue("Ms. Marvel: Mutant Menace", 1, "Fall of X", "", "2024"),
        make_issue("Ms. Marvel: Mutant Menace", 2, "Fall of X", "", "2024"),
        make_issue("Ms. Marvel: Mutant Menace", 3, "Fall of X", "", "2024"),
        make_issue("Ms. Marvel: Mutant Menace", 4, "Fall of X", "", "2024"),
    ]),
    # Uncanny Spider-Man + Blue Origins: after Dark X-Men #5 (order 441)
    (441, [
        make_issue("Uncanny Spider-Man", 1, "Fall of X", "", "2023"),
        make_issue("Uncanny Spider-Man", 2, "Fall of X", "", "2023"),
        make_issue("Uncanny Spider-Man", 3, "Fall of X", "", "2024"),
        make_issue("Uncanny Spider-Man", 4, "Fall of X", "", "2024"),
        make_issue("X-Men Blue: Origins", 1, "Fall of X", "", "2024"),
        make_issue("Uncanny Spider-Man", 5, "Fall of X", "", "2024"),
    ]),
    # Ghost Rider/Wolverine crossover: after X-Force #50 (order 450)
    (450, [
        make_issue("Ghost Rider/Wolverine: Weapons of Vengeance Alpha", 1, "Fall of X", "", "2023"),
        make_issue("Ghost Rider/Wolverine: Weapons of Vengeance Omega", 1, "Fall of X", "", "2023"),
    ]),
    # Invincible Iron Man #19-20: after #18 (order 496)
    (496, [
        make_issue("Invincible Iron Man", 19, "Fall of X", "Fall of the House of X", "2024"),
        make_issue("Invincible Iron Man", 20, "Fall of X", "", "2024"),
    ]),
    # Wedding Special: after X-Men (2021) #35 (order 506)
    (506, [
        make_issue("X-Men: The Wedding Special", 1, "Fall of X", "", "2024"),
    ]),
]


def main():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    issues = data['issues']

    # Build indexed list: (sort_key, issue_data)
    # Existing issues get integer sort keys matching their original order
    indexed = []
    for issue in issues:
        indexed.append((issue['order'], issue))

    # For each insertion, assign fractional sort keys so they sort
    # right after the target order number
    for after_order, new_issues in insertions:
        for i, new_issue in enumerate(new_issues):
            sort_key = after_order + 0.0001 * (i + 1)
            indexed.append((sort_key, new_issue))

    # Sort by sort key
    indexed.sort(key=lambda x: x[0])

    # Renumber sequentially
    final_issues = []
    for new_order, (_, issue_data) in enumerate(indexed, start=1):
        entry = {
            "order": new_order,
            "title": issue_data["title"],
            "issue": issue_data["issue"],
            "phase": issue_data["phase"],
            "event": issue_data["event"],
            "year": issue_data["year"],
        }
        # Preserve bookmark if present
        if issue_data.get("bookmark"):
            entry["bookmark"] = True
        final_issues.append(entry)

    # Count total
    total = len(final_issues)
    added = total - len(issues)

    # Build output
    output = {
        "bookmark_note": data["bookmark_note"],
        "eras": data["eras"],
        "total_issues": total,
        "issues": final_issues,
    }

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Done! Added {added} issues. Total: {total}")

    # Print summary of what was added
    print("\nAdded issues summary:")
    for after_order, new_issues in sorted(insertions, key=lambda x: x[0]):
        for ni in new_issues:
            print(f"  After #{after_order}: {ni['title']} #{ni['issue']} ({ni['phase']})")


if __name__ == '__main__':
    main()
