from operator import attrgetter

from numpy import sum

from app import db
from scraper import CFBStatsScraper
from .team import Team


class FieldGoals(db.Model):
    __tablename__ = 'field_goals'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    field_goals = db.Column(db.Integer, nullable=False)

    @property
    def attempts_per_game(self) -> float:
        if self.games:
            return self.attempts / self.games
        return 0.0

    @property
    def field_goals_per_game(self) -> float:
        if self.games:
            return self.field_goals / self.games
        return 0.0

    @property
    def pct(self) -> float:
        if self.attempts:
            return self.field_goals / self.attempts * 100
        return 0.0

    @classmethod
    def get_field_goals(cls, side_of_ball: str, start_year: int,
                        end_year: int = None, team: str = None
                        ) -> list['FieldGoals']:
        """
        Get field goals or opponent field goals for qualifying teams
        for the given years. If team is provided, only get field goal
        data for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting field goal data
            end_year (int): Year to stop getting field goal data
            team (str): Team for which to get field goal data

        Returns:
            list[FieldGoals]: Field goals or opponent field goals for
                all teams or only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            field_goals = query.filter_by(name=team).all()
            return [sum(field_goals)] if field_goals else []

        field_goals = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_field_goals = query.filter_by(name=team_name).all()

            if team_field_goals:
                field_goals[team_name] = sum(team_field_goals)

        return [field_goals[team] for team in sorted(field_goals.keys())]

    @classmethod
    def add_field_goals(cls, start_year: int, end_year: int = None) -> None:
        """
        Get field goal and opponent field goal stats for all teams for
        the given years and add them to the database.

        Args:
            start_year (int): Year to start adding field goal stats
            end_year (int): Year to stop adding field goal stats
        """
        if end_year is None:
            end_year = start_year
        years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding field goal stats for {year}')
            cls.add_field_goals_for_one_year(year=year)

    @classmethod
    def add_field_goals_for_one_year(cls, year: int) -> None:
        """
        Get field goal and opponent field goal stats for all teams for
        one year and add them to the database.

        Args:
            year (int): Year to add field goal stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            field_goals = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='07')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()

                field_goals.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    attempts=item[3],
                    field_goals=item[4]
                ))

            for team_field_goals in sorted(
                    field_goals, key=attrgetter('team_id')):
                db.session.add(team_field_goals)

        db.session.commit()

    def __add__(self, other: 'FieldGoals') -> 'FieldGoals':
        """
        Add two FieldGoals objects to combine multiple years of data.

        Args:
            other (FieldGoals): Data about a team's field goals or
                opponent field goals

        Returns:
            FieldGoals: self
        """
        self.games += other.games
        self.attempts += other.attempts
        self.field_goals += other.field_goals

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'attempts': self.attempts,
            'attempts_per_game': round(self.attempts_per_game, 2),
            'field_goals': self.field_goals,
            'field_goals_per_game': round(self.field_goals_per_game, 2),
            'pct': round(self.pct, 2),
        }


class PATs(db.Model):
    __tablename__ = 'pats'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    pats = db.Column(db.Integer, nullable=False)

    @property
    def attempts_per_game(self) -> float:
        if self.games:
            return self.attempts / self.games
        return 0.0

    @property
    def pats_per_game(self) -> float:
        if self.games:
            return self.pats / self.games
        return 0.0

    @property
    def pct(self) -> float:
        if self.attempts:
            return self.pats / self.attempts * 100
        return 0.0

    @classmethod
    def get_pats(cls, side_of_ball: str, start_year: int, end_year: int = None,
                 team: str = None) -> list['PATs']:
        """
        Get PATs or opponent PATs for qualifying teams for the given
        years. If team is provided, only get PAT data for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting PAT data
            end_year (int): Year to stop getting PAT data
            team (str): Team for which to get PAT data

        Returns:
            list[PATs]: PATs or opponent PATs for all teams or only for
                one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            pats = query.filter_by(name=team).all()
            return [sum(pats)] if pats else []

        pats = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_pats = query.filter_by(name=team_name).all()

            if team_pats:
                pats[team_name] = sum(team_pats)

        return [pats[team] for team in sorted(pats.keys())]

    @classmethod
    def add_pats(cls, start_year: int, end_year: int = None) -> None:
        """
        Get PAT and opponent PAT stats for all teams for the given
        years and add them to the database.

        Args:
            start_year (int): Year to start adding PAT stats
            end_year (int): Year to stop adding PAT stats
        """
        if end_year is None:
            end_year = start_year
        years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding PAT stats for {year}')
            cls.add_pats_for_one_year(year=year)

    @classmethod
    def add_pats_for_one_year(cls, year: int) -> None:
        """
        Get PAT and opponent PAT stats for all teams for one year and
        add them to the database.

        Args:
            year (int): Year to add PAT stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            pats = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='08')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()

                pats.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    attempts=item[3],
                    pats=item[4]
                ))

            for team_pats in sorted(pats, key=attrgetter('team_id')):
                db.session.add(team_pats)

        db.session.commit()

    def __add__(self, other: 'PATs') -> 'PATs':
        """
        Add two PATs objects to combine multiple years of data.

        Args:
            other (PATs): Data about a team's PATs or opponent PATs

        Returns:
            PATs: self
        """
        self.games += other.games
        self.attempts += other.attempts
        self.pats += other.pats

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'attempts': self.attempts,
            'attempts_per_game': round(self.attempts_per_game, 2),
            'pats': self.pats,
            'pats_per_game': round(self.pats_per_game, 2),
            'pct': round(self.pct, 2),
        }
