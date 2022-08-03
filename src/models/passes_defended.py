from operator import attrgetter

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .passing import Passing
from .team import Team


class PassesDefended(db.Model):
    __tablename__ = 'passes_defended'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    games = db.Column(db.Integer, nullable=False)
    ints = db.Column(db.Integer, nullable=False)
    passes_broken_up = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    incompletions = db.Column(db.Integer, nullable=False)

    @property
    def passes_defended(self) -> int:
        return self.ints + self.passes_broken_up

    @property
    def passes_defended_per_game(self) -> float:
        if self.games:
            return self.passes_defended / self.games
        return 0.0

    @property
    def int_pct(self) -> float:
        if self.passes_defended:
            return self.ints / self.passes_defended * 100
        return 0.0

    @property
    def passes_defended_pct(self) -> float:
        if self.attempts:
            return self.passes_defended / self.attempts * 100
        return 0.0

    @property
    def forced_incompletion_pct(self) -> float:
        if self.incompletions:
            return self.passes_defended / self.incompletions * 100
        return 0.0

    @classmethod
    def get_passes_defended(cls, start_year: int, end_year: int = None,
                            team: str = None) -> list['PassesDefended']:
        """
        Get passes defended for qualifying teams for the given years. If
        team is provided, only get passes defended data for that team.

        Args:
            start_year (int): Year to start getting passes defended data
            end_year (int): Year to stop getting passes defended data
            team (str): Team for which to get passes defended data

        Returns:
            list[PassesDefended]: Passes defended for all teams or only
                for one team
        """
        if end_year is None:
            end_year = start_year

        qualifying_teams = Team.get_qualifying_teams(
            start_year=start_year, end_year=end_year)

        query = cls.query.join(Team).filter(
            cls.year >= start_year, cls.year <= end_year)

        if team is not None:
            passes_defended = query.filter_by(name=team).all()
            return ([sum(passes_defended[1:], passes_defended[0])]
                    if passes_defended else [])

        passes_defended = {}
        for team_name in qualifying_teams:
            team_passes_defended = query.filter_by(name=team_name).all()

            if team_passes_defended:
                passes_defended[team_name] = sum(
                    team_passes_defended[1:], team_passes_defended[0])

        return [passes_defended[team] for team in sorted(passes_defended.keys())]

    @classmethod
    def add_passes_defended(cls, start_year: int = None,
                            end_year: int = None) -> None:
        """
        Get passes defended for all teams for the given years and add
        them to the database.

        Args:
            start_year (int): Year to start adding passes defended stats
            end_year (int): Year to stop adding passes defended stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            end_year = max([year.year for year in query])
            years = range(2010, end_year + 1)
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding passes defended stats for {year}')
            cls.add_passes_defended_for_one_year(year=year)

    @classmethod
    def add_passes_defended_for_one_year(cls, year: int) -> None:
        """
        Get passes defended for all teams for one year and add them to
        the database.

        Args:
            year (int): Year to add passes defended stats
        """
        passes_defended = []
        scraper = CFBStatsScraper(year=year)
        html_content = scraper.get_html_data(
            side_of_ball='offense', category='23')

        for item in scraper.parse_html_data(
                html_content=html_content):
            team = Team.query.filter_by(name=item[1]).first()
            passing = Passing.query.filter_by(
                team_id=team.id,
                year=year,
                side_of_ball='defense',
            ).first()

            passes_defended.append(cls(
                team_id=team.id,
                year=year,
                games=item[2],
                ints=item[3],
                passes_broken_up=item[4],
                attempts=passing.attempts,
                incompletions=passing.attempts - passing.completions
            ))

        for team_passes_defended in sorted(
                passes_defended, key=attrgetter('team_id')):
            db.session.add(team_passes_defended)

        db.session.commit()

    def __add__(self, other: 'PassesDefended') -> 'PassesDefended':
        """
        Add two PassesDefended objects to combine multiple years of data.

        Args:
            other (PassesDefended): Data about a team's passes defended

        Returns:
            Interceptions: self
        """
        self.games += other.games
        self.ints += other.ints
        self.passes_broken_up += other.passes_broken_up
        self.attempts += other.attempts
        self.incompletions += other.incompletions

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'games': self.games,
            'ints': self.ints,
            'int_pct': round(self.int_pct, 2),
            'passes_broken_up': self.passes_broken_up,
            'passes_defended': self.passes_defended,
            'passes_defended_per_game': round(self.passes_defended_per_game, 2),
            'attempts': self.attempts,
            'passes_defended_pct': round(self.passes_defended_pct, 2),
            'incompletions': self.incompletions,
            'forced_incompletion_pct': round(self.forced_incompletion_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
