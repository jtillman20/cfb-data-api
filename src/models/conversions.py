from app import db


class ThirdDowns(db.Model):
    __tablename__ = 'third_downs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    conversions = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def conversion_pct(self) -> float:
        if self.attempts:
            return self.conversions / self.attempts * 100
        return 0.0

    @property
    def play_pct(self) -> float:
        if self.plays:
            return self.attempts / self.plays * 100
        return 0.0

    def __add__(self, other: 'ThirdDowns') -> 'ThirdDowns':
        """
        Add two ThirdDowns objects to combine multiple years of data.

        Args:
            other (ThirdDowns): Data about a team's third down
                offense/defense

        Returns:
            ThirdDowns: self
        """
        self.games += other.games
        self.attempts += other.attempts
        self.conversions += other.conversions
        self.plays += other.plays

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'attempts': self.attempts,
            'conversions': self.conversions,
            'conversion_pct': round(self.conversion_pct, 2),
            'play_pct': round(self.play_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
