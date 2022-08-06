from numpy import sum

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

    @classmethod
    def get_scoring(cls, side_of_ball: str, start_year: int,
                    end_year: int = None, team: str = None) -> list['Scoring']:
        """
        Get scoring offense or defense for qualifying teams for the
        given years. If team is provided, only get scoring data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting scoring data
            end_year (int): Year to stop getting scoring data
            team (str): Team for which to get scoring data

        Returns:
            list[Scoring]: Scoring offense or defense for all teams or
                only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            scoring = query.filter_by(name=team).all()
            return [sum(scoring)] if scoring else []

        scoring = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_scoring = query.filter_by(name=team_name).all()

            if team_scoring:
                scoring[team_name] = sum(team_scoring)

        return [scoring[team] for team in sorted(scoring.keys())]

    @classmethod
    def add_scoring(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get scoring offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding scoring stats
            end_year (int): Year to stop adding scoring stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding scoring stats for {year}')
            cls.add_scoring_for_one_year(year=year)
            cls.add_opponent_scoring(year=year)

    @classmethod
    def add_scoring_for_one_year(cls, year: int) -> None:
        """
        Get scoring offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to add scoring stats
        """
        scoring = {}

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
                for team in Team.get_teams(year=year)
            }

        offense = scoring['offense']
        defense = scoring['defense']

        for game in Game.get_games(year=year):
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
        for team_scoring in cls.query.filter_by(year=year).all():
            team = team_scoring.team.name

            for game in Game.get_games(year=year, team=team):
                if team == game.away_team:
                    opponent_name = game.home_team
                    points = game.away_score
                else:
                    opponent_name = game.away_team
                    points = game.home_score

                opponent_query = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name)

                if opponent_query.first() is not None:
                    opponent = Team.query.filter_by(name=opponent_name).first()
                    side_of_ball = team_scoring.side_of_ball
                    opposite_side_of_ball = ('defense' if side_of_ball == 'offense'
                                             else 'offense')

                    opponent_scoring = cls.query.filter_by(
                        team_id=opponent.id,
                        year=year,
                        side_of_ball=opposite_side_of_ball,
                    ).first()

                    opponent_points = opponent_scoring.points - points
                    team_scoring.opponents_points += opponent_points
                    opponent_games = opponent_scoring.games
                    team_scoring.opponents_games += opponent_games - 1

        db.session.commit()

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

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'points': self.points,
            'points_per_game': round(self.points_per_game, 1),
            'relative_points_per_game': round(self.relative_points_per_game, 1)
        }
