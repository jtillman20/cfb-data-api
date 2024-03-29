from operator import attrgetter

from numpy import sum

from app import db
from scraper import CFBStatsScraper
from .passing import Passing
from .team import Team


class Sacks(db.Model):
    __tablename__ = 'sacks'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    sacks = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    pass_attempts = db.Column(db.Integer, nullable=False)

    @property
    def sacks_per_game(self) -> float:
        if self.games:
            return self.sacks / self.games
        return 0.0

    @property
    def sack_pct(self) -> float:
        attempts = self.sacks + self.pass_attempts
        if attempts:
            return self.sacks / attempts * 100
        return 0.0

    @property
    def yards_per_sack(self) -> float:
        if self.sacks:
            return self.yards / self.sacks
        return 0.0

    @classmethod
    def get_sacks(cls, side_of_ball: str, start_year: int, end_year: int = None,
                  team: str = None) -> list['Sacks']:
        """
        Get sacks or opponent sacks for qualifying teams for the given
        years. If team is provided, only get sack data for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting sack data
            end_year (int): Year to stop getting sack data
            team (str): Team for which to get sack data

        Returns:
            list[Sacks]: Sacks or opponent sacks for all teams or only
                for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            sacks = query.filter_by(name=team).all()
            return [sum(sacks)] if sacks else []

        sacks = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_sacks = query.filter_by(name=team_name).all()

            if team_sacks:
                sacks[team_name] = sum(team_sacks)

        return [sacks[team] for team in sorted(sacks.keys())]

    @classmethod
    def add_sacks(cls, start_year: int, end_year: int = None) -> None:
        """
        Get sack and opponent sack stats for all teams for the given
        years and add them to the database.

        Args:
            start_year (int): Year to start adding sack stats
            end_year (int): Year to stop adding sack stats
        """
        if end_year is None:
            end_year = start_year
        years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding sack stats for {year}')
            cls.add_sacks_for_one_year(year=year)

    @classmethod
    def add_sacks_for_one_year(cls, year: int) -> None:
        """
        Get sack and opponent sack stats for all teams for one year and
        add them to the database.

        Args:
            year (int): Year to add sack stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            sacks = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='20')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()
                opposite_side_of_ball = ('defense' if side_of_ball == 'offense'
                                         else 'offense')
                passing = Passing.query.filter_by(
                    team_id=team.id,
                    year=year,
                    side_of_ball=opposite_side_of_ball,
                ).first()

                sacks.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    sacks=item[3],
                    yards=item[4],
                    pass_attempts=passing.attempts
                ))

            for team_sacks in sorted(sacks, key=attrgetter('team_id')):
                db.session.add(team_sacks)

        db.session.commit()

    def __add__(self, other: 'Sacks') -> 'Sacks':
        """
        Add two Sacks objects to combine multiple years of data.

        Args:
            other (Sacks): Data about a team's sacks or opponent's sacks

        Returns:
            Sacks: self
        """
        self.games += other.games
        self.sacks += other.sacks
        self.yards += other.yards
        self.pass_attempts += other.pass_attempts

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'sacks': self.sacks,
            'sacks_per_game': round(self.sacks_per_game, 2),
            'yards': self.yards,
            'yards_per_sack': round(self.yards_per_sack, 2),
            'pass_attempts': self.pass_attempts,
            'sack_pct': round(self.sack_pct, 2)
        }
