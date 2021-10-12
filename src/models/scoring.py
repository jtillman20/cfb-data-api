from typing import Union

from app import db
from .game import Game
from .team import Team


class Scoring(db.Model):
    __tablename__ = 'scoring'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    games = db.Column(db.Integer, nullable=False)
    opponents_points = db.Column(db.Integer, nullable=False)
    opponents_games = db.Column(db.Integer, nullable=False)

    @property
    def points_per_game(self) -> float:
        if self.games:
            return self.points / self.games
        return 0.0

    @property
    def opponents_points_per_game(self) -> float:
        if self.opponents_games:
            return self.opponents_points / self.opponents_games
        return 0.0

    @property
    def relative_points_per_game(self) -> float:
        if self.opponents_points_per_game:
            return (self.points_per_game / self.opponents_points_per_game) * 100
        return 0.0

    def __add__(self, other: 'Scoring') -> 'Scoring':
        """
        Add two Scoring objects to combine multiple years of data.

        Args:
            other (Scoring): Data about a team's scoring offense/defense

        Returns:
            Scoring: self
        """
        self.points += other.points
        self.games += other.games
        self.opponents_points += other.opponents_points
        self.opponents_games += other.opponents_games

        return self

    @classmethod
    def add_scoring(cls, start_year: int, end_year: int) -> None:
        """
        Get scoring offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start getting scoring stats
            end_year (int): Year to stop getting scoring stats
        """
        for year in range(start_year, end_year + 1):
            print(f'Adding scoring stats for {year}')
            cls.add_scoring_for_one_year(year=year)
            cls.add_opponent_scoring(year=year)

    @classmethod
    def add_scoring_for_one_year(cls, year: int) -> None:
        """
        Get scoring offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to get scoring stats
        """
        scoring = {}
        teams = Team.get_teams(year=year)

        for side_of_ball in ['offense', 'defense']:
            scoring[side_of_ball] = {
                team.name: cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    points=0,
                    games=0,
                    opponents_points=0,
                    opponents_games=0
                )
                for team in teams
            }

        offense = scoring['offense']
        defense = scoring['defense']
        games = Game.get_games(year=year)

        for game in games:
            home_team = game.home_team
            away_team = game.away_team

            if home_team in offense:
                home_offense = offense[home_team]
                home_defense = defense[home_team]

                home_offense.games += 1
                home_offense.points += game.home_score
                home_defense.games += 1
                home_defense.points += game.away_score

            if away_team in defense:
                away_offense = offense[away_team]
                away_defense = defense[away_team]

                away_offense.games += 1
                away_offense.points += game.away_score
                away_defense.games += 1
                away_defense.points += game.home_score

        for side_of_ball in ['offense', 'defense']:
            for team, team_scoring in scoring[side_of_ball].items():
                db.session.add(team_scoring)

        db.session.commit()

    @classmethod
    def add_opponent_scoring(cls, year: int) -> None:
        """
        Get scoring offense and defense for all team's opponents
        and add them to the database.

        Args:
            year (int): Year to get scoring stats
        """
        scoring = cls.query.filter_by(year=year).all()

        for team_scoring in scoring:
            team = team_scoring.team.name
            schedule = Game.get_games(year=year, team=team)

            for game in schedule:
                if team == game.away_team:
                    opponent_name = game.home_team
                    points = game.away_score
                else:
                    opponent_name = game.away_team
                    points = game.home_score

                opponent_query = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name)

                if opponent_query.first() is not None:
                    side_of_ball = team_scoring.side_of_ball

                    if side_of_ball == 'offense':
                        opponent_defense = cls.query.filter_by(
                            year=year, side_of_ball='defense').join(
                            Team).filter_by(name=opponent_name).first()

                        opponent_points = opponent_defense.points - points
                        team_scoring.opponents_points += opponent_points
                        opponent_games = opponent_defense.games
                        team_scoring.opponents_games += opponent_games - 1

                    else:
                        opponent_offense = cls.query.filter_by(
                            year=year, side_of_ball='offense').join(
                            Team).filter_by(name=opponent_name).first()

                        opponent_points = opponent_offense.points - points
                        team_scoring.opponents_points += opponent_points
                        opponent_games = opponent_offense.games
                        team_scoring.opponents_games += opponent_games - 1

        db.session.commit()

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'games': self.games,
            'points': self.points,
            'points_per_game': round(self.points_per_game, 1),
            'relative_points_per_game': round(self.relative_points_per_game, 1)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
