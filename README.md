# fbref

`fbref` is a Python libary for pulling data out of [Fbref.com](https://fbref.com/matches).

# Installation from sources
In the `fbref` directory (same one where you found this file after cloning the git repo), execute:

```bash
python setup.py install
```

or installing in development mode:
```bash
pip install -e . --no-build-isolation --no-use-pep517
```

# Quick Start

```python
from fbref import FbrefDayMatches

fdm = FbrefDayMatches()
day_matches = fdm.day_matches(date='2022-03-13') #date format must be YYYY-MM-DD format

for match in day_matches:
  # return average stats for match squads
  print(match.describe())

  # -- export history data from squads
  # save data into a .csv file
  home_team = match.home_stats()
  home_team.to_csv(f'{home_team.name}.csv')
  home_history = home_team.to_dict()

  away_team = match.away_stats()
  away_team.to_csv(f'{away_team.name}.csv')
  home_history = home_team.to_dict()

```