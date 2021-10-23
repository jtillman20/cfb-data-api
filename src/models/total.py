from app import db


class Total(db.Model):
    __tablename__ = 'total'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    opponents_games = db.Column(db.Integer, nullable=False)
    opponents_plays = db.Column(db.Integer, nullable=False)
    opponents_yards = db.Column(db.Integer, nullable=False)

    @property
    def plays_per_game(self) -> float:
        if self.games:
            return self.plays / self.games
        return 0.0

    @property
    def yards_per_play(self) -> float:
        if self.plays:
            return self.yards / self.plays
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def opponents_plays_per_game(self) -> float:
        if self.opponents_games:
            return self.opponents_plays / self.opponents_games
        return 0.0

    @property
    def opponents_yards_per_play(self) -> float:
        if self.opponents_plays:
            return self.opponents_yards / self.opponents_plays
        return 0.0

    @property
    def opponents_yards_per_game(self) -> float:
        if self.opponents_games:
            return self.opponents_yards / self.opponents_games
        return 0.0

    @property
    def relative_yards_per_play(self) -> float:
        if self.opponents_yards_per_play:
            return (self.yards_per_play / self.opponents_yards_per_play) * 100
        return 0.0

    @property
    def relative_yards_per_game(self) -> float:
        if self.opponents_yards_per_game:
            return (self.yards_per_game / self.opponents_yards_per_game) * 100
        return 0.0

    def __add__(self, other: 'Total') -> 'Total':
        """
        Add two Total objects to combine multiple years of data.

        Args:
            other (Total): Data about a team's total offense/defense

        Returns:
            Total: self
        """
        self.games += other.games
        self.plays += other.plays
        self.yards += other.yards
        self.opponents_games += other.opponents_games
        self.opponents_plays += other.opponents_plays
        self.opponents_yards += other.opponents_yards

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'plays': self.attempts,
            'plays_per_game': round(self.plays, 1),
            'yards': self.yards,
            'yards_per_play': round(self.yards_per_play, 2),
            'yards_per_game': round(self.yards_per_game, 1),
            'relative_yards_per_play': round(self.relative_yards_per_play, 1),
            'relative_yards_per_game': round(self.relative_yards_per_game, 1)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
