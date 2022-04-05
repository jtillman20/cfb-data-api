from app import db


class Punting(db.Model):
    __tablename__ = 'punting'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    punts = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def punts_per_game(self) -> float:
        if self.games:
            return self.punts / self.games
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def yards_per_punt(self) -> float:
        if self.punts:
            return self.yards / self.punts
        return 0.0

    @property
    def plays_per_punt(self) -> float:
        if self.punts:
            return self.plays / self.punts
        return 0.0

    def __add__(self, other: 'Punting') -> 'Punting':
        """
        Add two Punting objects to combine multiple years of data.

        Args:
            other (Punting): Data about a team's punting or opponent
                punting

        Returns:
            Punting: self
        """
        self.games += other.games
        self.punts += other.punts
        self.yards += other.yards
        self.plays += other.plays

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'punts': self.punts,
            'punts_per_game': round(self.punts_per_game, 2),
            'yards': self.yards,
            'yards_per_game': round(self.yards_per_game, 1),
            'yards_per_punt': round(self.yards_per_punt, 2),
            'plays_per_punt': round(self.plays_per_punt, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
