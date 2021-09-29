from app import db


class SRS(db.Model):
    __tablename__ = 'srs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    year = db.Column(db.Integer, nullable=False)
    scoring_margin = db.Column(db.Integer, nullable=False)
    opponent_rating = db.Column(db.Integer, nullable=False)
    wins = db.Column(db.Integer, nullable=True)
    losses = db.Column(db.Integer, nullable=True)
    ties = db.Column(db.Integer, nullable=True)

    @property
    def avg_scoring_margin(self) -> float:
        if self.games:
            return self.scoring_margin / self.games
        return 0.0

    @property
    def sos(self) -> float:
        if self.games:
            return self.opponent_rating / self.games
        return 0.0

    @property
    def srs(self) -> float:
        return self.avg_scoring_margin + self.sos

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.ties

    def __add__(self, other: 'SRS') -> 'SRS':
        """
        Add two SRS objects to combine multiple years of data.

        Args:
            other (SRS): Data about a team's SRS rating

        Returns:
            SRS: self
        """
        self.scoring_margin += other.scoring_margin
        self.opponent_rating += other.opponent_rating
        self.wins += other.wins
        self.losses += other.losses
        self.ties += other.ties

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'srs': round(self.srs, 2),
            'sos': round(self.sos, 2),
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
