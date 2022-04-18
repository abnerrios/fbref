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
from datetime import datetime
from fbref import FbrefDayMatches

fdm = FbrefDayMatches()
date = datetime.now().strftime('%Y-%m-%d')
day_matches = fdm.day_matches(date=date) #date format must be YYYY-MM-DD format

for match in day_matches:
  # return average stats for match squads
  print(match.describe(previous_matches=7))

  # -- export history data from squads
  # save data into a .csv file

  # -- match.home_stats
  # : params previous_matches: int 
  # : params competitions: str ['all', 'same'] 
  # : params venue: str ['home', 'away', 'any']

  home_team = match.home_stats(previous_matches=5, competitions='all' , venue='any')
  home_team.to_csv(f'{home_team.name}.csv')
  home_history = home_team.to_dict()

  away_team = match.away_stats(previous_matches=5, competitions='same' , venue='away')
  away_team.to_csv(f'{away_team.name}.csv')
  home_history = home_team.to_dict()

```