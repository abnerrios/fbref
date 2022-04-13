from urllib.parse import urljoin
import requests
import re
import json
import csv
from bs4 import BeautifulSoup
from datetime import datetime
from handlers import PreviousMatchHandlers


class ScheduledMatches:
    r"""``Matches`` allows you to collect all matches of the day from `fbref.com`.

        See following example:

            matches = Matches()

            matches.day_matches('YYYY-MM-DD')

    """
    def _handle_date(self, date) -> str:
        
        if not date:
            return datetime.now().strftime('YYYY-MM-DD')

    def day_matches(self, date) -> list:
        """Return matches from specified date.

        :params date: 'YYYY-MM-DD'
        """
        date = self._handle_date(date)
        rsp = requests.request('GET', f'https://fbref.com/en/matches/{date}')
        content = rsp.content
        day_matches = []

        if rsp.status_code < 400:
            soup = BeautifulSoup(content, 'html.parser')
            all_sched_tables = soup.find_all('div', attrs={'id': re.compile('all_sched_\\d+')})

            for sched_table in all_sched_tables:
                competition = sched_table.find('h2').find('a').text
                tbody = sched_table.find('tbody')
                rows = tbody.find_all('tr')

                for row in rows:
                    match = ScheduledMatch()
                    data = row.find_all('td')
                    match_dict = {stat.attrs['data-stat']: stat for stat in data}

                    # set match attributes
                    match.competition = competition
                    match.date = match_dict.get('time').text
                    match.home = match_dict.get('squad_a').text
                    match.away = match_dict.get('squad_b').text
                    match.score = match_dict.get('score').text
                    match.venue = match_dict.get('venue').text

                    # parse name when country comes first
                    match.away = re.sub('^[a-z]+\s', '', match.away)
                    match.home = re.sub('\s+[a-z]{2}$', '', match.home)

                    home_a = match_dict.get('squad_a').find('a')
                    away_a = match_dict.get('squad_b').find('a')

                    match._home_ref = home_a.attrs.get('href')
                    match._away_ref = away_a.attrs.get('href')

                    day_matches.append(match)
        else:
            raise AttributeError(f"Can't collect matches. See error:\n {rsp.text}")

        return day_matches


class PreviousMatch:
    def __init__(self) -> None:
        self.time = str
        self.competition = str
        self.result = str
        self.venue = str
        self.opponent = str
        self.goals_for = int
        self.goals_against = int
        self.formation = str
        self.possession = str
        self.captain = str
        self.corners = str
        self.shots = int
        self.shots_on_target = int
        self.offsides = int
        self.fouls = int
        self.match_summary = dict


