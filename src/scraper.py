import re

from bs4 import BeautifulSoup
from requests import Session


class SportsReferenceScraper(object):
    BASE_URL = 'https://sports-reference.com/cfb/years'
    CONFERENCE_NAME_PATTERN = r'([A-Za-z0-9- ]+) \([A-Za-z]+\)'

    # Conference names that are modified from how they appear on Sports
    # Reference to how to store them in the database
    CONFERENCES_NAMES = {
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

    # Team names that are modified from how they appear on Sports
    # Reference to how to store them in the database
    TEAMS_NAMES = {
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
            if row_class is not None:
                if 'thead' in row_class:
                    continue

            row_data = row.find_all('td')
            team = row_data[0].a.text

            result = re.findall(cls.CONFERENCE_NAME_PATTERN, row_data[1].text)
            conference = result[0].strip() if result else row_data[1].text

            team = cls.TEAMS_NAMES.get(team) or team
            conference = cls.CONFERENCES_NAMES.get(conference) or conference

            yield team, conference
