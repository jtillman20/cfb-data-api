from sqlalchemy import or_

from app import db
from scraper import SportsReferenceScraper
from .team import Team


class Game(db.Model):
    __tablename__ = 'game'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date(), nullable=False)
    neutral_site = db.Column(db.Boolean, nullable=False)
    home_team = db.Column(db.String(100), nullable=False)
    home_score = db.Column(db.Integer, nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    away_score = db.Column(db.Integer, nullable=False)

    def determine_result(self, team: str) -> str:
        """
        Determine the result of the game for the given team.

        Args:
            team (str): Team for which to determine the result

        Returns:
            str: Game result as 'win', 'loss', or 'tie'
        """
        if self.home_score == self.away_score:
            return 'tie'

        if self.home_team == team:
            return 'win' if self.home_score > self.away_score else 'loss'
        else:
            return 'win' if self.away_score > self.home_score else 'loss'

    def is_conference_game(self) -> bool:
        """
        Determine if a game was played between teams from the same
        conference for the given year, ignoring if the conference
        is Independent.

        Returns:
            bool: Whether the game was played between teams from the
                same conference
        """
        home_team = Team.query.filter_by(name=self.home_team).first()
        away_team = Team.query.filter_by(name=self.away_team).first()

        if home_team is not None and away_team is not None:
            home_conference = home_team.get_conference(year=self.year)
            away_conference = away_team.get_conference(year=self.year)
        else:
            return False

        if home_conference == 'Independent':
            return False

        return home_conference == away_conference

    @classmethod
    def get_games(cls, year: int, team: str = None) -> list['Game']:
        """
        Get FBS games for the given year. If team is provided, only
        get that team's games.

        Args:
            year (int): Year to get games
            team (str): Team for which to get games

        Returns:
            list[Game]: All games or only a team's games
        """
        query = cls.query.filter_by(year=year)

        if team is not None:
            query = query.filter(
                or_(cls.home_team == team, cls.away_team == team))

        return query.all()

    @classmethod
    def add_games(cls, start_year: int, end_year: int) -> None:
        """
        Get all FBS games for the given years and add them to the
        database.

        Args:
            start_year (int): Year to begin adding games
            end_year (int): Year to stop adding games
        """
        scraper = SportsReferenceScraper()

        for year in range(start_year, end_year + 1):
            print(f'Adding games for {year}')
            html_content = scraper.get_html_data(path=f'{year}-schedule.html')
            game_data = scraper.parse_schedule_html_data(
                html_content=html_content)

            for game in game_data:
                db.session.add(cls(
                    year=year,
                    week=game['week'],
                    date=game['date'],
                    neutral_site=game['neutral_site'],
                    home_team=game['home_team'],
                    home_score=game['home_score'],
                    away_team=game['away_team'],
                    away_score=game['away_score']
                ))

        db.session.commit()

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'year': self.year,
            'week': self.week,
            'date': self.date,
            'neutral_site': self.neutral_site,
            'home_team': self.team,
            'home_score': self.home_score,
            'away_team': self.away_team,
            'away_score': self.away_score
        }
