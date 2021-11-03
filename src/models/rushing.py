from typing import Union

from app import db
from .first_downs import FirstDowns
from .game import Game
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
    first_downs = db.Column(db.Integer, nullable=False)
    opponents_games = db.Column(db.Integer, nullable=False)
    opponents_attempts = db.Column(db.Integer, nullable=False)
    opponents_yards = db.Column(db.Integer, nullable=False)

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

    @property
    def first_down_pct(self) -> float:
        if self.attempts:
            return self.first_downs / self.attempts * 100
        return 0.0

    @property
    def opponents_yards_per_game(self) -> float:
        if self.opponents_games:
            return self.opponents_yards / self.opponents_games
        return 0.0

    @property
    def opponents_yards_per_attempt(self) -> float:
        if self.opponents_attempts:
            return self.opponents_yards / self.opponents_attempts
        return 0.0

    @property
    def relative_yards_per_game(self) -> float:
        if self.opponents_yards_per_game:
            return (self.yards_per_game / self.opponents_yards_per_game) * 100
        return 0.0

    @property
    def relative_yards_per_attempt(self) -> float:
        if self.opponents_yards_per_attempt:
            return (self.yards_per_attempt / self.opponents_yards_per_attempt) \
                   * 100
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
        self.opponents_games += other.opponents_games
        self.opponents_attempts += other.opponents_attempts
        self.opponents_yards += other.opponents_yards
        self.opponents_tds += other.opponents_tds

        return self

    @classmethod
    def get_rushing(cls, side_of_ball: str, start_year: int,
                    end_year: int = None, team: str = None
                    ) -> Union['Rushing', list['Rushing']]:
        """
        Get rushing offense or defense for qualifying teams for the
        given years. If team is provided, only get rushing data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting rushing data
            end_year (int): Year to stop getting rushing data
            team (str): Team for which to get rushing data

        Returns:
            Union[Rushing, list[Rushing]]: rushing offense or defense
                for all teams or only for one team
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
            rushing = query.filter_by(name=team).all()
            return sum(rushing[1:], rushing[0])

        rushing = {}
        for team_name in qualifying_teams:
            team_rushing = query.filter_by(name=team_name).all()

            if team_rushing:
                rushing[team_name] = sum(team_rushing[1:], team_rushing[0])

        return [rushing[team] for team in sorted(rushing.keys())]

    @classmethod
    def add_rushing(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get rushing offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding rushing stats
            end_year (int): Year to stop adding rushing stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding rushing stats for {year}')
            cls.add_rushing_for_one_year(year=year)
            cls.add_opponent_rushing(year=year)

    @classmethod
    def add_rushing_for_one_year(cls, year: int) -> None:
        """
        Get rushing offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to get rushing stats
        """
        teams = Team.get_teams(year=year)

        for team in teams:
            games = Game.get_games(year=year, team=team.name)
            game_stats = [game.stats[0] for game in games]

            for side_of_ball in ['offense', 'defense']:
                attempts = 0
                yards = 0
                tds = 0

                for stats in game_stats:
                    home_team = stats.game.home_team

                    if side_of_ball == 'offense':
                        side = 'home' if home_team == team.name else 'away'
                    else:
                        side = 'away' if home_team == team.name else 'home'

                    attempts += getattr(stats, f'{side}_rushing_attempts')
                    yards += getattr(stats, f'{side}_rushing_yards')
                    tds += getattr(stats, f'{side}_rushing_tds')

                first_downs = FirstDowns.get_first_downs(
                    side_of_ball=side_of_ball, start_year=year, team=team.name)

                db.session.add(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=len(games),
                    attempts=attempts,
                    yards=yards,
                    tds=tds,
                    first_downs=first_downs.rushing,
                    opponents_games=0,
                    opponents_attempts=0,
                    opponents_yards=0
                ))

        db.session.commit()

    @classmethod
    def add_opponent_rushing(cls, year: int) -> None:
        """
        Get rushing offense and defense for all team's opponents
        and add them to the database.

        Args:
            year (int): Year to add rushing stats
        """
        rushing = cls.query.filter_by(year=year).all()

        for team_rushing in rushing:
            team = team_rushing.team.name
            schedule = Game.get_games(year=year, team=team)

            for game in schedule:
                game_stats = game.stats[0]

                if team == game.away_team:
                    opponent_name = game.home_team
                    attempts = game_stats.away_rushing_attempts
                    yards = game_stats.away_rushing_yards
                else:
                    opponent_name = game.away_team
                    attempts = game_stats.home_rushing_attempts
                    yards = game_stats.home_rushing_yards

                opponent_query = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name)

                if opponent_query.first() is not None:
                    side_of_ball = team_rushing.side_of_ball
                    opposite_side_of_ball = 'defense' \
                        if side_of_ball == 'offense' else 'offense'

                    opponent_stats = cls.query.filter_by(
                        year=year, side_of_ball=opposite_side_of_ball).join(
                        Team).filter_by(name=opponent_name).first()

                    opponent_games = opponent_stats.games
                    team_rushing.opponents_games += opponent_games - 1

                    opponent_attempts = opponent_stats.attempts - attempts
                    team_rushing.opponents_attempts += opponent_attempts

                    opponent_yards = opponent_stats.yards - yards
                    team_rushing.opponents_yards += opponent_yards

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
            'td_pct': round(self.td_pct, 2),
            'first_down_pct': round(self.first_down_pct, 1),
            'relative_yards_per_attempt': round(
                self.relative_yards_per_attempt, 1),
            'relative_yards_per_game': round(self.relative_yards_per_game, 1)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
