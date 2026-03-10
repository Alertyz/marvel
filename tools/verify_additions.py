import json

with open('data/reading_order.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

series_to_check = {
    'Excalibur': range(1,27),
    'X-Force': range(1,51),
    'Hellions': range(1,19),
    'S.W.O.R.D.': range(1,12),
    'Cable': range(1,13),
    'X-Men (2021)': range(1,36),
    'Immortal X-Men': range(1,19),
    'X-Men Red (2022)': range(1,19),
    'Legion of X': range(1,11),
    'New Mutants': range(1,34),
    'Invincible Iron Man': range(1,21),
    'Uncanny Avengers (2023)': range(1,6),
}

all_good = True
for series, expected_range in series_to_check.items():
    existing = set()
    for issue in data['issues']:
        if issue['title'] == series:
            existing.add(issue['issue'])
    missing = [i for i in expected_range if i not in existing]
    if missing:
        print(f'STILL MISSING - {series}: {missing}')
        all_good = False

new_series = [
    'Empyre: X-Men', 'King in Black: Marauders', 'X-Men: Curse of the Man-Thing',
    'Cable: Reloaded', "Devil's Reign: X-Men", 'Sabretooth & The Exiles',
    'X-Force Annual', 'Giant-Size X-Men: Thunderbird', 'X-Men: Hellfire Gala (2022)',
    'Marauders Annual', 'X-Men Annual (2022)', 'New Mutants: Lethal Legion',
    'Dark Web: X-Men', 'Before the Fall: Sons of X', 'Before the Fall: Heralds of Apocalypse',
    'Before the Fall: Sinister Four', "Marvel's Voices: X-Men",
    'Before the Fall: Mutant First Strike', 'Bishop: War College', 'Rogue & Gambit',
    'Uncanny Spider-Man', 'X-Men Blue: Origins', 'Ms. Marvel: Mutant Menace',
    'Ghost Rider/Wolverine: Weapons of Vengeance Alpha',
    'Ghost Rider/Wolverine: Weapons of Vengeance Omega',
    'X-Men: The Wedding Special'
]
existing_titles = set(issue['title'] for issue in data['issues'])
for title in new_series:
    if title not in existing_titles:
        print(f'STILL MISSING SERIES: {title}')
        all_good = False

if all_good:
    print('All gaps filled successfully!')
