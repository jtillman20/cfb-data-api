from app import db


class Passing(db.Model):
    __tablename__ = 'passing'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    completions = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    tds = db.Column(db.Integer, nullable=False)
    ints = db.Column(db.Integer, nullable=False)

    @property
    def attempts_per_game(self) -> float:
        if self.games:
            return self.attempts / self.games
        return 0.0

    @property
    def completions_per_game(self) -> float:
        if self.games:
            return self.completions / self.games
        return 0.0

    @property
    def completion_pct(self) -> float:
        if self.attempts:
            return self.completions / self.attempts * 100
        return 0.0

    @property
    def yards_per_attempt(self) -> float:
        if self.attempts:
            return self.yards / self.attempts
        return 0.0

    @property
    def yards_per_completion(self) -> float:
        if self.completions:
            return self.yards / self.completions
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0

    @property
    def td_pct(self) -> float:
        if self.attempts:
            return self.tds / self.attempts * 100
        return 0.0

    @property
    def int_pct(self) -> float:
        if self.attempts:
            return self.ints / self.attempts * 100
        return 0.0

    @property
    def td_int_ratio(self) -> float:
        if self.ints:
            return self.tds / self.ints
        return 0.0

    @property
    def rating(self) -> float:
        if self.attempts:
            return (self.yards * 8.4 + self.completions * 100 + self.tds
                    * 330 - self.ints * 200) / self.attempts
        return 0.0

    def __add__(self, other: 'Passing') -> 'Passing':
        """
        Add two Passing objects to combine multiple years of data.

        Args:
            other (Passing): Data about a team's passing offense/defense

        Returns:
            Passing: self
        """
        self.games += other.games
        self.attempts += other.attempts
        self.completions += other.completions
        self.yards += other.yards
        self.tds += other.tds
        self.ints += other.ints

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
            'completions': self.completions,
            'completions_per_game': round(self.completions_per_game, 2),
            'completion_pct': round(self.completion_pct, 2),
            'yards': self.yards,
            'yards_per_attempt': round(self.yards_per_attempt, 2),
            'yards_per_completion': round(self.yards_per_completion, 2),
            'yards_per_game': round(self.yards_per_game, 1),
            'tds': self.tds,
            'td_pct': round(self.td_pct, 2),
            'ints': self.ints,
            'int_pct': round(self.int_pct, 2),
            'td_int_ratio': round(self.td_int_ratio, 2),
            'rating': round(self.rating, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
