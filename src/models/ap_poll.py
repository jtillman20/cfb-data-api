from app import db


class APPollRanking(db.Model):
    __tablename__ = 'ap_poll_ranking'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)
    first_place_votes = db.Column(db.Integer, nullable=False)
    previous_rank = db.Column(db.Integer, nullable=True)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    ties = db.Column(db.Integer, nullable=False)

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'year': self.year,
            'team': self.team.serialize(year=self.year),
            'week': self.week,
            'rank': self.rank,
            'points': self.points,
            'first_place_votes': self.first_place_votes,
            'previous_rank': self.previous_rank,
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties
        }
