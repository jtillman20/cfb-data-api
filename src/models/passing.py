from operator import attrgetter

from app import db
from scraper import CFBStatsScraper
from .team import Team


class Passing(db.Model):
    __tablename__ = 'passing'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    completions = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    tds = db.Column(db.Integer, nullable=False)
    ints = db.Column(db.Integer, nullable=False)

    @property
    def attempts_per_game(self) -> float:
        if self.games:
            return self.attempts / self.games
        return 0.0

    @property
    def completions_per_game(self) -> float:
        if self.games:
            return self.completions / self.games
        return 0.0

    @property
    def completion_pct(self) -> float:
        if self.attempts:
            return self.completions / self.attempts * 100
        return 0.0

    @property
    def yards_per_attempt(self) -> float:
        if self.attempts:
            return self.yards / self.attempts
        return 0.0

    @property
    def yards_per_completion(self) -> float:
        if self.completions:
            return self.yards / self.completions
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0

    @property
    def td_pct(self) -> float:
        if self.attempts:
            return self.tds / self.attempts * 100
        return 0.0

    @property
    def int_pct(self) -> float:
        if self.attempts:
            return self.ints / self.attempts * 100
        return 0.0

    @property
    def td_int_ratio(self) -> float:
        if self.ints:
            return self.tds / self.ints
        return 0.0

    @property
    def rating(self) -> float:
        if self.attempts:
            return (self.yards * 8.4 + self.completions * 100 + self.tds
                    * 330 - self.ints * 200) / self.attempts
        return 0.0

    def __add__(self, other: 'Passing') -> 'Passing':
        """
        Add two Passing objects to combine multiple years of data.

        Args:
            other (Passing): Data about a team's passing offense/defense

        Returns:
            Passing: self
        """
        self.games += other.games
        self.attempts += other.attempts
        self.completions += other.completions
        self.yards += other.yards
        self.tds += other.tds
        self.ints += other.ints

        return self

    @classmethod
    def add_passing(cls, start_year: int, end_year: int) -> None:
        """
        Get passing offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start getting passing stats
            end_year (int): Year to stop getting passing stats
        """
        for year in range(start_year, end_year + 1):
            print(f'Adding passing stats for {year}')
            cls.add_passing_for_one_year(year=year)

    @classmethod
    def add_passing_for_one_year(cls, year: int) -> None:
        """
        Get passing offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to get passing stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            passing = []

            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='02')
            passing_data = scraper.parse_html_data(
                html_content=html_content)

            for item in passing_data:
                team = Team.query.filter_by(name=item[1]).first()
                passing.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    attempts=item[3],
                    completions=item[4],
                    yards=item[6],
                    tds=item[8],
                    ints=item[9]
                ))

            for team_passing in sorted(passing, key=attrgetter('team_id')):
                db.session.add(team_passing)

        db.session.commit()

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'attempts': self.attempts,
            'attempts_per_game': round(self.attempts_per_game, 2),
            'completions': self.completions,
            'completions_per_game': round(self.completions_per_game, 2),
            'completion_pct': round(self.completion_pct, 2),
            'yards': self.yards,
            'yards_per_attempt': round(self.yards_per_attempt, 2),
            'yards_per_completion': round(self.yards_per_completion, 2),
            'yards_per_game': round(self.yards_per_game, 1),
            'tds': self.tds,
            'td_pct': round(self.td_pct, 2),
            'ints': self.ints,
            'int_pct': round(self.int_pct, 2),
            'td_int_ratio': round(self.td_int_ratio, 2),
            'rating': round(self.rating, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
