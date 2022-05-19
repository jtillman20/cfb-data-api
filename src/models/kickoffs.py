from app import db


class Kickoffs(db.Model):
    __tablename__ = 'kickoffs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    kickoffs = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    touchbacks = db.Column(db.Integer, nullable=False)
    out_of_bounds = db.Column(db.Integer, nullable=False)
    onside = db.Column(db.Integer, nullable=False)

    @property
    def yards_per_kickoff(self) -> float:
        if self.kickoffs:
            return self.yards / self.kickoffs
        return 0.0

    @property
    def touchback_pct(self) -> float:
        if self.kickoffs:
            return self.touchbacks / self.kickoffs * 100
        return 0.0

    @property
    def out_of_bounds_pct(self) -> float:
        if self.kickoffs:
            return self.out_of_bounds / self.kickoffs * 100
        return 0.0

    @property
    def onside_pct(self) -> float:
        if self.kickoffs:
            return self.onside / self.kickoffs * 100
        return 0.0

    def __add__(self, other: 'Kickoffs') -> 'Kickoffs':
        """
        Add two Kickoffs objects to combine multiple years of data.

        Args:
            other (Kickoffs): Data about a team's kickoffs or opponent
                kickoffs

        Returns:
            Kickoffs: self
        """
        self.games += other.games
        self.kickoffs += other.kickoffs
        self.yards += other.yards
        self.touchbacks += other.touchbacks
        self.out_of_bounds += other.out_of_bounds
        self.onside += other.onside

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'kickoffs': self.kickoffs,
            'yards': self.yards,
            'yards_per_kickoff': round(self.yards_per_kickoff, 2),
            'touchbacks': self.kickoffs,
            'touchback_pct': round(self.touchback_pct, 2),
            'out_of_bounds': self.kickoffs,
            'out_of_bounds_pct': round(self.out_of_bounds_pct, 2),
            'onside': self.kickoffs,
            'onside_pct': round(self.onside_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
