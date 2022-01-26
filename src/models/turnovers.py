from app import db


class Turnovers(db.Model):
    __tablename__ = 'turnovers'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    games = db.Column(db.Integer, nullable=False)
    ints = db.Column(db.Integer, nullable=False)
    fumbles = db.Column(db.Integer, nullable=False)
    opponent_ints = db.Column(db.Integer, nullable=False)
    opponent_fumbles = db.Column(db.Integer, nullable=False)

    @property
    def giveaways(self) -> int:
        return self.ints + self.fumbles

    @property
    def giveaways_per_game(self) -> float:
        if self.games:
            return self.giveaways / self.games
        return 0.0

    @property
    def takeaways(self) -> int:
        return self.opponent_ints + self.opponent_fumbles

    @property
    def takeaways_per_game(self) -> float:
        if self.games:
            return self.takeaways / self.games
        return 0.0

    @property
    def margin(self) -> int:
        return self.takeaways - self.giveaways

    @property
    def margin_per_game(self) -> float:
        if self.games:
            return self.margin / self.games
        return 0.0

    def __add__(self, other: 'Turnovers') -> 'Turnovers':
        """
        Add two Turnovers objects to combine multiple years of data.

        Args:
            other (Turnovers): Data about a team's turnovers and
                opponent's turnovers

        Returns:
            Turnovers: self
        """
        self.games += other.games
        self.ints += other.ints
        self.fumbles += other.fumbles
        self.opponent_ints += other.opponent_ints
        self.opponent_fumbles += other.opponent_fumbles

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'games': self.games,
            'ints': self.ints,
            'fumbles': self.fumbles,
            'giveaways': self.giveaways,
            'giveaways_per_game': round(self.giveaways_per_game, 2),
            'opponent_ints': self.opponent_ints,
            'opponent_fumbles': self.opponent_fumbles,
            'takeaways': self.takeaways,
            'takeaways_per_game': round(self.takeaways_per_game, 2),
            'margin': self.margin,
            'margin_per_game': round(self.margin_per_game, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
