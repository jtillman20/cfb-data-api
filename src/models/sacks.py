from app import db


class Sacks(db.Model):
    __tablename__ = 'sacks'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    sacks = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    pass_attempts = db.Column(db.Integer, nullable=False)

    @property
    def sacks_per_game(self) -> float:
        if self.games:
            return self.sacks / self.games
        return 0.0

    @property
    def sack_pct(self) -> float:
        attempts = self.sacks + self.pass_attempts
        if attempts:
            return self.sacks / attempts * 100
        return 0.0

    @property
    def yards_per_sack(self) -> float:
        if self.sacks:
            return self.yards / self.sacks
        return 0.0

    def __add__(self, other: 'Sacks') -> 'Sacks':
        """
        Add two Sacks objects to combine multiple years of data.

        Args:
            other (Sacks): Data about a team's sacks or opponent's sacks

        Returns:
            Sacks: self
        """
        self.games += other.games
        self.sacks += other.sacks
        self.yards += other.yards
        self.pass_attempts += other.pass_attempts

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'sacks': self.sacks,
            'sacks_per_game': round(self.sacks_per_game, 2),
            'yards': self.yards,
            'yards_per_sack': round(self.yards_per_sack, 2),
            'pass_attempts': self.pass_attempts,
            'sack_pct': round(self.sack_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
