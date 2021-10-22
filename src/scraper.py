import re
from typing import Iterator

import dateutil
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import Session


class SportsReferenceScraper(object):
    BASE_URL = 'https://sports-reference.com/cfb'

    # Conference names that are modified from how they appear on Sports
    # Reference to how to store them in the database
    CONFERENCE_NAMES = {
        'ACC': 'Atlantic Coast',
        'American': 'American Athletic',
        'BIAA': 'Border',
        'CUSA': 'Conference USA',
        'Ind': 'Independent',
        'MAC': 'Mid-American',
        'MVC': 'Missouri Valley',
        'MWC': 'Mountain West',
        'PCC': 'Pacific Coast',
        'SEC': 'Southeastern',
        'SWAC': 'Southwestern Athletic',
        'SWC': 'Southwest',
        'WAC': 'Western Athletic'
    }

    TEAM_NAMES = {
        'Bowling Green State': 'Bowling Green',
        'California-Santa Barbara': 'UCSB',
        'Louisiana': 'Louisiana-Lafayette',
        'Massachusetts': 'UMass',
        'Middle Tennessee State': 'Middle Tennessee',
        'Nevada-Las Vegas': 'UNLV',
        'North Carolina State': 'NC State',
        'Texas Christian': 'TCU',
        'Virginia Military Institute': 'VMI'
    }

    # Team names from the standings and polls page that are modified
    # from how they appear on Sports Reference to how to store them
    # in the database
    STANDINGS_TEAM_NAMES = {
        **TEAM_NAMES,
        'Ole Miss': 'Mississippi',
        'Pitt': 'Pittsburgh',
    }
    RANKINGS_TEAM_NAMES = STANDINGS_TEAM_NAMES

    # Team names from the schedule page that are modified from how they
    # appear on Sports Reference to how to store them in the database
    SCHEDULE_TEAM_NAMES = {
        **TEAM_NAMES,
        'Alabama-Birmingham': 'UAB',
        'Brigham Young': 'BYU',
        'California-Davis': 'UC Davis',
        'California-Riverside': 'UC Riverside',
        'Central Florida': 'UCF',
        'Louisiana State': 'LSU',
        'Massachusetts': 'UMass',
        'Southern California': 'USC',
        'Southern Methodist': 'SMU',
        'Texas-El Paso': 'UTEP',
        'Texas-San Antonio': 'UTSA',
    }

    # Team names that are modified from how they are stored in the
    # database to how they appear in the Sports Reference URLs
    URL_TEAM_NAMES = {
        'Bowling Green': 'Bowling Green State',
        'BYU': 'Brigham Young',
        'LSU': 'Louisiana State',
        'Middle Tennessee': 'Middle Tennessee State',
        'NC State': 'North Carolina State',
        'SMU': 'Southern Methodist',
        'TCU': 'Texas Christian',
        'UAB': 'Alabama Birmingham',
        'UCF': 'Central Florida',
        'UMass': 'Massachusetts',
        'UNLV': 'Nevada-Las Vegas',
        'USC': 'Southern California',
        'UTEP': 'Texas-El Paso',
        'UTSA': 'Texas-San Antonio'
    }

    def __init__(self):
        self.session = Session()

    def get_html_data(self, path: str) -> str:
        """
        Get HTML data from a Sports Reference web page for games,
        standings, or polls.

        Args:
            path (str): Path to the web page

        Returns:
            str: HTML data
        """
        url = f'{self.BASE_URL}/years/{path}'
        return self.session.get(url).content.decode('latin-1')

    @classmethod
    def parse_standings_html_data(cls, html_content: str) -> tuple:
        """
        Parse the HTML data to get each team and its associated
        conference.

        Args:
            html_content (str): Web page HTML data

        Returns:
            tuple: Team and conference name
        """
        soup = BeautifulSoup(html_content, 'lxml')
        rows = soup.find(id='standings').find('tbody').find_all('tr')

        for row in rows:
            # Header rows have a thead class attribute so skip them
            row_class = row.get('class')
            if row_class is not None and 'thead' in row_class:
                continue

            team = row.find(attrs={'data-stat': 'school_name'}).text
            conference = row.find(attrs={'data-stat': 'conf_abbr'}).a.text

            team = cls.STANDINGS_TEAM_NAMES.get(team) or team
            conference = cls.CONFERENCE_NAMES.get(conference) or conference

            yield team, conference

    @classmethod
    def parse_schedule_html_data(cls, html_content: str) -> tuple:
        """
        Parse the HTML data to get information for every game.

        Args:
            html_content (str): Web page HTML data

        Returns:
            tuple: Game information
        """
        soup = BeautifulSoup(html_content, 'lxml')
        rows = soup.find(id='schedule').find('tbody').find_all('tr')

        for row in rows:
            # Header rows have a thead class attribute so skip them
            row_class = row.get('class')
            if row_class is not None and 'thead' in row_class:
                continue

            week = int(row.find(attrs={'data-stat': 'week_number'}).text)
            date = dateutil.parser.parse(row.find(
                attrs={'data-stat': 'date_game'}).text)
            year = date.year

            winning_score = int(row.find(
                attrs={'data-stat': 'winner_points'}).text or 0)
            losing_score = int(row.find(
                attrs={'data-stat': 'loser_points'}).text or 0)

            # This happens if a game is cancelled or hasn't been played yet
            if not winning_score and not losing_score and year >= 1996:
                continue

            tag = row.find(attrs={'data-stat': 'winner_school_name'})
            winning_team = tag.a.text if tag.a else tag.text

            tag = row.find(attrs={'data-stat': 'loser_school_name'})
            losing_team = tag.a.text if tag.a else tag.text

            location = row.find(attrs={'data-stat': 'game_location'}).text
            neutral_site = location == 'N'

            if location == '@':
                home_team = losing_team
                home_score = losing_score
                away_team = winning_team
                away_score = winning_score
            else:
                home_team = winning_team
                home_score = winning_score
                away_team = losing_team
                away_score = losing_score

            home_team = cls.SCHEDULE_TEAM_NAMES.get(home_team) or home_team
            away_team = cls.SCHEDULE_TEAM_NAMES.get(away_team) or away_team

            yield (
                week,
                date,
                neutral_site,
                home_team,
                home_score,
                away_team,
                away_score
            )

    @classmethod
    def parse_ap_rankings_data(cls, html_content: str) -> tuple:
        """
        Parse the HTML data to get information for every AP Poll
        ranking.

        Args:
            html_content (str): Web page HTML data

        Returns:
            tuple: AP Poll ranking information
        """
        # Remove any comments
        html_content = html_content.replace('<!--', '').replace('-->', '')

        soup = BeautifulSoup(html_content, 'lxml')
        rows = soup.find(id='ap').find('tbody').find_all('tr')

        # Get the final week to get every team's record for that poll
        # because Sports Reference doesn't have it before 2010
        final_week = int(rows[0].find('th').text)

        for row in rows:
            # Header rows have a thead class attribute so skip them
            row_class = row.get('class')
            if row_class is not None and 'thead' in row_class:
                continue

            team_data = row.find(attrs={'data-stat': 'school_name'}).text
            pattern = r'([A-Za-z &]+(\([A-Z]+\))?)\s?(\((\d+)-(\d+)-?(\d+)?\))?'
            team_data = re.findall(pattern, team_data)[0]

            team = team_data[0].strip()
            team = cls.RANKINGS_TEAM_NAMES.get(team) or team

            wins = team_data[3] or 0
            losses = team_data[4] or 0
            ties = team_data[5] or 0

            week = int(row.find('th').text)
            rank = int(row.find(attrs={'data-stat': 'rank'}).text)

            first_place_votes = row.find(
                attrs={'data-stat': 'votes_first'}).text
            first_place_votes = int(first_place_votes) \
                if first_place_votes else 0

            previous_rank = row.find(attrs={'data-stat': 'rank_prev'}).text
            try:
                previous_rank = int(previous_rank)
            except ValueError:
                previous_rank = None

            yield (
                final_week,
                week,
                rank,
                team,
                first_place_votes,
                previous_rank,
                int(wins),
                int(losses),
                int(ties)
            )

    def get_game_log_html_data(self, team: str, year: int) -> str:
        """
        Get HTML data from Sports Reference page for the game logs.

        Args:
            team (str): Team for which to get game stats
            year (int): Year to get game stats

        Returns:
            str: HTML data
        """
        team = self.URL_TEAM_NAMES.get(team) or team
        for char in ['&', '(', ')']:
            team = team.replace(char, '')
        team = team.replace(' ', '-').lower()

        url = f'{self.BASE_URL}/schools/{team}/{year}/gamelog/'
        return self.session.get(url).content.decode('latin-1')

    @classmethod
    def parse_game_log_data(cls, html_content: str, side_of_ball: str) -> tuple:
        """
        Parse the HTML data to get game stats, such as passing and
        rushing offense/defense, firsts downs, turnovers, etc.

        Args:
            html_content (str): Web page HTML data
            side_of_ball (str): Offense or defense

        Returns:
            tuple: Game stats
        """
        # Remove any comments
        html_content = html_content.replace('<!--', '').replace('-->', '')

        soup = BeautifulSoup(html_content, 'lxml')
        rows = soup.find(id=side_of_ball).find('tbody').find_all('tr')

        for row in rows:
            date = dateutil.parser.parse(row.find(
                attrs={'data-stat': 'date_game'}).text)
            opponent = row.find(
                attrs={'data-stat': 'opp_name'}).text.replace('*', '')
            opponent = cls.SCHEDULE_TEAM_NAMES.get(opponent) or opponent

            passing = list(cls.get_passing_game_log_data(
                tag=row, side_of_ball=side_of_ball))

            rushing = list(cls.get_rushing_game_log_data(
                tag=row, side_of_ball=side_of_ball))

            first_downs = list(cls.get_first_down_game_log_data(
                tag=row, side_of_ball=side_of_ball))

            penalties = int(cls.get_attr_data(
                tag=row, attr='penalty', side_of_ball=side_of_ball))
            penalty_yards = int(cls.get_attr_data(
                tag=row, attr='penalty_yds', side_of_ball=side_of_ball))
            fumbles = int(cls.get_attr_data(
                tag=row, attr='fumbles_lost', side_of_ball=side_of_ball))

            yield (
                date,
                opponent,
                *passing,
                *rushing,
                *first_downs,
                penalties,
                penalty_yards,
                fumbles
            )

    @classmethod
    def get_passing_game_log_data(
            cls, tag: Tag, side_of_ball: str) -> Iterator[str]:
        """
        Get passing data from the game log web page.

        Args:
            tag (Tag): HTML tag
            side_of_ball (str): Offense or defense

        Returns:
            str: Passing data
        """
        attrs = ['att', 'cmp', 'yds', 'td', 'int']
        for attr in attrs:
            yield cls.get_attr_data(
                tag=tag, attr=f'pass_{attr}', side_of_ball=side_of_ball)

    @classmethod
    def get_rushing_game_log_data(
            cls, tag: Tag, side_of_ball: str) -> Iterator[str]:
        """
        Get rushing data from the game log web page.

        Args:
            tag (Tag): HTML tag
            side_of_ball (str): Offense or defense

        Returns:
            str: Rushing data
        """
        attrs = ['att', 'yds', 'td']
        for attr in attrs:
            yield cls.get_attr_data(
                tag=tag, attr=f'rush_{attr}', side_of_ball=side_of_ball)

    @classmethod
    def get_first_down_game_log_data(
            cls, tag: Tag, side_of_ball: str) -> Iterator[str]:
        """
        Get first down data from the game log web page.

        Args:
            tag (Tag): HTML tag
            side_of_ball (str): Offense or defense

        Returns:
            str: First down data
        """
        attrs = ['pass', 'rush', 'penalty']
        for attr in attrs:
            yield cls.get_attr_data(
                tag=tag, attr=f'first_down_{attr}', side_of_ball=side_of_ball)

    @classmethod
    def get_attr_data(cls, tag: Tag, attr: str, side_of_ball: str) -> str:
        """
        Get the data for the given attribute from the given HTML tag.

        Args:
            tag (Tag): HTML tag
            attr (str): Attribute name
            side_of_ball (str): Offense or defense

        Returns:
            str: Attribute data
        """
        attr = f'opp_{attr}' if side_of_ball == 'defense' else attr
        return tag.find(attrs={'data-stat': attr}).text


