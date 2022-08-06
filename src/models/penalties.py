from numpy import sum

from app import db
from .game import Game
from .team import Team


class Penalties(db.Model):
    __tablename__ = 'penalties'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    penalties = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)

    @property
    def penalties_per_game(self) -> float:
        if self.games:
            return self.penalties / self.games
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def yards_per_penalty(self) -> float:
        if self.penalties:
            return self.yards / self.penalties
        return 0.0

    @classmethod
    def get_penalties(cls, side_of_ball: str, start_year: int,
                      end_year: int = None, team: str = None
                      ) -> list['Penalties']:
        """
        Get penalties or opponent penalties for qualifying teams for
        the given years. If team is provided, only get penalty data
        for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting penalty data
            end_year (int): Year to stop getting penalty data
            team (str): Team for which to get penalty data

        Returns:
            list[Penalties]: Penalties or opponent penalties for all
                teams or only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            penalties = query.filter_by(name=team).all()
            return [sum(penalties)] if penalties else []

        penalties = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_penalties = query.filter_by(name=team_name).all()

            if team_penalties:
                penalties[team_name] = sum(team_penalties)

        return [penalties[team] for team in sorted(penalties.keys())]

    @classmethod
    def add_penalties(cls, start_year: int, end_year: int = None) -> None:
        """
        Get penalties and opponent penalties for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding penalty stats
            end_year (int): Year to stop adding penalty stats
        """
        if end_year is None:
            end_year = start_year
        years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding penalty stats for {year}')
            cls.add_penalties_for_one_year(year=year)

    @classmethod
    def add_penalties_for_one_year(cls, year: int) -> None:
        """
        Get penalties and opponent penalties for all teams for one year
        and add them to the database.

        Args:
            year (int): Year to get penalty stats
        """
        for team in Team.get_teams(year=year):
            games = Game.get_games(year=year, team=team.name)
            game_stats = [game.stats[0] for game in games]

            for side_of_ball in ['offense', 'defense']:
                penalties, yards = 0, 0

                for stats in game_stats:
                    home_team = stats.game.home_team

                    if side_of_ball == 'offense':
                        side = 'home' if home_team == team.name else 'away'
                    else:
                        side = 'away' if home_team == team.name else 'home'

                    penalties += getattr(stats, f'{side}_penalties')
                    yards += getattr(stats, f'{side}_penalty_yards')

                db.session.add(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=len(games),
                    penalties=penalties,
                    yards=yards,
                ))

        db.session.commit()

    def __add__(self, other: 'Penalties') -> 'Penalties':
        """
        Add two Penalties objects to combine multiple years of data.

        Args:
            other (Penalties): Data about a team's penalties or
                opponent's penalties

        Returns:
            Penalties: self
        """
        self.games += other.games
        self.penalties += other.penalties
        self.yards += other.yards

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'penalties': self.penalties,
            'penalties_per_game': round(self.penalties_per_game, 1),
            'yards': self.yards,
            'yards_per_game': round(self.yards_per_game, 1),
            'yards_per_penalty': round(self.yards_per_penalty, 2)
        }