class Squad(PreviousMatchHandlers):
    def __init__(self, name, competition, venue) -> None:
        super().__init__()
        self.name = re.sub('\s+[a-z]{2}$', '', name)
        self._competition = competition
        self._venue = venue
        self.history = []

    def match_summary(self, href, previous_matches, competitions, venue) -> None:
        VALID_COMPETITIONS = ['all', 'same']
        VALID_VENUES = ['home', 'away', 'any']

        if competitions.lower() not in VALID_COMPETITIONS:
            raise ValueError("competitions: status must be one of %r." % VALID_COMPETITIONS)

        if venue.lower() not in VALID_VENUES:
            raise ValueError("venue: status must be one of %r." % VALID_VENUES)

        squad_url = urljoin('https://fbref.com', href)
        previous_matches = self._handle_previous_matches(squad_url, previous_matches)

        for match in previous_matches:
            previous_match = PreviousMatch()
            previous_match.time = match.get('time').text
            previous_match.competition = match.get('comp').text
            previous_match.result = match.get('result').text
            previous_match.venue = match.get('venue').text
            previous_match.opponent = match.get('opponent').text 

            # parse name when country comes first or at the end
            previous_match.opponent = re.sub('^[a-z]+\s', '', previous_match.opponent)

            previous_match.goals_for = int(match.get('goals_for').text)
            previous_match.goals_against = int(match.get('goals_against').text)
            previous_match.formation = match.get('formation').text
            previous_match.possession = float(match.get('possession').text) if match.get('possession').text else None 
            previous_match.captain = match.get('captain').text

            # collect match details 
            match_report = self._handle_match_report(
                match_url = match.get('match_report').find('a').attrs.get('href'), 
                venue = previous_match.venue
            )
            previous_match.corners = match_report['corners']
            previous_match.shots = match_report['shots']
            previous_match.shots_on_target = match_report['shots_on_target']
            previous_match.offsides = match_report['offsides']
            previous_match.fouls = match_report['fouls']
            previous_match.match_summary = match_report['summary']

            self.history.append(previous_match)

    def results(self) -> dict:
        """ """
        results = {'W':0, 'L': 0, 'D': 0}

        for match in self.history:
            if match.result=='W':
                results['W'] +=1
            
            if match.result=='L':
                results['L'] +=1
            
            if match.result=='D':
                results['D'] +=1
        
        return results 

    def corners(self) -> dict:
        """ """
        total = 0
        avg = None

        for match in self.history:
            if match.corners:
                total+=match.corners
        
        avg = round(total/len(self.history), 2)

        return {'total': total, 'avg': avg}

    def fouls(self) -> dict:
        """ """
        total = 0
        avg = None

        for match in self.history:
            if match.fouls:
                total+=match.fouls
        
        avg = round(total/len(self.history), 2)

        return {'total': total, 'avg': avg}

    def offsides(self) -> dict:
        """ """
        total = 0
        avg = None

        for match in self.history:
            if match.offsides:
                total+=match.offsides
        
        avg = round(total/len(self.history), 2)

        return {'total': total, 'avg': avg}
        
    def shots(self) -> dict:
        """ """
        total = 0
        avg = None

        for match in self.history:
            if match.shots:
                total+=match.shots
        
        avg = round(total/len(self.history), 2)

        return {'total': total, 'avg': avg}
        
    def goals_for(self) -> dict:
        """ """
        total = 0
        avg = None

        for match in self.history:
            if match.goals_for:
                total+=match.goals_for
        
        avg = round(total/len(self.history), 2)

        return {'total': total, 'avg': avg}
        
    def goals_against(self) -> dict:
        """ """
        total = 0
        avg = None

        for match in self.history:
            if match.goals_against:
                total+=match.goals_against
        
        avg = round(total/len(self.history), 2)

        return {'total': total, 'avg': avg}

    def to_dict(self) -> list:
        
        team_history = []

        for match in self.history:
            team_history.append({
                'time': match.time,
                'competition': match.competition,
                'result': match.result,
                'venue': match.venue,
                'opponent': match.opponent,
                'goals_for': match.goals_for,
                'goals_against': match.goals_against,
                'formation': match.formation,
                'possession': match.possession,
                'captain': match.captain,
                'corners': match.corners,
                'shots': match.shots,
                'shots_on_target': match.shots_on_target,
                'offsides': match.offsides,
                'fouls': match.fouls,
                'match_summary': match.match_summary
            })
        
        return team_history

    def to_json(self) -> str:
        
        team_history = []

        for match in self.history:
            team_history.append({
                'time': match.time,
                'competition': match.competition,
                'result': match.result,
                'venue': match.venue,
                'opponent': match.opponent,
                'goals_for': match.goals_for,
                'goals_against': match.goals_against,
                'formation': match.formation,
                'possession': match.possession,
                'captain': match.captain,
                'corners': match.corners,
                'shots': match.shots,
                'shots_on_target': match.shots_on_target,
                'offsides': match.offsides,
                'fouls': match.fouls,
                'match_summary': match.match_summary
            })
        
        return json.dumps(team_history)

    def to_csv(self, path: str) -> None:

        data = self.to_dict()
        with open(path, 'w', newline='') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)


class ScheduledMatch:
    def __init__(self) -> None:
        self.competition = str
        self.home = str
        self.away = str
        self.score = str
        self.date = str
        self.venue = str
        self._home_ref = str
        self._away_ref = str

    def display(self) -> str:
        return f"""=====************=====
        🏆 {self.competition} 
        ⚽️ {self.date}
        {self.home} X {self.away}
        🏟  {self.venue}
        """

    def home_stats(self, previous_matches: int, competitions: str, venue= str) -> Squad:
        """Return statistics from Home team last N `~previous_matches` games.

        :params previous_matches: number of matches to considerate on summary.
        """
        squad = Squad(name=self.home, competition=self.competition, venue='Home')
        squad.match_summary(href=self._home_ref, previous_matches=previous_matches, competitions=competitions, venue=venue)

        return squad
    
    def away_stats(self, previous_matches: int, competitions: str, venue= str) -> Squad:
        """Return statistics from Away team last N `~previous_matches` games.

        :params previous_matches: number of matches to considerate on summary.
        """
        squad = Squad(name=self.away, competition=self.competition, venue='Away')
        squad.match_summary(href=self._away_ref, previous_matches=previous_matches, competitions=competitions, venue=venue)

        return squad
    
    def describe(self) -> str:
        home = self.home_stats(previous_matches=5, competitions='all', venue='any')
        away = self.away_stats(previous_matches=5, competitions='all', venue='any')

        return f"""
            =====*******************************=====
            🏆 {self.competition} 
            ⚽️ {self.date}
            🏟  {self.venue}
            |---------------------------------------|
            | {self.home}
            | goals. {home.goals_for()['avg']}
            | corners. {home.corners()['avg']}
            | fouls. {home.fouls()['avg']}
            | shots. {home.shots()['avg']}
            | offsides. {home.offsides()['avg']}
            |---------------------------------------|
            | {self.away}
            | goals. {away.goals_for()['avg']}
            | corners. {away.corners()['avg']}
            | fouls. {away.fouls()['avg']}
            | shots. {away.shots()['avg']}
            | offsides. {away.offsides()['avg']}
        
        """


matches = ScheduledMatches()
for match in matches.day_matches(date='2022-04-13'):
    print(match.describe())