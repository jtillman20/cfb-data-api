from app import db


class TacklesForLoss(db.Model):
    __tablename__ = 'tackles_for_loss'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    tackles_for_loss = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def tackles_for_loss_per_game(self) -> float:
        if self.games:
            return self.tackles_for_loss / self.games
        return 0.0

    @property
    def tackle_for_loss_pct(self) -> float:
        if self.plays:
            return self.tackles_for_loss / self.plays * 100
        return 0.0

    @property
    def yards_per_tackle_for_loss(self) -> float:
        if self.tackles_for_loss:
            return self.yards / self.tackles_for_loss
        return 0.0

    def __add__(self, other: 'TacklesForLoss') -> 'TacklesForLoss':
        """
        Add two TacklesForLoss objects to combine multiple years of
        data.

        Args:
            other (TacklesForLoss): Data about a team's tackles for
                loss or opponent's tackles for loss

        Returns:
            TacklesForLoss: self
        """
        self.games += other.games
        self.tackles_for_loss += other.tackles_for_loss
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
            'tackles_for_loss': self.tackles_for_loss,
            'tackles_for_loss_per_game': round(
                self.tackles_for_loss_per_game, 2),
            'yards': self.yards,
            'yards_per_tackle_for_loss': round(
                self.yards_per_tackle_for_loss, 2),
            'plays': self.plays,
            'tackle_for_loss_pct': round(self.tackle_for_loss_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
