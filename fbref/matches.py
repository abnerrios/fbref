import requests
from bs4 import BeautifulSoup
import re
import logging
from models.match import Match

logging.basicConfig(filename='footstats.log', filemode='a', level=logging.ERROR, format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p')
html_parser = 'html.parser'

class Matches:
  def __init__(self) -> None:
    self.url = 'https://fbref.com/en/matches/'

  def _parse_match(self, sched_table: BeautifulSoup) -> list:
    """ """
    competition = sched_table.find('h2').find('a').text
    tbody = sched_table.find('tbody')
    rows = tbody.find_all('tr')
    matches = []

    for row in rows:
      match = Match()
      data = row.find_all('td')
      match_dict = {stat.attrs['data-stat']: stat.text for stat in data}

      match.competition = competition
      match.date = match_dict.get('time')
      match.home = match_dict.get('squad_a')
      match.away = match_dict.get('squad_b')
      match.score = match_dict.get('score')
      match.venue = match_dict.get('venue')

      matches.append(match)

    return matches

  def day_matches(self) -> list:
    """ """
    rsp = requests.request('GET', self.url)
    content = rsp.content
    all_day_matches = []

    if rsp.status_code < 400:
      soup = BeautifulSoup(content, html_parser)
      all_sched_tables = soup.find_all('div', attrs={'id': re.compile('all_sched_\d+')})

      for sched_table in all_sched_tables:
        matches = self._parse_match(sched_table)
        all_day_matches.extend(matches)

    return all_day_matches

matches = Matches()

for match in matches.day_matches():
  print(match.detail())