class CFBStatsScraper(object):
    BASE_URL = 'http://cfbstats.com'

    TEAM_NAMES = {
        'Hawai\'i': 'Hawaii',
        'Massachusetts': 'UMass',
        'Miami (Florida)': 'Miami (FL)',
        'Miami (Ohio)': 'Miami (OH)',
        'North Carolina State': 'NC State',
    }

    def __init__(self, year: int):
        self.session = Session()
        self.base_url = f'{self.BASE_URL}/{year}/leader/national/team'

    def get_html_data(self, side_of_ball: str, category: str) -> str:
        """
        Get HTML data from a CFB Stats web page for team stats.

        Args:
            side_of_ball (str): Offense or defense
            category (str): Number to determine the stat

        Returns:
            str: HTML data
        """
        url = f'{self.base_url}/{side_of_ball}/split01/category{category}/sort01.html'
        return self.session.get(url).content.decode('utf-8')

    @classmethod
    def parse_html_data(cls, html_content: str) -> tuple:
        """
        Parse the HTML data to get every team's stats.

        Args:
            html_content (str): Web page HTML data

        Returns:
            tuple: Team stats
        """
        soup = BeautifulSoup(html_content, 'lxml')
        rows = soup.find('table').find_all('tr')

        for row in rows:
            row_data = row.find_all('td')

            if not row_data:
                continue

            data = [item.text for item in row_data]
            data[1] = cls.TEAM_NAMES.get(data[1]) or data[1]

            yield tuple(data)
