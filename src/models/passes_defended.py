from app import db


class PassesDefended(db.Model):
    __tablename__ = 'passes_defended'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    games = db.Column(db.Integer, nullable=False)
    ints = db.Column(db.Integer, nullable=False)
    passes_broken_up = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    incompletions = db.Column(db.Integer, nullable=False)

    @property
    def passes_defended(self) -> int:
        return self.ints + self.passes_broken_up

    @property
    def passes_defended_per_game(self) -> float:
        if self.games:
            return self.passes_defended / self.games
        return 0.0

    @property
    def int_pct(self) -> float:
        if self.passes_defended:
            return self.ints / self.passes_defended * 100
        return 0.0

    @property
    def passes_defended_pct(self) -> float:
        if self.attempts:
            return self.passes_defended / self.attempts * 100
        return 0.0

    @property
    def forced_incompletion_pct(self) -> float:
        if self.incompletions:
            return self.passes_defended / self.incompletions * 100
        return 0.0

    def __add__(self, other: 'PassesDefended') -> 'PassesDefended':
        """
        Add two PassesDefended objects to combine multiple years of data.

        Args:
            other (PassesDefended): Data about a team's passes defended

        Returns:
            Interceptions: self
        """
        self.games += other.games
        self.ints += other.ints
        self.passes_broken_up += other.passes_broken_up
        self.attempts += other.attempts
        self.incompletions += other.incompletions

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'games': self.games,
            'ints': self.ints,
            'int_pct': round(self.int_pct, 2),
            'passes_broken_up': self.passes_broken_up,
            'passes_defended': self.passes_defended,
            'passes_defended_per_game': round(self.passes_defended_per_game, 2),
            'attempts': self.attempts,
            'passes_defended_pct': round(self.passes_defended_pct, 2),
            'incompletions': self.incompletions,
            'forced_incompletion_pct': round(self.forced_incompletion_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
