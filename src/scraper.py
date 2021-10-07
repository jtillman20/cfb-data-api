import re

import dateutil
from bs4 import BeautifulSoup
from requests import Session


class SportsReferenceScraper(object):
    BASE_URL = 'https://sports-reference.com/cfb/years'

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
        url = f'{self.BASE_URL}/{path}'
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
    def parse_schedule_html_data(cls, html_content: str) -> dict:
        """
        Parse the HTML data to get information for every game.

        Args:
            html_content (str): Web page HTML data

        Returns:
            dict: Game information
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

            yield {
                'year': year,
                'week': week,
                'date': date,
                'neutral_site': neutral_site,
                'home_team': home_team,
                'home_score': home_score,
                'away_team': away_team,
                'away_score': away_score
            }

    @classmethod
    def parse_ap_rankings_data(cls, html_content: str) -> dict:
        """
        Parse the HTML data to get information for every AP Poll
        ranking.

        Args:
            html_content (str): Web page HTML data

        Returns:
            dict: AP Poll ranking information
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

            yield {
                'final_week': final_week,
                'week': week,
                'rank': rank,
                'team': team,
                'first_place_votes': first_place_votes,
                'previous_rank': previous_rank,
                'wins': int(wins),
                'losses': int(losses),
                'ties': int(ties)
            }
