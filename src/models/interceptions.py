from operator import attrgetter
from typing import Union

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team


class Interceptions(db.Model):
    __tablename__ = 'interceptions'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    games = db.Column(db.Integer, nullable=False)
    ints = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    tds = db.Column(db.Integer, nullable=False)

    @property
    def ints_per_game(self) -> float:
        if self.games:
            return self.ints / self.games
        return 0.0

    @property
    def yards_per_int(self) -> float:
        if self.ints:
            return self.yards / self.ints
        return 0.0

    @property
    def td_pct(self) -> float:
        if self.ints:
            return self.tds / self.ints * 100
        return 0.0

    @classmethod
    def get_interceptions(cls, start_year: int, end_year: int = None,
                          team: str = None) -> Union['Interceptions',
                                                     list['Interceptions']]:
        """
        Get interceptions or opponent interceptions for qualifying
        teams for the given years. If team is provided, only get
        interception data for that team.

        Args:
            start_year (int): Year to start getting interception data
            end_year (int): Year to stop getting interception data
            team (str): Team for which to get interception data

        Returns:
            Union[Interceptions, list[Interceptions]]: Interceptions or
                opponent interceptions for all teams or only for one
                team
        """
        if end_year is None:
            end_year = start_year

        qualifying_teams = Team.get_qualifying_teams(
            start_year=start_year, end_year=end_year)

        query = cls.query.join(Team).filter(
            cls.year >= start_year, cls.year <= end_year)

        if team is not None:
            ints = query.filter_by(name=team).all()
            return sum(ints[1:], ints[0])

        ints = {}
        for team_name in qualifying_teams:
            team_ints = query.filter_by(name=team_name).all()

            if team_ints:
                ints[team_name] = sum(team_ints[1:], team_ints[0])

        return [ints[team] for team in sorted(ints.keys())]

    @classmethod
    def add_interceptions(cls, start_year: int = None,
                          end_year: int = None) -> None:
        """
        Get interceptions and opponent interceptionss for all teams for
        the given years and add them to the database.

        Args:
            start_year (int): Year to start adding interception stats
            end_year (int): Year to stop adding interception stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            end_year = max([year.year for year in query])
            years = range(2010, end_year + 1)
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding interception stats for {year}')
            cls.add_interceptions_for_one_year(year=year)

    @classmethod
    def add_interceptions_for_one_year(cls, year: int) -> None:
        """
        Get interceptions and opponent interceptions for all teams for
        one year and add them to the database.

        Args:
            year (int): Year to add interception stats
        """
        scraper = CFBStatsScraper(year=year)
        interceptions = []

        html_content = scraper.get_html_data(
            side_of_ball='offense', category='16')
        interception_data = scraper.parse_html_data(
            html_content=html_content)

        for item in interception_data:
            team = Team.query.filter_by(name=item[1]).first()

            interceptions.append(cls(
                team_id=team.id,
                year=year,
                games=item[2],
                ints=item[3],
                yards=item[4],
                tds=item[5]
            ))

        for team_interceptions in sorted(
                interceptions, key=attrgetter('team_id')):
            db.session.add(team_interceptions)

        db.session.commit()

    def __add__(self, other: 'Interceptions') -> 'Interceptions':
        """
        Add two Interceptions objects to combine multiple years of data.

        Args:
            other (Interceptions): Data about a team's interceptions

        Returns:
            Interceptions: self
        """
        self.games += other.games
        self.ints += other.ints
        self.yards += other.yards
        self.tds += other.tds

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'ints': self.ints,
            'ints_per_game': round(self.ints_per_game, 2),
            'yards': self.yards,
            'yards_per_int': round(self.yards_per_int, 2),
            'tds': self.tds,
            'td_pct': round(self.td_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
