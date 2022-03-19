from operator import attrgetter
from typing import Union

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .passing import Passing
from .team import Team


class Sacks(db.Model):
    __tablename__ = 'sacks'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    sacks = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    pass_attempts = db.Column(db.Integer, nullable=False)

    @property
    def sacks_per_game(self) -> float:
        if self.games:
            return self.sacks / self.games
        return 0.0

    @property
    def sack_pct(self) -> float:
        attempts = self.sacks + self.pass_attempts
        if attempts:
            return self.sacks / attempts * 100
        return 0.0

    @property
    def yards_per_sack(self) -> float:
        if self.sacks:
            return self.yards / self.sacks
        return 0.0

    @classmethod
    def add_sacks(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get sack and opponent sack stats for all teams for the given
        years and add them to the database.

        Args:
            start_year (int): Year to start adding sack stats
            end_year (int): Year to stop adding sack stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding sack stats for {year}')
            cls.add_sacks_for_one_year(year=year)

    @classmethod
    def add_sacks_for_one_year(cls, year: int) -> None:
        """
        Get sack and opponent sack stats for all teams for one year and
        add them to the database.

        Args:
            year (int): Year to add sack stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            sacks = []

            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='20')
            sacks_data = scraper.parse_html_data(
                html_content=html_content)

            for item in sacks_data:
                team = Team.query.filter_by(name=item[1]).first()
                opposite_side_of_ball = 'defense' \
                    if side_of_ball == 'offense' else 'offense'
                passing = Passing.get_passing(
                    side_of_ball=opposite_side_of_ball,
                    start_year=year,
                    team=team.name
                )

                sacks.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    sacks=item[3],
                    yards=item[4],
                    pass_attempts=passing.attempts
                ))

            for team_sacks in sorted(sacks, key=attrgetter('team_id')):
                db.session.add(team_sacks)

        db.session.commit()

    def __add__(self, other: 'Sacks') -> 'Sacks':
        """
        Add two Sacks objects to combine multiple years of data.

        Args:
            other (Sacks): Data about a team's sacks or opponent's sacks

        Returns:
            Sacks: self
        """
        self.games += other.games
        self.sacks += other.sacks
        self.yards += other.yards
        self.pass_attempts += other.pass_attempts

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'sacks': self.sacks,
            'sacks_per_game': round(self.sacks_per_game, 2),
            'yards': self.yards,
            'yards_per_sack': round(self.yards_per_sack, 2),
            'pass_attempts': self.pass_attempts,
            'sack_pct': round(self.sack_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
