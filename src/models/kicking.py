from app import db


class FieldGoals(db.Model):
    __tablename__ = 'field_goals'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    field_goals = db.Column(db.Integer, nullable=False)

    @property
    def attempts_per_game(self) -> float:
        if self.games:
            return self.attempts / self.games
        return 0.0

    @property
    def field_goals_per_game(self) -> float:
        if self.games:
            return self.field_goals / self.games
        return 0.0

    @property
    def pct(self) -> float:
        if self.attempts:
            return self.field_goals / self.attempts * 100
        return 0.0

    def __add__(self, other: 'FieldGoals') -> 'FieldGoals':
        """
        Add two FieldGoals objects to combine multiple years of data.

        Args:
            other (FieldGoals): Data about a team's field goals or
                opponent field goals

        Returns:
            FieldGoals: self
        """
        self.games += other.games
        self.attempts += other.attempts
        self.field_goals += other.field_goals

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'attempts': self.attempts,
            'attempts_per_game': round(self.attempts_per_game, 2),
            'field_goals': self.field_goals,
            'field_goals_per_game': round(self.field_goals_per_game, 1),
            'pct': round(self.pct, 2),
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
