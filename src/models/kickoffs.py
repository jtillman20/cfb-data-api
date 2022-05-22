from operator import attrgetter
from typing import Union

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team


class Kickoffs(db.Model):
    __tablename__ = 'kickoffs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    kickoffs = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    touchbacks = db.Column(db.Integer, nullable=False)
    out_of_bounds = db.Column(db.Integer, nullable=False)
    onside = db.Column(db.Integer, nullable=False)

    @property
    def yards_per_kickoff(self) -> float:
        if self.kickoffs:
            return self.yards / self.kickoffs
        return 0.0

    @property
    def touchback_pct(self) -> float:
        if self.kickoffs:
            return self.touchbacks / self.kickoffs * 100
        return 0.0

    @property
    def out_of_bounds_pct(self) -> float:
        if self.kickoffs:
            return self.out_of_bounds / self.kickoffs * 100
        return 0.0

    @property
    def onside_pct(self) -> float:
        if self.kickoffs:
            return self.onside / self.kickoffs * 100
        return 0.0

    @classmethod
    def get_kickoffs(cls, side_of_ball: str, start_year: int,
                     end_year: int = None, team: str = None
                     ) -> Union['Kickoffs', list['Kickoffs']]:
        """
        Get kickoffs or opponent kickoffs for qualifying teams for the
        given years. If team is provided, only get kickoff data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting kickoff data
            end_year (int): Year to stop getting kickoff data
            team (str): Team for which to get kickoff data

        Returns:
            Union[Kickoffs, list[Kickoffs]]: Kickoffs or opponent
                kickoffs for all teams or only for one team
        """
        if end_year is None:
            end_year = start_year

        qualifying_teams = Team.get_qualifying_teams(
            start_year=start_year, end_year=end_year)

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            kickoffs = query.filter_by(name=team).all()
            return sum(kickoffs[1:], kickoffs[0])

        kickoffs = {}
        for team_name in qualifying_teams:
            team_kickoffs = query.filter_by(name=team_name).all()

            if team_kickoffs:
                kickoffs[team_name] = sum(team_kickoffs[1:], team_kickoffs[0])

        return [kickoffs[team] for team in sorted(kickoffs.keys())]

    @classmethod
    def add_kickoffs(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get kickoff and opponent kickoff stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding kickoff stats
            end_year (int): Year to stop adding kickoff stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding kickoff stats for {year}')
            cls.add_kickoffs_for_one_year(year=year)

    @classmethod
    def add_kickoffs_for_one_year(cls, year: int) -> None:
        """
        Get kickoff and opponent kickoff stats for all teams for
        one year and add them to the database.

        Args:
            year (int): Year to add kickoff stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            kickoffs = []

            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='29')
            kickoff_data = scraper.parse_html_data(html_content=html_content)

            for item in kickoff_data:
                team = Team.query.filter_by(name=item[1]).first()

                kickoffs.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    kickoffs=item[3],
                    yards=item[4],
                    touchbacks=item[6],
                    out_of_bounds=item[8],
                    onside=item[9]
                ))

            for team_kickoffs in sorted(kickoffs, key=attrgetter('team_id')):
                db.session.add(team_kickoffs)

        db.session.commit()

    def __add__(self, other: 'Kickoffs') -> 'Kickoffs':
        """
        Add two Kickoffs objects to combine multiple years of data.

        Args:
            other (Kickoffs): Data about a team's kickoffs or opponent
                kickoffs

        Returns:
            Kickoffs: self
        """
        self.games += other.games
        self.kickoffs += other.kickoffs
        self.yards += other.yards
        self.touchbacks += other.touchbacks
        self.out_of_bounds += other.out_of_bounds
        self.onside += other.onside

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'kickoffs': self.kickoffs,
            'yards': self.yards,
            'yards_per_kickoff': round(self.yards_per_kickoff, 2),
            'touchbacks': self.touchbacks,
            'touchback_pct': round(self.touchback_pct, 2),
            'out_of_bounds': self.out_of_bounds,
            'out_of_bounds_pct': round(self.out_of_bounds_pct, 2),
            'onside': self.onside,
            'onside_pct': round(self.onside_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data


class KickoffReturns(db.Model):
    __tablename__ = 'kickoff_returns'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    returns = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    tds = db.Column(db.Integer, nullable=False)
    kickoffs = db.Column(db.Integer, nullable=False)

    @property
    def returns_per_game(self) -> float:
        if self.games:
            return self.returns / self.games
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def yards_per_return(self) -> float:
        if self.returns:
            return self.yards / self.returns
        return 0.0

    @property
    def td_pct(self) -> float:
        if self.returns:
            return self.tds / self.returns * 100
        return 0.0

    @property
    def return_pct(self) -> float:
        if self.kickoffs:
            return self.returns / self.kickoffs * 100
        return 0.0

    def __add__(self, other: 'KickoffReturns') -> 'KickoffReturns':
        """
        Add two KickoffReturns objects to combine multiple years of data.

        Args:
            other (KickoffReturns): Data about a team's kickoff returns
                or opponent kickoff returns

        Returns:
            KickoffReturns: self
        """
        self.games += other.games
        self.returns += other.returns
        self.yards += other.yards
        self.tds += other.tds
        self.kickoffs += other.kickoffs

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'returns': self.returns,
            'returns_per_game': round(self.returns_per_game, 2),
            'yards': self.yards,
            'yards_per_game': round(self.yards_per_game, 1),
            'yards_per_return': round(self.yards_per_return, 2),
            'tds': self.tds,
            'td_pct': round(self.td_pct, 2),
            'kickoffs': self.kickoffs,
            'return_pct': round(self.return_pct, 2)

        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
