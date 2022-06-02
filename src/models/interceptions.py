from app import db


class Interceptions(db.Model):
    __tablename__ = 'interceptions'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    games = db.Column(db.Integer, nullable=False)
    ints = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    tds = db.Column(db.Integer, nullable=False)

    @property
    def ints_per_game(self) -> float:
        if self.games:
            return self.ints / self.games
        return 0.0

    @property
    def yards_per_int(self) -> float:
        if self.ints:
            return self.yards / self.ints
        return 0.0

    @property
    def td_pct(self) -> float:
        if self.ints:
            return self.tds / self.ints * 100
        return 0.0

    def __add__(self, other: 'Interceptions') -> 'Interceptions':
        """
        Add two Interceptions objects to combine multiple years of data.

        Args:
            other (Interceptions): Data about a team's interceptions

        Returns:
            Interceptions: self
        """
        self.games += other.games
        self.ints += other.ints
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
            'ints': self.ints,
            'ints_per_game': round(self.ints_per_game, 2),
            'yards': self.yards,
            'yards_per_int': round(self.yards_per_int, 2),
            'tds': self.tds,
            'td_pct': round(self.td_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
