from app import db


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
        data = {
            'id': self.id,
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

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
