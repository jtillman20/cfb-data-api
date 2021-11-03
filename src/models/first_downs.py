from app import db


class FirstDowns(db.Model):
    __tablename__ = 'first_downs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    passing = db.Column(db.Integer, nullable=False)
    rushing = db.Column(db.Integer, nullable=False)
    penalty = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def total(self) -> int:
        return self.passing + self.rushing + self.penalty

    @property
    def total_per_game(self) -> float:
        if self.games:
            return self.total / self.games
        return 0.0

    @property
    def passing_pct(self) -> float:
        if self.total:
            return self.passing / self.total * 100
        return 0.0

    @property
    def rushing_pct(self) -> float:
        if self.total:
            return self.rushing / self.total * 100
        return 0.0

    @property
    def penalty_pct(self) -> float:
        if self.total:
            return self.penalty / self.total * 100
        return 0.0

    @property
    def plays_per_first_down(self) -> float:
        if self.plays:
            return self.plays / self.total
        return 0.0

    def __add__(self, other: 'FirstDowns') -> 'FirstDowns':
        """
        Add two FirstDowns objects to combine multiple years of data.

        Args:
            other (Total): Data about a team's first down offense/defense

        Returns:
            Total: self
        """
        self.games += other.games
        self.passing += other.passing
        self.rushing += other.rushing
        self.penalty += other.penalty
        self.plays += other.plays

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'total': self.total,
            'total_per_game': round(self.total_per_game, 1),
            'passing': self.passing,
            'passing_pct': round(self.passing_pct, 1),
            'rushing': self.rushing,
            'rushing_pct': round(self.rushing_pct, 1),
            'penalty': self.penalty,
            'penalty_pct': round(self.penalty_pct, 1),
            'plays_per_first_down': round(self.plays_per_first_down, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
