from operator import attrgetter

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team


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

    @classmethod
    def add_kickoffs(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get kickoff and opponent kickoff stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding kickoff stats
            end_year (int): Year to stop adding kickoff stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding kickoff stats for {year}')
            cls.add_kickoffs_for_one_year(year=year)

    @classmethod
    def add_kickoffs_for_one_year(cls, year: int) -> None:
        """
        Get kickoff and opponent kickoff stats for all teams for
        one year and add them to the database.

        Args:
            year (int): Year to add kickoff stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            kickoffs = []

            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='29')
            kickoff_data = scraper.parse_html_data(html_content=html_content)

            for item in kickoff_data:
                team = Team.query.filter_by(name=item[1]).first()

                kickoffs.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    kickoffs=item[3],
                    yards=item[4],
                    touchbacks=item[6],
                    out_of_bounds=item[8],
                    onside=item[9]
                ))

            for team_kickoffs in sorted(kickoffs, key=attrgetter('team_id')):
                db.session.add(team_kickoffs)

        db.session.commit()

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
