from operator import attrgetter

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team
from .total import Total


class ThirdDowns(db.Model):
    __tablename__ = 'third_downs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    conversions = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def conversion_pct(self) -> float:
        if self.attempts:
            return self.conversions / self.attempts * 100
        return 0.0

    @property
    def play_pct(self) -> float:
        if self.plays:
            return self.attempts / self.plays * 100
        return 0.0

    @classmethod
    def add_third_downs(cls, start_year: int = None,
                        end_year: int = None) -> None:
        """
        Get third down offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding third down stats
            end_year (int): Year to stop adding third down stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding third down stats for {year}')
            cls.add_third_downs_for_one_year(year=year)

    @classmethod
    def add_third_downs_for_one_year(cls, year: int) -> None:
        """
        Get third down offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to add third down stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            third_downs = []

            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='25')
            third_down_data = scraper.parse_html_data(
                html_content=html_content)

            for item in third_down_data:
                team = Team.query.filter_by(name=item[1]).first()
                total = Total.get_total(
                    side_of_ball=side_of_ball, start_year=year, team=team.name)

                third_downs.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    attempts=item[3],
                    conversions=item[4],
                    plays=total.plays
                ))

            for team_third_downs in sorted(
                    third_downs, key=attrgetter('team_id')):
                db.session.add(team_third_downs)

        db.session.commit()

    def __add__(self, other: 'ThirdDowns') -> 'ThirdDowns':
        """
        Add two ThirdDowns objects to combine multiple years of data.

        Args:
            other (ThirdDowns): Data about a team's third down
                offense/defense

        Returns:
            ThirdDowns: self
        """
        self.games += other.games
        self.attempts += other.attempts
        self.conversions += other.conversions
        self.plays += other.plays

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'attempts': self.attempts,
            'conversions': self.conversions,
            'conversion_pct': round(self.conversion_pct, 2),
            'play_pct': round(self.play_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
