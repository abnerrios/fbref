
from urllib.parse import urljoin, urlparse
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime


class Matches:
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
                    match = Match()
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


class Stats(object):

    def _handle_played_matches(self, rows: list) -> list:
        matches = []

        for row in rows:
            result = row.find('td', attrs={'data-stat': 'result'})
            if result.text:
                data = row.find_all('td')
                match_dict = {stat.attrs['data-stat']: stat for stat in data}
                matches.append(match_dict)

        return matches

    def _handle_previous_matches(self, squad_url, previous_matches) -> list:

        last_matches = []
        rsp = requests.request('GET', squad_url)
        content = rsp.content
        soup = BeautifulSoup(content, 'html.parser')
        matchlogs = soup.find('div', attrs={'id': 'div_matchlogs_for'})
        matchlogs_table = matchlogs.find('tbody')
        rows = matchlogs_table.find_all('tr')

        matches = self._handle_played_matches(rows)
        matches.reverse()

        for i in range(previous_matches):
            match = matches[i]
            last_matches.append(match)

        return last_matches

    def match_summary(self, href, previous_matches) -> dict:
        squad_url = urljoin('https://fbref.com', href)
        previous_matches = self._handle_previous_matches(squad_url, previous_matches)

        for match in previous_matches:
            pass


class Match(Stats):
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

    def home_stats(self, previous_matches: int) -> None:
        """Return statistics from Home team last N `~previous_matches` games.

        :params previous_matches: number of matches to considerate on summary.
        """
        self.match_summary(href=self._home_ref, previous_matches=previous_matches)
    
    def away_stats(self, previous_matches: int) -> None:
        """Return statistics from Away team last N `~previous_matches` games.

        :params previous_matches: number of matches to considerate on summary.
        """
        self.match_summary(href=self._away_ref, previous_matches=previous_matches)

matches = Matches(data='2022-04-11')

for match in matches.day_matches():
    match.home_stats(previous_matches=5)