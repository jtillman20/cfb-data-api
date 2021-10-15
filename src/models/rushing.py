from app import db


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
            'yards': self.yards,
            'yards_per_attempt': round(self.yards_per_attempt, 2),
            'yards_per_game': round(self.yards_per_game, 1),
            'tds': self.tds,
            'td_pct': round(self.td_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
