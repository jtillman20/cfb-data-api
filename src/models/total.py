from typing import Union

from app import db
from .game import Game
from .team import Team


class Total(db.Model):
    __tablename__ = 'total'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    opponents_games = db.Column(db.Integer, nullable=False)
    opponents_plays = db.Column(db.Integer, nullable=False)
    opponents_yards = db.Column(db.Integer, nullable=False)

    @property
    def plays_per_game(self) -> float:
        if self.games:
            return self.plays / self.games
        return 0.0

    @property
    def yards_per_play(self) -> float:
        if self.plays:
            return self.yards / self.plays
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def opponents_plays_per_game(self) -> float:
        if self.opponents_games:
            return self.opponents_plays / self.opponents_games
        return 0.0

    @property
    def opponents_yards_per_play(self) -> float:
        if self.opponents_plays:
            return self.opponents_yards / self.opponents_plays
        return 0.0

    @property
    def opponents_yards_per_game(self) -> float:
        if self.opponents_games:
            return self.opponents_yards / self.opponents_games
        return 0.0

    @property
    def relative_yards_per_play(self) -> float:
        if self.opponents_yards_per_play:
            return (self.yards_per_play / self.opponents_yards_per_play) * 100
        return 0.0

    @property
    def relative_yards_per_game(self) -> float:
        if self.opponents_yards_per_game:
            return (self.yards_per_game / self.opponents_yards_per_game) * 100
        return 0.0

    def __add__(self, other: 'Total') -> 'Total':
        """
        Add two Total objects to combine multiple years of data.

        Args:
            other (Total): Data about a team's total offense/defense

        Returns:
            Total: self
        """
        self.games += other.games
        self.plays += other.plays
        self.yards += other.yards
        self.opponents_games += other.opponents_games
        self.opponents_plays += other.opponents_plays
        self.opponents_yards += other.opponents_yards

        return self

    @classmethod
    def add_total(cls, start_year: int, end_year: int) -> None:
        """
        Get total offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start getting total stats
            end_year (int): Year to stop getting total stats
        """
        for year in range(start_year, end_year + 1):
            print(f'Adding total stats for {year}')
            cls.add_total_for_one_year(year=year)
            cls.add_opponent_total(year=year)

    @classmethod
    def add_total_for_one_year(cls, year: int) -> None:
        """
        Get total offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to get total stats
        """
        teams = Team.get_teams(year=year)

        for team in teams:
            games = Game.get_games(year=year, team=team.name)
            game_stats = [game.stats[0] for game in games]

            for side_of_ball in ['offense', 'defense']:
                plays = 0
                yards = 0

                for stats in game_stats:
                    home_team = stats.game.home_team

                    if side_of_ball == 'offense':
                        side = 'home' if home_team == team.name else 'away'
                    else:
                        side = 'away' if home_team == team.name else 'home'

                    plays += getattr(stats, f'{side}_plays')
                    yards += getattr(stats, f'{side}_total_yards')

                db.session.add(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=len(games),
                    plays=plays,
                    yards=yards,
                    opponents_games=0,
                    opponents_plays=0,
                    opponents_yards=0
                ))

        db.session.commit()

    @classmethod
    def add_opponent_total(cls, year: int) -> None:
        """
        Get total offense and defense for all team's opponents
        and add them to the database.

        Args:
            year (int): Year to get total stats
        """
        total = cls.query.filter_by(year=year).all()

        for team_total in total:
            team = team_total.team.name
            schedule = Game.get_games(year=year, team=team)

            for game in schedule:
                game_stats = game.stats[0]

                if team == game.away_team:
                    opponent_name = game.home_team
                    plays = game_stats.away_plays
                    yards = game_stats.away_total_yards
                else:
                    opponent_name = game.away_team
                    plays = game_stats.home_plays
                    yards = game_stats.home_total_yards

                opponent_query = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name)

                if opponent_query.first() is not None:
                    side_of_ball = team_total.side_of_ball
                    opposite_side_of_ball = 'defense' \
                        if side_of_ball == 'offense' else 'offense'

                    opponent_defense = cls.query.filter_by(
                        year=year, side_of_ball=opposite_side_of_ball).join(
                        Team).filter_by(name=opponent_name).first()

                    opponent_games = opponent_defense.games
                    team_total.opponents_games += opponent_games - 1

                    opponent_plays = opponent_defense.plays - plays
                    team_total.opponents_plays += opponent_plays

                    opponent_yards = opponent_defense.yards - yards
                    team_total.opponents_yards += opponent_yards

        db.session.commit()

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'plays': self.attempts,
            'plays_per_game': round(self.plays, 1),
            'yards': self.yards,
            'yards_per_play': round(self.yards_per_play, 2),
            'yards_per_game': round(self.yards_per_game, 1),
            'relative_yards_per_play': round(self.relative_yards_per_play, 1),
            'relative_yards_per_game': round(self.relative_yards_per_game, 1)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
