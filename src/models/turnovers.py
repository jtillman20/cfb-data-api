from numpy import sum

from app import db
from .game import Game
from .team import Team


class Turnovers(db.Model):
    __tablename__ = 'turnovers'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    games = db.Column(db.Integer, nullable=False)
    ints = db.Column(db.Integer, nullable=False)
    fumbles = db.Column(db.Integer, nullable=False)
    opponent_ints = db.Column(db.Integer, nullable=False)
    opponent_fumbles = db.Column(db.Integer, nullable=False)

    @property
    def giveaways(self) -> int:
        return self.ints + self.fumbles

    @property
    def giveaways_per_game(self) -> float:
        if self.games:
            return self.giveaways / self.games
        return 0.0

    @property
    def takeaways(self) -> int:
        return self.opponent_ints + self.opponent_fumbles

    @property
    def takeaways_per_game(self) -> float:
        if self.games:
            return self.takeaways / self.games
        return 0.0

    @property
    def margin(self) -> int:
        return self.takeaways - self.giveaways

    @property
    def margin_per_game(self) -> float:
        if self.games:
            return self.margin / self.games
        return 0.0

    @classmethod
    def get_turnovers(cls, start_year: int, end_year: int = None,
                      team: str = None) -> list['Turnovers']:
        """
        Get turnovers and opponent turnovers for qualifying teams for
        the given years. If team is provided, only get turnover data
        for that team.

        Args:
            start_year (int): Year to start getting turnover data
            end_year (int): Year to stop getting turnover data
            team (str): Team for which to get turnover data

        Returns:
            list[Turnovers]: Turnovers or opponent turnovers for all
                teams or only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.year >= start_year, cls.year <= end_year)

        if team is not None:
            turnovers = query.filter_by(name=team).all()
            return [sum(turnovers)] if turnovers else []

        turnovers = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_turnovers = query.filter_by(name=team_name).all()

            if team_turnovers:
                turnovers[team_name] = sum(team_turnovers)

        return [turnovers[team] for team in sorted(turnovers.keys())]

    @classmethod
    def add_turnovers(cls, start_year: int = None,
                      end_year: int = None) -> None:
        """
        Get turnovers and opponent turnovers for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding penalty stats
            end_year (int): Year to stop adding penalty stats
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
            print(f'Adding turnover stats for {year}')
            cls.add_turnovers_for_one_year(year=year)

    @classmethod
    def add_turnovers_for_one_year(cls, year: int) -> None:
        """
        Get turnovers and opponent turnovers for all teams for one year
        and add them to the database.

        Args:
            year (int): Year to get penalty stats
        """
        for team in Team.get_teams(year=year):
            games = Game.get_games(year=year, team=team.name)
            game_stats = [game.stats[0] for game in games]
            ints, fumbles, opponent_ints, opponent_fumbles = 0, 0, 0, 0

            for stats in game_stats:
                home_team = stats.game.home_team

                if home_team == team.name:
                    side = 'home'
                    opp_side = 'away'
                else:
                    side = 'away'
                    opp_side = 'home'

                ints += getattr(stats, f'{side}_ints')
                fumbles += getattr(stats, f'{side}_fumbles')
                opponent_ints += getattr(stats, f'{opp_side}_ints')
                opponent_fumbles += getattr(stats, f'{opp_side}_fumbles')

            db.session.add(cls(
                team_id=team.id,
                year=year,
                games=len(games),
                ints=ints,
                fumbles=fumbles,
                opponent_ints=opponent_ints,
                opponent_fumbles=opponent_fumbles
            ))

        db.session.commit()

    def __add__(self, other: 'Turnovers') -> 'Turnovers':
        """
        Add two Turnovers objects to combine multiple years of data.

        Args:
            other (Turnovers): Data about a team's turnovers and
                opponent's turnovers

        Returns:
            Turnovers: self
        """
        self.games += other.games
        self.ints += other.ints
        self.fumbles += other.fumbles
        self.opponent_ints += other.opponent_ints
        self.opponent_fumbles += other.opponent_fumbles

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'games': self.games,
            'ints': self.ints,
            'fumbles': self.fumbles,
            'giveaways': self.giveaways,
            'giveaways_per_game': round(self.giveaways_per_game, 2),
            'opponent_ints': self.opponent_ints,
            'opponent_fumbles': self.opponent_fumbles,
            'takeaways': self.takeaways,
            'takeaways_per_game': round(self.takeaways_per_game, 2),
            'margin': self.margin,
            'margin_per_game': round(self.margin_per_game, 2)
        }
