from operator import attrgetter
from typing import Union

from app import db
from scraper import CFBStatsScraper
from .team import Team


class Rushing(db.Model):
    __tablename__ = 'rushing'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    tds = db.Column(db.Integer, nullable=False)

    @property
    def attempts_per_game(self) -> float:
        if self.games:
            return self.attempts / self.games
        return 0.0

    @property
    def yards_per_attempt(self) -> float:
        if self.attempts:
            return self.yards / self.attempts
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def td_pct(self) -> float:
        if self.attempts:
            return self.tds / self.attempts * 100
        return 0.0

    def __add__(self, other: 'Rushing') -> 'Rushing':
        """
        Add two Rushing objects to combine multiple years of data.

        Args:
            other (Rushing): Data about a team's rushing offense/defense

        Returns:
            Rushing: self
        """
        self.games += other.games
        self.attempts += other.attempts
        self.yards += other.yards
        self.tds += other.tds

        return self

    @classmethod
    def add_rushing(cls, start_year: int, end_year: int) -> None:
        """
        Get rushing offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start getting rushing stats
            end_year (int): Year to stop getting rushing stats
        """
        for year in range(start_year, end_year + 1):
            print(f'Adding rushing stats for {year}')
            cls.add_rushing_for_one_year(year=year)

    @classmethod
    def add_rushing_for_one_year(cls, year: int) -> None:
        """
        Get rushing offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to get rushing stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            rushing = []

            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='01')
            rushing_data = scraper.parse_html_data(
                html_content=html_content)

            for item in rushing_data:
                team = Team.query.filter_by(name=item[1]).first()
                rushing.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    attempts=item[3],
                    yards=item[4],
                    tds=item[6]
                ))

            for team_rushing in sorted(rushing, key=attrgetter('team_id')):
                db.session.add(team_rushing)

        db.session.commit()

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'attempts': self.attempts,
            'attempts_per_game': round(self.attempts_per_game, 2),
            'yards': self.yards,
            'yards_per_attempt': round(self.yards_per_attempt, 2),
            'yards_per_game': round(self.yards_per_game, 1),
            'tds': self.tds,
            'td_pct': round(self.td_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
