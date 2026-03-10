#!/usr/bin/env python3
"""Generate reading_order.json for the complete X-Men mutant saga."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "reading_order.json"

issues = []
n = 0

def add(title, issue, phase, event="", year=""):
    global n
    n += 1
    issues.append({"order": n, "title": title, "issue": issue, "phase": phase, "event": event, "year": year})

# ============================================================
# ERA 1: KRAKOA (2019-2024)
# ============================================================

# --- HOUSE OF X / POWERS OF X ---
P, E = "House of X / Powers of X", ""
for t, i in [("House of X",1),("Powers of X",1),("House of X",2),("Powers of X",2),("Powers of X",3),
             ("House of X",3),("House of X",4),("Powers of X",4),("House of X",5),("Powers of X",5),
             ("House of X",6),("Powers of X",6)]:
    add(t, i, P, year="2019")

# --- DAWN OF X ---
P = "Dawn of X"
for t,i in [("X-Men",1),("Marauders",1),("Excalibur",1),("New Mutants",1),("X-Force",1),("Fallen Angels",1)]:
    add(t,i,P,year="2019")
for t,i in [("Marauders",2),("Marauders",3),("Excalibur",2),("Excalibur",3),("X-Men",2),("X-Men",3),
            ("New Mutants",2),("New Mutants",3),("New Mutants",4),("X-Force",2),("X-Force",3),
            ("Fallen Angels",2),("Fallen Angels",3),("Fallen Angels",4),("Marauders",4),("X-Men",4),
            ("Excalibur",4),("Excalibur",5),("New Mutants",5),("Fallen Angels",5),("Fallen Angels",6),
            ("X-Force",4),("X-Force",5),("Marauders",5),("Marauders",6),("New Mutants",6),("X-Men",5),
            ("Excalibur",6),("X-Force",6)]:
    add(t,i,P,year="2020")
for t,i in [("X-Men/Fantastic Four",1),("X-Men/Fantastic Four",2),("X-Men/Fantastic Four",3),("X-Men/Fantastic Four",4)]:
    add(t,i,P,year="2020")
for t,i in [("Marauders",7),("Giant-Size X-Men: Jean Grey and Emma Frost",1),("New Mutants",7),("New Mutants",8),
            ("X-Force",7),("X-Force",8),("Excalibur",7),("Excalibur",8),("Marauders",8),("X-Men",6),
            ("Wolverine",1),("Wolverine",2),("Wolverine",3),("Cable",1),("New Mutants",9),("New Mutants",10),
            ("New Mutants",11),("X-Force",9),("X-Force",10),("Marauders",9),("Marauders",10),("Cable",2),
            ("Cable",3),("Cable",4),("X-Men",7),("X-Men",8),("X-Factor",1),("Hellions",1),("Hellions",2),
            ("Hellions",3),("Hellions",4),("Giant-Size X-Men: Nightcrawler",1),("Wolverine",4),("Wolverine",5),
            ("X-Factor",2),("X-Factor",3),("Marauders",11),("Marauders",12),("Giant-Size X-Men: Magneto",1),
            ("New Mutants",12),("Giant-Size X-Men: Fantomex",1),("Giant-Size X-Men: Storm",1),
            ("X-Men",9),("X-Men",10),("X-Men",11)]:
    add(t,i,P,year="2020")

# --- X OF SWORDS ---
P, EV = "Dawn of X", "X of Swords"
for t,i in [("Excalibur",12),("X-Men",12),("X of Swords: Creation",1),("X-Factor",4),("Wolverine",6),
            ("X-Force",13),("Marauders",13),("Hellions",5),("New Mutants",13),("Cable",5),("Excalibur",13),
            ("X-Men",13),("X of Swords: Stasis",1),("X-Men",14),("Marauders",14),("Marauders",15),
            ("Excalibur",14),("Wolverine",7),("X-Force",14),("Hellions",6),("Cable",6),("X-Men",15),
            ("Excalibur",15),("X of Swords: Destruction",1)]:
    add(t,i,P,EV,year="2020")

# --- REIGN OF X ---
P = "Reign of X"
for t,i in [("X-Men",16),("S.W.O.R.D.",1),("X-Factor",5),("Hellions",7),("Hellions",8),
            ("New Mutants",14),("New Mutants",15),("Marauders",16),("X-Force",15),("X-Force",16),
            ("Cable",7),("Cable",8),("Wolverine",8),("Wolverine",9),("Wolverine",10),("Marauders",17),
            ("Excalibur",16),("Excalibur",17),("X-Factor",6),("X-Factor",7),("X-Factor",8),
            ("S.W.O.R.D.",2),("S.W.O.R.D.",3),("S.W.O.R.D.",4),("New Mutants",16),("New Mutants",17),
            ("X-Men",17),("Children of the Atom",1),("Children of the Atom",2),("Children of the Atom",3),
            ("Marauders",18),("Marauders",19),("X-Force",17),("X-Force",18),("X-Force",19),
            ("Cable",9),("Cable",10),("Wolverine",11),("Wolverine",12),("X-Men",18),("X-Men",19),
            ("X-Men",20),("X-Corp",1),("New Mutants",18),("Children of the Atom",4),("Children of the Atom",5),
            ("X-Factor",9),("Way of X",1),("Way of X",2),("Marauders",20)]:
    add(t,i,P,year="2021")

# --- HELLFIRE GALA 2021 ---
EV = "Hellfire Gala 2021"
for t,i in [("Marauders",21),("X-Force",20),("Hellions",12),("X-Corp",2),("X-Men",21),("Excalibur",21),
            ("Planet-Size X-Men",1),("Wolverine",13),("New Mutants",19),("Children of the Atom",6),
            ("S.W.O.R.D.",6),("Way of X",3),("X-Factor",10)]:
    add(t,i,P,EV,year="2021")

# --- POST-GALA REIGN OF X ---
EV = ""
for t,i in [("New Mutants",20),("New Mutants",21),("New Mutants",22),("New Mutants",23),("Marauders",22),
            ("S.W.O.R.D.",7),("Wolverine",14),("Wolverine",15),("Wolverine",16),("Marauders",23),
            ("X-Men (2021)",1),("X-Men: The Trial of Magneto",1),("X-Men: The Trial of Magneto",2),
            ("X-Men: The Trial of Magneto",3),("X-Men: The Trial of Magneto",4),("X-Men: The Trial of Magneto",5),
            ("Hellions",13),("Hellions",14),("Hellions",15),("Hellions",16),("Hellions",17),("Hellions",18),
            ("New Mutants",24),("X-Corp",3),("X-Corp",4),("X-Corp",5),("X-Men (2021)",2),("X-Men (2021)",3),
            ("Way of X",4),("Way of X",5),("X-Men: The Onslaught Revelation",1),
            ("Marauders",24),("Marauders",25),("Marauders",26),("Marauders",27),
            ("S.W.O.R.D.",8),("S.W.O.R.D.",9),("S.W.O.R.D.",10),("S.W.O.R.D.",11),
            ("Wolverine",17),("Wolverine",18),("Wolverine",19),
            ("X-Force",21),("X-Force",22),("X-Force",23),("X-Force",24),("X-Force",25),("X-Force",26),
            ("Excalibur",22),("Excalibur",23),("Excalibur",24),("Excalibur",25),("Excalibur",26)]:
    add(t,i,P,year="2021")

# --- INFERNO ---
EV = "Inferno"
for t,i in [("Inferno",1),("Inferno",2),("Inferno",3),("Inferno",4)]:
    add(t,i,P,EV,year="2022")

# --- DESTINY OF X ---
P = "Destiny of X"
for t,i in [("X Lives of Wolverine",1),("X Deaths of Wolverine",1),("X Lives of Wolverine",2),
            ("X Deaths of Wolverine",2),("X Lives of Wolverine",3),("X Deaths of Wolverine",3),
            ("X Lives of Wolverine",4),("X Deaths of Wolverine",4),("X Lives of Wolverine",5),
            ("X Deaths of Wolverine",5)]:
    add(t,i,P,year="2022")
for t,i in [("Sabretooth",1),("Sabretooth",2),("Sabretooth",3),("Sabretooth",4),("Sabretooth",5),
            ("Secret X-Men",1),("Wolverine",20),("Wolverine",21),("Wolverine",22),("Wolverine",23),
            ("X-Force",27),("X-Force",28),("X-Force",29),
            ("Immortal X-Men",1),("Immortal X-Men",2),("Immortal X-Men",3),
            ("X-Men Red (2022)",1),("X-Men Red (2022)",2),("X-Men Red (2022)",3),
            ("Knights of X",1),("Knights of X",2),("Knights of X",3),("Knights of X",4),("Knights of X",5),
            ("Marauders (2022)",1),("Marauders (2022)",2),("Marauders (2022)",3),("Marauders (2022)",4),
            ("X-Men (2021)",9),("X-Men (2021)",10),("X-Men (2021)",11),("X-Men (2021)",12),
            ("X-Men Red (2022)",4),("Marauders (2022)",5),
            ("Legion of X",1),("Legion of X",2),("Legion of X",3),("Legion of X",4),("Legion of X",5),
            ("New Mutants",25),("New Mutants",26),("New Mutants",27),("New Mutants",28),("New Mutants",29),("New Mutants",30)]:
    add(t,i,P,year="2022")

# --- A.X.E. JUDGMENT DAY ---
EV = "A.X.E. Judgment Day"
for t,i in [("A.X.E.: Eve of Judgment",1),("A.X.E.: Judgment Day",1),("Immortal X-Men",5),("X-Men Red (2022)",5),
            ("A.X.E.: Judgment Day",2),("A.X.E.: Death to the Mutants",1),
            ("A.X.E.: Judgment Day",3),("A.X.E.: Death to the Mutants",2),("Immortal X-Men",6),("X-Men Red (2022)",6),
            ("X-Force",31),("X-Force",32),("Wolverine",24),("Wolverine",25),("Marauders (2022)",6),
            ("A.X.E.: Judgment Day",4),("X-Men (2021)",14),("A.X.E.: Judgment Day",5),("A.X.E.: Death to the Mutants",3),
            ("Immortal X-Men",7),("X-Men Red (2022)",7),("A.X.E.: Judgment Day",6),("A.X.E.: Judgment Day Omega",1)]:
    add(t,i,P,EV,year="2022")

# --- POST-JUDGMENT DAY ---
EV = ""
for t,i in [("X-Men (2021)",15),("X-Men (2021)",16),("X-Men (2021)",17),("X-Men (2021)",18),
            ("X-Terminators",1),("X-Terminators",2),("X-Terminators",3),("X-Terminators",4),("X-Terminators",5),
            ("X-Men (2021)",19),("X-Men (2021)",20),("X-Men (2021)",21),
            ("Marauders (2022)",7),("Marauders (2022)",8),("Marauders (2022)",9),("Marauders (2022)",10),
            ("Marauders (2022)",11),("Marauders (2022)",12),
            ("Betsy Braddock: Captain Britain",1),("Betsy Braddock: Captain Britain",2),
            ("Betsy Braddock: Captain Britain",3),("Betsy Braddock: Captain Britain",4),
            ("Betsy Braddock: Captain Britain",5)]:
    add(t,i,P,year="2023")

# --- SINS OF SINISTER ---
EV = "Sins of Sinister"
for t,i in [("Immortal X-Men",8),("Immortal X-Men",9),("Immortal X-Men",10),
            ("Sins of Sinister",1),("Storm and the Brotherhood of Mutants",1),("Nightcrawlers",1),
            ("Immoral X-Men",1),("Nightcrawlers",2),("Immoral X-Men",2),
            ("Storm and the Brotherhood of Mutants",2),("Immoral X-Men",3),
            ("Storm and the Brotherhood of Mutants",3),("Nightcrawlers",3),
            ("Sins of Sinister: Dominion",1),("Immortal X-Men",11)]:
    add(t,i,P,EV,year="2023")

# --- BEFORE THE FALL ---
EV = ""
for t,i in [("Wolverine",26),("Wolverine",27),("X-Force",34),("X-Force",35),("X-Force",36),("X-Force",37),("X-Force",38),
            ("Wolverine",28),("Wolverine",29),("Wolverine",30),("Wolverine",31),
            ("X-Force",39),("X-Force",40),("X-Force",41),("X-Force",42),("Wolverine",32),("Wolverine",33),
            ("Wolverine",34),("Wolverine",35),
            ("Invincible Iron Man",1),("Invincible Iron Man",2),("Invincible Iron Man",3),
            ("Invincible Iron Man",4),("Invincible Iron Man",5),("Invincible Iron Man",6),("Invincible Iron Man",7),
            ("X-Men (2021)",22),("X-Men (2021)",23),("X-Men (2021)",24),
            ("Immortal X-Men",12),("Immortal X-Men",13),
            ("X-Men Red (2022)",11),("X-Men Red (2022)",12),("X-Men Red (2022)",13)]:
    add(t,i,P,year="2023")

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# BOOKMARK: USER STOPPED HERE (2nd Hellfire Gala)
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# --- HELLFIRE GALA 2023 / FALL OF X ---
P = "Fall of X"
EV = "Hellfire Gala 2023"
add("X-Men: Hellfire Gala (2023)", 1, P, EV, year="2023")
# Mark the bookmark
issues[-1]["bookmark"] = True

EV = ""
for t,i in [("X-Force",43),("Invincible Iron Man",8),("Invincible Iron Man",9),("X-Men (2021)",25),
            ("X-Men Red (2022)",14),("Immortal X-Men",14),("Immortal X-Men",15),("X-Men Red (2022)",15),
            ("Uncanny Avengers (2023)",1),("Children of the Vault (2023)",1),
            ("Dark X-Men",1),("Astonishing Iceman",1),("Alpha Flight (2023)",1),("Realm of X",1),
            ("Ms. Marvel: The New Mutant",1),("Ms. Marvel: The New Mutant",2),
            ("Ms. Marvel: The New Mutant",3),("Ms. Marvel: The New Mutant",4),
            ("Children of the Vault (2023)",2),("Children of the Vault (2023)",3),("Children of the Vault (2023)",4),
            ("Uncanny Avengers (2023)",2),("Uncanny Avengers (2023)",3),
            ("Dark X-Men",2),("Dark X-Men",3),
            ("Alpha Flight (2023)",2),("Alpha Flight (2023)",3),("Alpha Flight (2023)",4),("Alpha Flight (2023)",5),
            ("Realm of X",2),("Realm of X",3),("Realm of X",4),
            ("Immortal X-Men",16),("X-Men (2021)",26),("X-Men (2021)",27),("X-Men (2021)",28),("X-Men (2021)",29),
            ("X-Men Red (2022)",16),("X-Men Red (2022)",17),("X-Men Red (2022)",18),
            ("Jean Grey",1),("Jean Grey",2),("Jean Grey",3),("Jean Grey",4),
            ("Dark X-Men",4),("Dark X-Men",5),
            ("Immortal X-Men",17),("Immortal X-Men",18),
            ("X-Force",44),("X-Force",45),("X-Force",46),("X-Force",47),("X-Force",48),("X-Force",49),("X-Force",50),
            ("Wolverine",36),("Wolverine",37),("Wolverine",38),("Wolverine",39),("Wolverine",40),
            ("Wolverine",41),("Wolverine",42),("Wolverine",43),("Wolverine",44),("Wolverine",45),
            ("Wolverine",46),("Wolverine",47),("Wolverine",48),("Wolverine",49),("Wolverine",50),
            ("Cable (2024)",1),("Cable (2024)",2),("Cable (2024)",3),("Cable (2024)",4),
            ("Invincible Iron Man",10),("Invincible Iron Man",11),("Invincible Iron Man",12),
            ("Invincible Iron Man",13),("Invincible Iron Man",14),("X-Men (2021)",30)]:
    add(t,i,P,year="2023")

# --- FALL OF THE HOUSE OF X / RISE OF THE POWERS OF X ---
EV = "Fall of the House of X"
for t,i in [("Fall of the House of X",1),("Rise of the Powers of X",1),
            ("Invincible Iron Man",15),("Invincible Iron Man",16),
            ("Dead X-Men",1),("X-Men (2021)",31),("X-Men (2021)",32),
            ("Fall of the House of X",2),("Rise of the Powers of X",2),
            ("Resurrection of Magneto",1),("Resurrection of Magneto",2),
            ("Fall of the House of X",3),("Rise of the Powers of X",3),
            ("Dead X-Men",2),("Dead X-Men",3),
            ("Resurrection of Magneto",3),("Resurrection of Magneto",4),
            ("Dead X-Men",4),("X-Men Forever (2024)",1),
            ("Invincible Iron Man",17),("Invincible Iron Man",18),
            ("X-Men (2021)",33),
            ("Fall of the House of X",4),("Rise of the Powers of X",4),
            ("X-Men Forever (2024)",2),("X-Men Forever (2024)",3),("X-Men Forever (2024)",4),
            ("X-Men (2021)",34),
            ("Fall of the House of X",5),("Rise of the Powers of X",5),
            ("X-Men (2021)",35)]:
    add(t,i,P,EV,year="2024")

# ============================================================
# ERA 2: FROM THE ASHES (2024-2025)
# ============================================================
P = "From the Ashes"
for t,i in [("X-Men (2024)",1),("Phoenix",1),("NYX",1),("X-Force (2024)",1),
            ("Uncanny X-Men (2024)",1),("X-Factor (2024)",1),
            ("Exceptional X-Men",1),("Wolverine (2024)",1),("Storm (2024)",1)]:
    add(t,i,P,year="2024")
# Ongoing launches
for t,i in [("Dazzler (2024)",1),("Mystique (2024)",1),("Sentinels (2024)",1),
            ("Psylocke (2024)",1),("Laura Kinney: Wolverine",1)]:
    add(t,i,P,year="2024")
# Continue core titles through early issues
for num in range(2,9):
    add("X-Men (2024)",num,P,year="2024")
for num in range(2,8):
    add("Uncanny X-Men (2024)",num,P,year="2024")
for num in range(2,7):
    add("Phoenix",num,P,year="2024")
for num in range(2,7):
    add("NYX",num,P,year="2024")
for num in range(2,7):
    add("X-Force (2024)",num,P,year="2024")
for num in range(2,6):
    add("Exceptional X-Men",num,P,year="2024")
for num in range(2,6):
    add("Wolverine (2024)",num,P,year="2024")
for num in range(2,5):
    add("Storm (2024)",num,P,year="2024")
for num in range(2,5):
    add("X-Factor (2024)",num,P,year="2024")

# Raid on Graymalkin crossover
EV = "Raid on Graymalkin"
for t,i in [("X-Men (2024)",8),("Uncanny X-Men (2024)",7),("X-Men (2024)",9),("Uncanny X-Men (2024)",8)]:
    add(t,i,P,EV,year="2024")

# 2025 titles
EV = ""
add("Magik",1,P,year="2025")
add("Weapon X-Men",1,P,year="2025")

# X-Manhunt crossover
EV = "X-Manhunt"
for t,i in [("Uncanny X-Men (2024)",11),("NYX",9),("Storm (2024)",6),("X-Men (2024)",13),
            ("X-Factor (2024)",8),("X-Force (2024)",9),("Exceptional X-Men",7),("X-Manhunt Omega",1)]:
    add(t,i,P,EV,year="2025")

# Continue remaining issues
EV = ""
for num in range(14,20):
    add("X-Men (2024)",num,P,year="2025")
for num in range(12,18):
    add("Uncanny X-Men (2024)",num,P,year="2025")
for num in range(8,16):
    add("Phoenix",num,P,year="2025")
for num in range(6,13):
    add("Storm (2024)",num,P,year="2025")
for num in range(6,14):
    add("Exceptional X-Men",num,P,year="2025")
for num in range(6,11):
    add("Wolverine (2024)",num,P,year="2025")
for num in range(2,11):
    add("Magik",num,P,year="2025")
for num in range(2,6):
    add("Weapon X-Men",num,P,year="2025")
for num in range(2,11):
    add("Psylocke (2024)",num,P,year="2025")
for num in range(2,11):
    add("Laura Kinney: Wolverine",num,P,year="2025")

# ============================================================
# ERA 3: SHADOWS OF TOMORROW (2026+)
# ============================================================
P = "Shadows of Tomorrow"
for t,i in [("X-Men (2024)",21),("Uncanny X-Men (2024)",19),("Wolverine (2024)",11),
            ("X-Men United",1),("Inglorious X-Force",1),("Generation: X-23",1),
            ("Wade Wilson: Deadpool",1),("Moonstar",1),("Storm: Earth's Mightiest Mutant",1),
            ("Magik and Colossus",1)]:
    add(t,i,P,year="2026")

# Save
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump({"bookmark_note": "User stopped at the 2nd Hellfire Gala (2023). Issues with bookmark=true mark the stopping point.",
               "eras": ["House of X / Powers of X", "Dawn of X", "Reign of X", "Destiny of X", "Fall of X", "From the Ashes", "Shadows of Tomorrow"],
               "total_issues": len(issues),
               "issues": issues}, f, indent=2, ensure_ascii=False)

print(f"Generated {len(issues)} issues in {OUTPUT_PATH}")
