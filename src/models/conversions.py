from operator import attrgetter

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team
from .total import Total


class FourthDowns(db.Model):
    __tablename__ = 'fourth_downs'
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
    def get_fourth_downs(cls, side_of_ball: str, start_year: int,
                         end_year: int = None, team: str = None
                         ) -> list['FourthDowns']:
        """
        Get fourth down offense or defense for qualifying teams for the
        given years. If team is provided, only get fourth down data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting fourth down data
            end_year (int): Year to stop getting fourth down data
            team (str): Team for which to get fourth down data

        Returns:
            list[FourthDowns]: Fourth down offense or defense for all
                teams or only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            fourth_downs = query.filter_by(name=team).all()
            return ([sum(fourth_downs[1:], fourth_downs[0])]
                    if fourth_downs else [])

        fourth_downs = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_fourth_downs = query.filter_by(name=team_name).all()

            if team_fourth_downs:
                fourth_downs[team_name] = sum(
                    team_fourth_downs[1:], team_fourth_downs[0])

        return [fourth_downs[team] for team in sorted(fourth_downs.keys())]

    @classmethod
    def add_fourth_downs(cls, start_year: int = None,
                         end_year: int = None) -> None:
        """
        Get fourth down offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding fourth down stats
            end_year (int): Year to stop adding fourth down stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding fourth down stats for {year}')
            cls.add_fourth_downs_for_one_year(year=year)

    @classmethod
    def add_fourth_downs_for_one_year(cls, year: int) -> None:
        """
        Get fourth down offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to add fourth down stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            fourth_downs = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='26')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()
                total = Total.query.filter_by(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                ).first()

                fourth_downs.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    attempts=item[3],
                    conversions=item[4],
                    plays=total.plays
                ))

            for team_fourth_downs in sorted(
                    fourth_downs, key=attrgetter('team_id')):
                db.session.add(team_fourth_downs)

        db.session.commit()

    def __add__(self, other: 'FourthDowns') -> 'FourthDowns':
        """
        Add two FourthDowns objects to combine multiple years of data.

        Args:
            other (FourthDowns): Data about a team's fourth down
                offense/defense

        Returns:
            FourthDowns: self
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


class RedZone(db.Model):
    __tablename__ = 'red_zone'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    scores = db.Column(db.Integer, nullable=False)
    tds = db.Column(db.Integer, nullable=False)
    field_goals = db.Column(db.Integer, nullable=False)

    @property
    def score_pct(self) -> float:
        if self.attempts:
            return self.scores / self.attempts * 100
        return 0.0

    @property
    def td_pct(self) -> float:
        if self.attempts:
            return self.tds / self.attempts * 100
        return 0.0

    @property
    def field_goal_pct(self) -> float:
        if self.attempts:
            return self.field_goals / self.attempts * 100
        return 0.0

    @property
    def points_per_attempt(self) -> float:
        if self.attempts:
            return (self.tds * 6 + self.field_goals * 3) / self.attempts
        return 0.0

    @classmethod
    def get_red_zone(cls, side_of_ball: str, start_year: int,
                     end_year: int = None, team: str = None) -> list['RedZone']:
        """
        Get red zone offense or defense for qualifying teams for the
        given years. If team is provided, only get red zone data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting red zone data
            end_year (int): Year to stop getting red zone data
            team (str): Team for which to get red zone data

        Returns:
            list[RedZone]: Red zone offense or defense for all teams or
                only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            red_zone = query.filter_by(name=team).all()
            return [sum(red_zone[1:], red_zone[0])] if red_zone else []

        red_zone = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_red_zone = query.filter_by(name=team_name).all()

            if team_red_zone:
                red_zone[team_name] = sum(team_red_zone[1:], team_red_zone[0])

        return [red_zone[team] for team in sorted(red_zone.keys())]

    @classmethod
    def add_red_zone(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get red zone offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding red zone stats
            end_year (int): Year to stop adding red zone stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding red zone stats for {year}')
            cls.add_red_zone_for_one_year(year=year)

    @classmethod
    def add_red_zone_for_one_year(cls, year: int) -> None:
        """
        Get red zone offense and defense stats for all teams for one
        year and add them to the database.

        Args:
            year (int): Year to add red zone stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            red_zone = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='27')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()

                red_zone.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    attempts=item[3],
                    scores=item[4],
                    tds=item[6],
                    field_goals=item[8]
                ))

            for team_red_zone in sorted(red_zone, key=attrgetter('team_id')):
                db.session.add(team_red_zone)

        db.session.commit()

    def __add__(self, other: 'RedZone') -> 'RedZone':
        """
        Add two RedZone objects to combine multiple years of data.

        Args:
            other (RedZone): Data about a team's red zone
                offense/defense

        Returns:
            RedZone: self
        """
        self.games += other.games
        self.attempts += other.attempts
        self.scores += other.scores
        self.tds += other.tds
        self.field_goals += other.field_goals

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'attempts': self.attempts,
            'scores': self.scores,
            'score_pct': round(self.score_pct, 2),
            'tds': self.tds,
            'td_pct': round(self.td_pct, 2),
            'field_goals': self.field_goals,
            'field_goal_pct': round(self.field_goal_pct, 2),
            'points_per_attempt': round(self.points_per_attempt, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data


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
    def get_third_downs(cls, side_of_ball: str, start_year: int,
                        end_year: int = None, team: str = None
                        ) -> list['ThirdDowns']:
        """
        Get third down offense or defense for qualifying teams for the
        given years. If team is provided, only get third down data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting third down data
            end_year (int): Year to stop getting third down data
            team (str): Team for which to get third down data

        Returns:
            list[ThirdDowns]: Third down offense or defense for all
                teams or only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            third_downs = query.filter_by(name=team).all()
            return [sum(third_downs[1:], third_downs[0])] if third_downs else []

        third_downs = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_third_downs = query.filter_by(name=team_name).all()

            if team_third_downs:
                third_downs[team_name] = sum(
                    team_third_downs[1:], team_third_downs[0])

        return [third_downs[team] for team in sorted(third_downs.keys())]

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

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()
                total = Total.query.filter_by(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                ).first()

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
