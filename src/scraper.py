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

    # Team names from the standings page that are modified from how they
    # appear on Sports Reference to how to store them in the database
    STANDINGS_TEAM_NAMES = {
        'Bowling Green State': 'Bowling Green',
        'California-Santa Barbara': 'UCSB',
        'Louisiana': 'Louisiana-Lafayette',
        'Massachusetts': 'UMass',
        'Middle Tennessee State': 'Middle Tennessee',
        'Nevada-Las Vegas': 'UNLV',
        'North Carolina State': 'NC State',
        'Ole Miss': 'Mississippi',
        'Pitt': 'Pittsburgh',
        'Texas Christian': 'TCU',
        'Virginia Military Institute': 'VMI'
    }

    # Team names from the schedule page that are modified from how they
    # appear on Sports Reference to how to store them in the database
    SCHEDULE_TEAM_NAMES = {
        'Alabama-Birmingham': 'UAB',
        'California-Davis': 'UC Davis',
        'California-Riverside': 'UC Riverside',
        'California-Santa Barbara': 'UCSB',
        'Bowling Green State': 'Bowling Green',
        'Brigham Young': 'BYU',
        'Central Florida': 'UCF',
        'Louisiana': 'Louisiana-Lafayette',
        'Louisiana State': 'LSU',
        'Massachusetts': 'UMass',
        'Middle Tennessee State': 'Middle Tennessee',
        'Nevada-Las Vegas': 'UNLV',
        'North Carolina State': 'NC State',
        'Southern California': 'USC',
        'Southern Methodist': 'SMU',
        'Texas Christian': 'TCU',
        'Texas-El Paso': 'UTEP',
        'Texas-San Antonio': 'UTSA',
        'Virginia Military Institute': 'VMI'
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
