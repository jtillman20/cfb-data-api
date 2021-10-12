from app import db


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
