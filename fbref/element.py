
from urllib.parse import urljoin
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from handlers import PreviousMatchHandlers


class ScheduledMatches:
    r"""``Matches`` allows you to collect all matches of the day from `fbref.com`.

        See following example:

        .. code-block:: python

        matches = Matches()
        matches.day_matches()

        :params date: 'YYYY-MM-DD'

    """
    def __init__(self, data: str) -> None:
        self._data = data

    def _handle_data(self, data) -> str:
        
        if not data:
            return datetime.now().strftime('YYYY-MM-DD')

    def day_matches(self) -> list:
        """ """
        rsp = requests.request('GET', f'https://fbref.com/en/matches/{self._data}')
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

                    home_a = match_dict.get('squad_a').find('a')
                    away_a = match_dict.get('squad_a').find('a')

                    match._home_ref = home_a.attrs.get('href')
                    match._away_ref = away_a.attrs.get('href')

                    day_matches.append(match)
        else:
            raise AttributeError(f"Can't collect matches. See error:\n {rsp.text}")

        return day_matches


class MatchReport:
    def __init__(self) -> None:
        pass

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
        self.match_report = MatchReport()


class Squad(PreviousMatchHandlers):
    def __init__(self, name) -> None:
        super().__init__()
        self.name = name
        self.history = []

    def match_summary(self, href, previous_matches) -> None:
        squad_url = urljoin('https://fbref.com', href)
        previous_matches = self._handle_previous_matches(squad_url, previous_matches)

        for match in previous_matches:
            previous_match = PreviousMatch()
            previous_match.time = match.get('time').text
            previous_match.competition = match.get('comp').text
            previous_match.result = match.get('result').text
            previous_match.venue = match.get('venue').text
            previous_match.opponent = match.get('opponent').text 

            # parse name when country comes first
            previous_match.opponent = re.sub('^[a-z]+\s', '', previous_match.opponent)

            previous_match.goals_for = int(match.get('goals_for').text)
            previous_match.goals_against = int(match.get('goals_against').text)
            previous_match.formation = match.get('formation').text
            previous_match.possession = float(match.get('possession').text) if match.get('possession').text else None 
            previous_match.captain = match.get('captain').text
            previous_match.match_report = self._handle_match_report(match.get('match_report').find('a').attrs.get('href'))

            self.history.append(previous_match)

    def results(self) -> dict:
        results = {'W':0, 'L': 0, 'D': 0}

        for match in self.history:
            if match.result=='W':
                results['W'] +=1
            
            if match.result=='L':
                results['L'] +=1
            
            if match.result=='W':
                results['D'] +=1
        
        return results 

    def to_dict(self) -> dict:
        pass

    def to_json(self) -> dict:
        pass


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
        return f"""=====* {self.competition} *=====
        ⚽️ {self.date}
        {self.home} X {self.away}
        🏟  {self.venue}
        """

    def home_stats(self, previous_matches: int) -> Squad:
        """Return statistics from Home team last N `~previous_matches` games.

        :params previous_matches: number of matches to considerate on summary.
        """
        squad = Squad(name=self.home)
        squad.match_summary(href=self._home_ref, previous_matches=previous_matches)

        return squad
    
    def away_stats(self, previous_matches: int) -> Squad:
        """Return statistics from Away team last N `~previous_matches` games.

        :params previous_matches: number of matches to considerate on summary.
        """
        squad = Squad(name=self.away)
        squad.match_summary(href=self._away_ref, previous_matches=previous_matches)

        return squad



matches = ScheduledMatches(data='2022-04-12')
for match in matches.day_matches():
    match.home_stats(previous_matches=5)