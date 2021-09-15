from app import db


class Game(db.Model):
    __tablename__ = 'game'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date(), nullable=False)
    neutral_site = db.Column(db.Boolean, nullable=False)
    home_team = db.Column(db.String(100), nullable=False)
    home_score = db.Column(db.Integer, nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    away_score = db.Column(db.Integer, nullable=False)

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'year': self.year,
            'week': self.week,
            'date': self.date,
            'neutral_site': self.neutral_site,
            'home_team': self.team,
            'home_score': self.home_score,
            'away_team': self.away_team,
            'away_score': self.away_score
        }
