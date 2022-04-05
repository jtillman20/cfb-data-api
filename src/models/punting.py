from operator import attrgetter

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team
from .total import Total


class Punting(db.Model):
    __tablename__ = 'punting'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    punts = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def punts_per_game(self) -> float:
        if self.games:
            return self.punts / self.games
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def yards_per_punt(self) -> float:
        if self.punts:
            return self.yards / self.punts
        return 0.0

    @property
    def plays_per_punt(self) -> float:
        if self.punts:
            return self.plays / self.punts
        return 0.0

    @classmethod
    def add_punting(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get punting and opponent punting stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding punting stats
            end_year (int): Year to stop adding punting stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding punting stats for {year}')
            cls.add_punting_for_one_year(year=year)

    @classmethod
    def add_punting_for_one_year(cls, year: int) -> None:
        """
        Get punting and opponent punting stats for all teams for one
        year and add them to the database.

        Args:
            year (int): Year to add punting stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            punting = []

            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='06')
            punting_data = scraper.parse_html_data(
                html_content=html_content)

            for item in punting_data:
                team = Team.query.filter_by(name=item[1]).first()
                opposite_side_of_ball = 'defense' \
                    if side_of_ball == 'offense' else 'offense'
                total = Total.get_total(
                    side_of_ball=opposite_side_of_ball,
                    start_year=year,
                    team=team.name
                )

                punting.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    punts=item[3],
                    yards=item[4],
                    plays=total.plays
                ))

            for team_punting in sorted(punting, key=attrgetter('team_id')):
                db.session.add(team_punting)

        db.session.commit()

    def __add__(self, other: 'Punting') -> 'Punting':
        """
        Add two Punting objects to combine multiple years of data.

        Args:
            other (Punting): Data about a team's punting or opponent
                punting

        Returns:
            Punting: self
        """
        self.games += other.games
        self.punts += other.punts
        self.yards += other.yards
        self.plays += other.plays

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'punts': self.punts,
            'punts_per_game': round(self.punts_per_game, 2),
            'yards': self.yards,
            'yards_per_game': round(self.yards_per_game, 1),
            'yards_per_punt': round(self.yards_per_punt, 2),
            'plays_per_punt': round(self.plays_per_punt, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
