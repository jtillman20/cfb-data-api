from app import db


class RPI(db.Model):
    __tablename__ = 'rpi'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    year = db.Column(db.Integer, nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    ties = db.Column(db.Integer, nullable=False)
    opponent_win_pct = db.Column(db.Integer, nullable=False)
    opponents_opponent_win_pct = db.Column(db.Integer, nullable=True)
    opponent_games = db.Column(db.Integer, nullable=True)

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.ties

    @property
    def win_pct(self) -> float:
        if self.games:
            return (self.wins + self.ties * 0.5) / self.games
        return 0.0

    @property
    def opponent_avg_win_pct(self) -> float:
        if self.games:
            return self.opponent_win_pct / self.games
        return 0.0

    @property
    def opponents_opponent_avg_win_pct(self) -> float:
        if self.opponent_games:
            return self.opponents_opponent_win_pct / self.opponent_games
        return 0.0

    @property
    def sos(self) -> float:
        return self.opponent_avg_win_pct * 0.55 + \
               self.opponents_opponent_avg_win_pct * 0.45

    @property
    def rpi(self) -> float:
        return self.win_pct * 0.35 + self.sos * 0.65

    def __add__(self, other: 'RPI') -> 'RPI':
        """
        Add two RPI objects to combine multiple years of data.

        Args:
            other (RPI): Data about a team's RPI rating

        Returns:
            RPI: self
        """
        self.wins += other.wins
        self.losses += other.losses
        self.ties += other.ties
        self.opponent_win_pct += other.opponent_win_pct
        self.opponents_opponent_win_pct += other.opponents_opponent_win_pct
        self.opponent_games += other.opponent_games

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'rpi': round(self.rpi, 4),
            'sos': round(self.sos, 4),
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
