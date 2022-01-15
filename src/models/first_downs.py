from typing import Union

from app import db
from .game import Game
from .team import Team
from .total import Total


class FirstDowns(db.Model):
    __tablename__ = 'first_downs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    passing = db.Column(db.Integer, nullable=False)
    rushing = db.Column(db.Integer, nullable=False)
    penalty = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def total(self) -> int:
        return self.passing + self.rushing + self.penalty

    @property
    def total_per_game(self) -> float:
        if self.games:
            return self.total / self.games
        return 0.0

    @property
    def passing_pct(self) -> float:
        if self.total:
            return self.passing / self.total * 100
        return 0.0

    @property
    def rushing_pct(self) -> float:
        if self.total:
            return self.rushing / self.total * 100
        return 0.0

    @property
    def penalty_pct(self) -> float:
        if self.total:
            return self.penalty / self.total * 100
        return 0.0

    @property
    def plays_per_first_down(self) -> float:
        if self.plays:
            return self.plays / self.total
        return 0.0

    @classmethod
    def get_first_downs(cls, side_of_ball: str, start_year: int,
                        end_year: int = None, team: str = None
                        ) -> Union['FirstDowns', list['FirstDowns']]:
        """
        Get first down offense or defense for qualifying teams for the
        given years. If team is provided, only get first down data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting first down data
            end_year (int): Year to stop getting first down data
            team (str): Team for which to get first down data

        Returns:
            Union[FirstDowns, list[FirstDowns]]: First down offense or
                defense for all teams or only for one team
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
            first_downs = query.filter_by(name=team).all()
            return sum(first_downs[1:], first_downs[0])

        first_downs = {}
        for team_name in qualifying_teams:
            team_first_downs = query.filter_by(name=team_name).all()

            if team_first_downs:
                first_downs[team_name] = sum(
                    team_first_downs[1:], team_first_downs[0])

        return [first_downs[team] for team in sorted(first_downs.keys())]

    @classmethod
    def add_first_downs(cls, start_year: int = None,
                        end_year: int = None) -> None:
        """
        Get first down offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding first down stats
            end_year (int): Year to stop adding first down stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding first down stats for {year}')
            cls.add_first_downs_for_one_year(year=year)

    @classmethod
    def add_first_downs_for_one_year(cls, year: int) -> None:
        """
        Get first down offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to add first down stats
        """
        teams = Team.get_teams(year=year)

        for team in teams:
            games = Game.get_games(year=year, team=team.name)
            game_stats = [game.stats[0] for game in games]

            for side_of_ball in ['offense', 'defense']:
                passing = 0
                rushing = 0
                penalty = 0

                for stats in game_stats:
                    home_team = stats.game.home_team

                    if side_of_ball == 'offense':
                        side = 'home' if home_team == team.name else 'away'
                    else:
                        side = 'away' if home_team == team.name else 'home'

                    passing += getattr(stats, f'{side}_passing_first_downs')
                    rushing += getattr(stats, f'{side}_rushing_first_downs')
                    penalty += getattr(stats, f'{side}_penalty_first_downs')

                total = Total.get_total(
                    side_of_ball=side_of_ball, start_year=year, team=team.name)

                db.session.add(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=len(games),
                    passing=passing,
                    rushing=rushing,
                    penalty=penalty,
                    plays=total.plays,
                ))

        db.session.commit()

    def __add__(self, other: 'FirstDowns') -> 'FirstDowns':
        """
        Add two FirstDowns objects to combine multiple years of data.

        Args:
            other (Total): Data about a team's first down offense/defense

        Returns:
            Total: self
        """
        self.games += other.games
        self.passing += other.passing
        self.rushing += other.rushing
        self.penalty += other.penalty
        self.plays += other.plays

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'total': self.total,
            'total_per_game': round(self.total_per_game, 1),
            'passing': self.passing,
            'passing_pct': round(self.passing_pct, 1),
            'rushing': self.rushing,
            'rushing_pct': round(self.rushing_pct, 1),
            'penalty': self.penalty,
            'penalty_pct': round(self.penalty_pct, 1),
            'plays_per_first_down': round(self.plays_per_first_down, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
