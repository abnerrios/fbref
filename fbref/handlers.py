import requests
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup


class PreviousMatchHandlers(object):
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

    def _handle_match_report(self, match_url) -> dict:
        match_report = {
            'possesion': 0, 
            'shots': 0,
            'shots_on_target': 0,
            'corners': 0,
            'offsides': 0,
            'fouls': 0,
            'summary': {}
        }

        url = urljoin('https://fbref.com/', match_url)
        rsp = requests.request('GET', url)
        cleanr = re.compile('<.*?>|/|\n|\t|\xa0|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{a,6});')

        if rsp.status_code<400:
            content = rsp.content
            soup = BeautifulSoup(content, 'html.parser')
            scorebox = soup.find('div', attrs={'class': 'scorebox'})
            events_wrap = soup.find('div', attrs={'id': 'events_wrap'})
            events = events_wrap.find_all('div', attrs={'class': 'event'})

            performers = scorebox.find_all('a', attrs={'itemprop': 'name'})
            home = performers[0].text
            away = performers[1].text

            match_report['summary'].update({home: [], away: []})

            for event in events:
                team = home if 'a' in event.attrs.get('class') else away
                minute_div = event.find_all('div')[0]
                eventtype_div = event.find_all('div')[1]
                # clean simbols of text
                cleaned_minute = re.sub(cleanr, '', minute_div.text)
                cleaned_event = re.sub(cleanr, '', eventtype_div.text)
                # return only relevant parts of events
                minute = re.sub(r'\’.+','', cleaned_minute)
                player_event = cleaned_event.split('—')[0]
                event = cleaned_event.split('—')[1]

                if event!='Substitute':
                    match_report['summary'][team].append({
                        'minute': minute,
                        'eventtype': event,
                        'player': player_event
                    })

        return match_report