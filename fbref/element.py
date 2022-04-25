from urllib.parse import urljoin
import requests
import re
import json
import csv
from datetime import datetime
import time
from collections import Counter
from bs4 import BeautifulSoup
from .handlers import PreviousMatchHandlers


class ScheduledMatches:
    r"""``Matches`` allows you to collect all matches of the day from `fbref.com`.

        See following example:

            matches = Matches()

            matches.day_matches('YYYY-MM-DD')

    """
    def _handle_date(self, date) -> str:
        
        if not date:
            return datetime.now().strftime('%Y-%m-%d')
        else:
            return date

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
                    if not row.attrs.get('class'):
                        match = ScheduledMatch()
                        data = row.find_all('td')
                        match_dict = {stat.attrs['data-stat']: stat for stat in data}

                        try:
                            venue_epoch = match_dict.get('time').next_element.get('data-venue-epoch')
                        except AttributeError:
                            venue_epoch = None

                        # set match attributes
                        match.competition = competition
                        match.home = match_dict.get('squad_a').text
                        match.away = match_dict.get('squad_b').text
                        match.score = match_dict.get('score').text
                        match.venue = match_dict.get('venue').text

                        # convert epoch to timezone
                        if venue_epoch:
                            match.time = time.strftime('%H:%M',time.localtime(int(venue_epoch)))
                        else:
                            match.time = '00:00'

                        # parse name when country comes first
                        match.away = re.sub('^[a-z]+\s', '', match.away)
                        match.home = re.sub('\s+[a-z]{2,3}$', '', match.home)

                        home_a = match_dict.get('squad_a').find('a')
                        away_a = match_dict.get('squad_b').find('a')

                        match._home_ref = home_a.attrs.get('href')
                        match._away_ref = away_a.attrs.get('href')

                        day_matches.append(match)
        else:
            raise AttributeError(f"Can't collect matches. See error:\n {rsp.text}")

        return sorted(day_matches, key = lambda i: i.time)


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
        self.position = None
        self.history = []
    
    def _per_game(self, number):
        return round(number/len(self.history), 2)

    def match_summary(self, href, previous_matches, competitions, venue) -> None:
        VALID_COMPETITIONS = ['all', 'same']
        VALID_VENUES = ['all', 'same']

        if competitions.lower() not in VALID_COMPETITIONS:
            raise ValueError("competitions: status must be one of %r." % VALID_COMPETITIONS)

        if venue.lower() not in VALID_VENUES:
            raise ValueError("venue: status must be one of %r." % VALID_VENUES)

        squad_url = urljoin('https://fbref.com', href)

        previous_matches = self._handle_previous_matches(squad_url, previous_matches, competitions, venue)

        for match in previous_matches:
            previous_match = PreviousMatch()
            previous_match.time = match.get('time').text
            previous_match.competition = match.get('comp').text
            previous_match.result = match.get('result').text
            previous_match.venue = match.get('venue').text
            previous_match.opponent = match.get('opponent').text 

            # parse name when country comes first or at the end
            previous_match.opponent = re.sub('^[a-z]+\s', '', previous_match.opponent)

            previous_match.goals_for = int(match.get('goals_for').text.split(' ')[0])
            previous_match.goals_against = int(match.get('goals_against').text.split(' ')[0])
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
            previous_match.shots_on_target = match_report['shots_on_target'] or 0
            previous_match.offsides = match_report['offsides']
            previous_match.fouls = match_report['fouls']
            previous_match.match_summary = match_report['summary']

            self.history.append(previous_match)

    def results(self) -> dict:
        """ """
        results = {'W':0, 'L': 0, 'D': 0, 'pts_pct': 0}
        pts = 0

        if len(self.history)>0:
            for match in self.history:
                if match.result=='W':
                    results['W'] +=1
                    pts+=3
                
                if match.result=='L':
                    results['L'] +=1
                
                if match.result=='D':
                    results['D'] +=1
                    pts+=1

                results['pts_pct'] = round((pts/(len(self.history)*3))*100,0)
    
        return results 

    def corners(self) -> dict:
        """ """
        total = 0
        avg = 0.0

        if len(self.history)>0:
            for match in self.history:
                if match.corners:
                    total+=match.corners
            
            avg = self._per_game(total)

        return {'total': total, 'avg': avg}

    def fouls(self) -> dict:
        """ """
        total = 0
        avg = 0.0

        if len(self.history)>0:
            for match in self.history:
                if match.fouls:
                    total+=match.fouls
            
            avg = self._per_game(total)

        return {'total': total, 'avg': avg}

    def offsides(self) -> dict:
        """ """
        total = 0
        avg = 0.0

        if len(self.history)>0:
            for match in self.history:
                if match.offsides:
                    total+=match.offsides
            
            avg = self._per_game(total)

        return {'total': total, 'avg': avg}
        
    def shots(self) -> dict:
        """ """
        total = 0
        avg = 0.0

        if len(self.history)>0:
            for match in self.history:
                if match.shots:
                    total+=match.shots
            
            avg = self._per_game(total)

        return {'total': total, 'avg': avg}
        
    def goals_for(self) -> dict:
        """ """
        total = 0
        avg = 0.0

        if len(self.history)>0:
            for match in self.history:
                if match.goals_for:
                    total+=match.goals_for
            
            avg = self._per_game(total)

        return {'total': total, 'avg': avg}

    def shots_to_goal(self) -> float:
        goals = 0 
        shots_on_target = 0

        if len(self.history)>0:
            for match in self.history:
                goals+=match.goals_for
                shots_on_target+=match.shots_on_target

            if goals==0:
                return 0.0
            
        return round(shots_on_target/goals,2)
        
    def goals_against(self) -> dict:
        """ """
        total = 0
        avg = 0.0

        if len(self.history)>0:
            for match in self.history:
                if match.goals_against:
                    total+=match.goals_against
            
            avg = self._per_game(total)

        return {'total': total, 'avg': avg}

        
    def clean_sheets(self) -> int:
        """ """
        total = 0

        if len(self.history)>0:
            for match in self.history:
                if match.goals_against==0:
                    total+=1

        return total

    def possible_card(self) -> str:
        cards = []

        if len(self.history)>0:
            for match in self.history:
                match_summary = match.match_summary
                cards.extend([x['player'] if x['eventtype']=='Yellow' else None for x in match_summary])

            card_players = Counter(cards)
            card_players.pop(None, None)
            
            if len(card_players)>0 and card_players.most_common(1)[0][1]>1:
                return f'{card_players.most_common(1)[0][0]} [{card_players.most_common(1)[0][1]}]'
        
        return ''

    def possible_striker(self) -> str:
        goals = []
        if len(self.history)>0:
            for match in self.history:
                match_summary = match.match_summary
                goals.extend([x['player'] if x['eventtype']=='Goal' else None for x in match_summary])
                
            strikers = Counter(goals)
            strikers.pop(None, None)

            if len(strikers)>0 and strikers.most_common(1)[0][1]>1:
                return f'{strikers.most_common(1)[0][0]} [{strikers.most_common(1)[0][1]}]'
        
        return ''
            
    def cards(self) -> int:
        events = []
        results = 0
        
        if len(self.history)>0:
            for match in self.history:
                match_summary = match.match_summary
                events.extend([x['eventtype'] for x in match_summary])

            results = self._per_game(events.count('Yellow'))
        
        return results

    def cards_half(self) -> dict:
        half = {'first': 0, 'second': 0}
        events = []

        if len(self.history)>0:
            for match in self.history:
                match_summary = match.match_summary
                card_events = filter(lambda x: True if x['eventtype'] in ['Yellow','Red'] else False, match_summary)
                events.extend(list(card_events))

            first_half = list(filter(self._handle_first_half, events))
            second_half = list(filter(self._handle_second_half, events))

            half['first'] = self._per_game(len(first_half))
            half['second'] = self._per_game(len(second_half))

        return half

    def goals_half(self) -> dict:
        half = {'first': 0, 'second': 0}
        events = []

        if len(self.history)>0:
            for match in self.history:
                match_summary = match.match_summary
                goal_events = filter(lambda x: True if x['eventtype']=='Goal' else False, match_summary)
                events.extend(list(goal_events))

            first_half = list(filter(self._handle_first_half, events))
            second_half = list(filter(self._handle_second_half, events))

            half['first'] = self._per_game(len(first_half))
            half['second'] = self._per_game(len(second_half))

        return half

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
        self.time = str
        self.venue = str
        self._home_ref = str
        self._away_ref = str

    def display(self) -> str:
        return f"""=====************=====
        🏆 {self.competition} 
        ⚽️ {self.time}
        {self.home} X {self.away}
        🏟  {self.venue}
        """

    def home_stats(self, previous_matches: int, competitions: str, venue: str) -> Squad:
        """Return statistics from Home team last N `~previous_matches` games.

        :params previous_matches: number of matches to considerate on summary.
        """
        squad = Squad(name=self.home, competition=self.competition, venue='Home')
        squad.match_summary(href=self._home_ref, previous_matches=previous_matches, competitions=competitions, venue=venue)

        return squad
    
    def away_stats(self, previous_matches: int, competitions: str, venue: str) -> Squad:
        """Return statistics from Away team last N `~previous_matches` games.

        :params previous_matches: number of matches to considerate on summary.
        """
        squad = Squad(name=self.away, competition=self.competition, venue='Away')
        squad.match_summary(href=self._away_ref, previous_matches=previous_matches, competitions=competitions, venue=venue)

        return squad
    
    def describe(self, previous_matches: int) -> str:
        home = self.home_stats(previous_matches=previous_matches, competitions='all', venue='all')
        away = self.away_stats(previous_matches=previous_matches, competitions='all', venue='all')
        home_results = home.results()
        away_results = away.results()

        return f"""
            |===========*Partida*============|
            🏆 {self.competition} 
            ⚽️ {self.time}
            🏟  {self.venue}
            |---------------------------------------|
              *{self.home} ({home.position})*
            | ⚔️  partidas analisadas. {len(home.history)}
            | 📊 V {home_results['W']} | D {home_results['L']} | E {home_results['D']} |
            | 🎯 aproveitamento. {home_results['pts_pct']}%
            | 🥅 gols. {home.goals_for()['avg']}
            | ❌ gols sofridos. {home.goals_against()['avg']}
            | 🧤 clean sheets. {home.clean_sheets()}
            | ⛳️ escanteios. {home.corners()['avg']}
            | 👊 faltas. {home.fouls()['avg']}
            | 🟨 cartões. {home.cards()}
            | 👟 chutes. {home.shots()['avg']}
            | 👟⚽️ chutes para gol (no alvo). {home.shots_to_goal()}
            | 🚷 impedimentos. {home.offsides()['avg']}
            | 📌 olho no cartão. {home.possible_card()}
            | ✅ pode marcar. {home.possible_striker()}
            | ⚽️🕡 gols 1º tempo. {home.goals_half()['first']}
            | ⚽️🕛 gols 2º tempo. {home.goals_half()['second']}
            | 🟨🕡 cartões 1º tempo. {home.cards_half()['first']}
            | 🟨🕛 cartões 2º tempo. {home.cards_half()['second']}
            |---------------------------------------|
              *{self.away} ({away.position})*
            | ⚔️  partidas analisadas. {len(away.history)}
            | 📊 V {away_results['W']} | D {away_results['L']} | E {away_results['D']} |
            | 🎯 aproveitamento. {away_results['pts_pct']}%
            | 🥅 gols. {away.goals_for()['avg']}
            | ❌ gols sofridos. {away.goals_against()['avg']}
            | 🧤 clean sheets. {away.clean_sheets()}
            | ⛳️ escanteios. {away.corners()['avg']}
            | 👊 faltas cometidas. {away.fouls()['avg']}
            | 🟨 cartões. {away.cards()}
            | 👟 chutes. {away.shots()['avg']}
            | 👟⚽️ chutes para gol (no alvo). {away.shots_to_goal()}
            | 🚷 impedimentos. {away.offsides()['avg']}
            | 📌 olho no cartão. {away.possible_card()}
            | ✅ pode marcar. {away.possible_striker()}
            | ⚽️🕡 gols 1º tempo. {away.goals_half()['first']}
            | ⚽️🕛 gols 2º tempo. {away.goals_half()['second']}
            | 🟨🕡 cartões 1º tempo. {away.cards_half()['first']}
            | 🟨🕛 cartões 2º tempo. {away.cards_half()['second']}
        
        """