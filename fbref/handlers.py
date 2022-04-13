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
            if i<len(matches):
                match = matches[i] 
                last_matches.append(match)

        return last_matches

    def _handle_match_report(self, match_url: str, venue: str) -> dict:
        match_report = {
            'shots': None,
            'shots_on_target': None,
            'corners': None,
            'offsides': None,
            'fouls': None,
            'summary': []
        }

        url = urljoin('https://fbref.com/', match_url)
        rsp = requests.request('GET', url)
        cleanr = re.compile('<.*?>|/|\n|\t|\xa0|—|\d+%|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{a,6});')
        venue_event_class = 'a' if venue=='Home' else 'b'

        if rsp.status_code<400:
            content = rsp.content
            soup = BeautifulSoup(content, 'html.parser')
            team_stats = soup.find('div', attrs={'id': 'team_stats'})

            # Shots on Target
            shots_on_target = team_stats.find('tr', text='Shots on Target')

            if shots_on_target:
                i = 0 if venue=='Home' else 1
                shot_values = shots_on_target.find_next('tr')
                team_shot = shot_values.find_all('td')[i]

                shots_text = team_shot.find('div').find('div').text
                # clean simbols and accuracy of text
                shots_text = re.sub(cleanr,'',shots_text)
                match_report['shots'] = int(shots_text.split(' of ')[1])
                match_report['shots_on_target'] = int(shots_text.split(' of ')[0])

            team_stats_extra = soup.find('div', attrs={'id': 'team_stats_extra'})

            if team_stats_extra:
                has_fouls = team_stats_extra.find('div', text='Fouls')
                has_corners = team_stats_extra.find('div', text='Corners')
                has_offsides = team_stats_extra.find('div', text='Offsides')
                fouls = None
                corners = None
                offsides = None

                if venue=='Home':
                    fouls = int(has_fouls.find_previous('div').text) if has_fouls else None
                    corners = int(has_corners.find_previous('div').text) if has_corners else None
                    offsides = int(has_offsides.find_previous('div').text) if has_offsides else None

                if venue=='Away':
                    fouls = int(has_fouls.find_next('div').text) if has_fouls else None
                    corners = int(has_corners.find_next('div').text) if has_corners else None
                    offsides = int(has_offsides.find_next('div').text) if has_offsides else None
                
                match_report['fouls'] = fouls
                match_report['corners'] = corners
                match_report['offsides'] = offsides

            
            events_wrap = soup.find('div', attrs={'id': 'events_wrap'})
            if events_wrap:
                events = events_wrap.find_all('div', attrs={'class': f'event {venue_event_class}'})

                for event in events:
                    cleanr = re.compile('<.*?>|/|\n|\t|\xa0|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{a,6});')
                    minute_div = event.find_all('div')[0]
                    eventtype_div = event.find_all('div')[1]
                    # clean simbols of text
                    cleaned_minute = re.sub(cleanr, '', minute_div.text)
                    cleaned_event = re.sub(cleanr, '', eventtype_div.text)
                    # return only relevant parts of events
                    minute = re.sub(r'\’.+','', cleaned_minute)
                    event = cleaned_event.split('—')[1].split(' ')[0]
                    player_event = cleaned_event.split('—')[0].split(':')
                    player_event = player_event[1] if len(player_event)>1 else player_event[0]

                    if event!='Substitute':
                        match_report['summary'].append({
                            'minute': minute,
                            'eventtype': event,
                            'player': player_event
                        })

        return match_report