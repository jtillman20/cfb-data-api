from operator import attrgetter
from typing import Union

from app import db
from scraper import CFBStatsScraper
from .first_downs import FirstDowns
from .game import Game
from .team import Team


class Rushing(db.Model):
    __tablename__ = 'rushing'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    tds = db.Column(db.Integer, nullable=False)
    first_downs = db.Column(db.Integer, nullable=False)
    opponents_games = db.Column(db.Integer, nullable=False)
    opponents_attempts = db.Column(db.Integer, nullable=False)
    opponents_yards = db.Column(db.Integer, nullable=False)

    @property
    def attempts_per_game(self) -> float:
        if self.games:
            return self.attempts / self.games
        return 0.0

    @property
    def yards_per_attempt(self) -> float:
        if self.attempts:
            return self.yards / self.attempts
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def td_pct(self) -> float:
        if self.attempts:
            return self.tds / self.attempts * 100
        return 0.0

    @property
    def first_down_pct(self) -> float:
        if self.attempts:
            return self.first_downs / self.attempts * 100
        return 0.0

    @property
    def opponents_yards_per_game(self) -> float:
        if self.opponents_games:
            return self.opponents_yards / self.opponents_games
        return 0.0

    @property
    def opponents_yards_per_attempt(self) -> float:
        if self.opponents_attempts:
            return self.opponents_yards / self.opponents_attempts
        return 0.0

    @property
    def relative_yards_per_game(self) -> float:
        if self.opponents_yards_per_game:
            return (self.yards_per_game / self.opponents_yards_per_game) * 100
        return 0.0

    @property
    def relative_yards_per_attempt(self) -> float:
        if self.opponents_yards_per_attempt:
            return ((self.yards_per_attempt / self.opponents_yards_per_attempt)
                    * 100)
        return 0.0

    @classmethod
    def get_rushing(cls, side_of_ball: str, start_year: int,
                    end_year: int = None, team: str = None
                    ) -> Union['Rushing', list['Rushing']]:
        """
        Get rushing offense or defense for qualifying teams for the
        given years. If team is provided, only get rushing data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting rushing data
            end_year (int): Year to stop getting rushing data
            team (str): Team for which to get rushing data

        Returns:
            Union[Rushing, list[Rushing]]: rushing offense or defense
                for all teams or only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            rushing = query.filter_by(name=team).all()
            return sum(rushing[1:], rushing[0]) if rushing else []

        rushing = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_rushing = query.filter_by(name=team_name).all()

            if team_rushing:
                rushing[team_name] = sum(team_rushing[1:], team_rushing[0])

        return [rushing[team] for team in sorted(rushing.keys())]

    @classmethod
    def add_rushing(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get rushing offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding rushing stats
            end_year (int): Year to stop adding rushing stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding rushing stats for {year}')
            cls.add_rushing_for_one_year(year=year)
            cls.add_opponent_rushing(year=year)

    @classmethod
    def add_rushing_for_one_year(cls, year: int) -> None:
        """
        Get rushing offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to get rushing stats
        """
        for team in Team.get_teams(year=year):
            games = Game.get_games(year=year, team=team.name)
            game_stats = [game.stats[0] for game in games]

            for side_of_ball in ['offense', 'defense']:
                attempts, yards, tds = 0, 0, 0

                for stats in game_stats:
                    home_team = stats.game.home_team

                    if side_of_ball == 'offense':
                        side = 'home' if home_team == team.name else 'away'
                    else:
                        side = 'away' if home_team == team.name else 'home'

                    attempts += getattr(stats, f'{side}_rushing_attempts')
                    yards += getattr(stats, f'{side}_rushing_yards')
                    tds += getattr(stats, f'{side}_rushing_tds')

                first_downs = FirstDowns.get_first_downs(
                    side_of_ball=side_of_ball, start_year=year, team=team.name)

                db.session.add(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=len(games),
                    attempts=attempts,
                    yards=yards,
                    tds=tds,
                    first_downs=first_downs.rushing,
                    opponents_games=0,
                    opponents_attempts=0,
                    opponents_yards=0
                ))

        db.session.commit()

    @classmethod
    def add_opponent_rushing(cls, year: int) -> None:
        """
        Get rushing offense and defense for all team's opponents
        and add them to the database.

        Args:
            year (int): Year to add rushing stats
        """
        for team_rushing in cls.query.filter_by(year=year).all():
            team = team_rushing.team.name

            for game in Game.get_games(year=year, team=team):
                game_stats = game.stats[0]

                if team == game.away_team:
                    opponent_name = game.home_team
                    attempts = game_stats.away_rushing_attempts
                    yards = game_stats.away_rushing_yards
                else:
                    opponent_name = game.away_team
                    attempts = game_stats.home_rushing_attempts
                    yards = game_stats.home_rushing_yards

                opponent_query = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name)

                if opponent_query.first() is not None:
                    side_of_ball = team_rushing.side_of_ball
                    opposite_side_of_ball = ('defense' if side_of_ball == 'offense'
                                             else 'offense')

                    opponent_stats = cls.get_rushing(
                        side_of_ball=opposite_side_of_ball,
                        start_year=year,
                        team=opponent_name
                    )

                    opponent_games = opponent_stats.games
                    team_rushing.opponents_games += opponent_games - 1

                    opponent_attempts = opponent_stats.attempts - attempts
                    team_rushing.opponents_attempts += opponent_attempts

                    opponent_yards = opponent_stats.yards - yards
                    team_rushing.opponents_yards += opponent_yards

        db.session.commit()

    def __add__(self, other: 'Rushing') -> 'Rushing':
        """
        Add two Rushing objects to combine multiple years of data.

        Args:
            other (Rushing): Data about a team's rushing offense/defense

        Returns:
            Rushing: self
        """
        self.games += other.games
        self.attempts += other.attempts
        self.yards += other.yards
        self.tds += other.tds
        self.first_downs += other.first_downs
        self.opponents_games += other.opponents_games
        self.opponents_attempts += other.opponents_attempts
        self.opponents_yards += other.opponents_yards

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'attempts': self.attempts,
            'attempts_per_game': round(self.attempts_per_game, 2),
            'yards': self.yards,
            'yards_per_attempt': round(self.yards_per_attempt, 2),
            'yards_per_game': round(self.yards_per_game, 1),
            'tds': self.tds,
            'td_pct': round(self.td_pct, 2),
            'first_down_pct': round(self.first_down_pct, 1),
            'relative_yards_per_attempt': round(
                self.relative_yards_per_attempt, 1),
            'relative_yards_per_game': round(self.relative_yards_per_game, 1)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data


class RushingPlays(db.Model):
    __tablename__ = 'rushing_plays'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    ten = db.Column(db.Integer, nullable=False)
    twenty = db.Column(db.Integer, nullable=False)
    thirty = db.Column(db.Integer, nullable=False)
    forty = db.Column(db.Integer, nullable=False)
    fifty = db.Column(db.Integer, nullable=False)
    sixty = db.Column(db.Integer, nullable=False)
    seventy = db.Column(db.Integer, nullable=False)
    eighty = db.Column(db.Integer, nullable=False)
    ninety = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def ten_pct(self) -> float:
        if self.plays:
            return self.ten / self.plays * 100
        return 0.0

    @property
    def twenty_pct(self) -> float:
        if self.plays:
            return self.twenty / self.plays * 100
        return 0.0

    @property
    def thirty_pct(self) -> float:
        if self.plays:
            return self.thirty / self.plays * 100
        return 0.0

    @property
    def forty_pct(self) -> float:
        if self.plays:
            return self.forty / self.plays * 100
        return 0.0

    @property
    def fifty_pct(self) -> float:
        if self.plays:
            return self.fifty / self.plays * 100
        return 0.0

    @property
    def sixty_pct(self) -> float:
        if self.plays:
            return self.sixty / self.plays * 100
        return 0.0

    @property
    def seventy_pct(self) -> float:
        if self.plays:
            return self.sixty / self.plays * 100
        return 0.0

    @property
    def eighty_pct(self) -> float:
        if self.plays:
            return self.eighty / self.plays * 100
        return 0.0

    @property
    def ninety_pct(self) -> float:
        if self.plays:
            return self.ninety / self.plays * 100
        return 0.0

    @classmethod
    def get_rushing_plays(cls, side_of_ball: str, start_year: int,
                          end_year: int = None, team: str = None
                          ) -> Union['RushingPlays', list['RushingPlays']]:
        """
        Get rushing plays or opponent rushing plays for qualifying
        teams for the given years. If team is provided, only get
        scrimmage plays data for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting rushing play data
            end_year (int): Year to stop getting rushing play data
            team (str): Team for which to get rushing play data

        Returns:
            Union[RushingPlays, list[RushingPlays]]: Rassing plays
                or opponent rushing plays for all teams or only for
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
            rushing_plays = query.filter_by(name=team).all()
            return (sum(rushing_plays[1:], rushing_plays[0])
                    if rushing_plays else [])

        rushing_plays = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_rushing_plays = query.filter_by(name=team_name).all()

            if team_rushing_plays:
                rushing_plays[team_name] = sum(
                    team_rushing_plays[1:], team_rushing_plays[0])

        return [rushing_plays[team] for team in sorted(rushing_plays.keys())]

    @classmethod
    def add_rushing_plays(cls, start_year: int = None,
                          end_year: int = None) -> None:
        """
        Get rushing plays and opponent rushing plays for all teams
        for the given years and add them to the database.

        Args:
            start_year (int): Year to start adding rushing play stats
            end_year (int): Year to stop adding rushing play stats
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
            print(f'Adding rushing play stats for {year}')
            cls.add_rushing_plays_for_one_year(year=year)

    @classmethod
    def add_rushing_plays_for_one_year(cls, year: int) -> None:
        """
        Get rushing plays and opponent rushing plays for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to add rushing play stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            rushing_plays = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='31')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()
                rushing = Rushing.get_rushing(
                    side_of_ball=side_of_ball, start_year=year, team=team.name)

                rushing_plays.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    ten=item[3],
                    twenty=item[4],
                    thirty=item[5],
                    forty=item[6],
                    fifty=item[7],
                    sixty=item[8],
                    seventy=item[9],
                    eighty=item[10],
                    ninety=item[11],
                    plays=rushing.attempts
                ))

            for team_rushing_plays in sorted(
                    rushing_plays, key=attrgetter('team_id')):
                db.session.add(team_rushing_plays)

        db.session.commit()

    def __add__(self, other: 'RushingPlays') -> 'RushingPlays':
        """
        Add two RushingPlays objects to combine multiple years of data.

        Args:
            other (RushingPlays): Data about a team's rushing plays
                or opponent rushing plays

        Returns:
            RushingPlays: self
        """
        self.games += other.games
        self.ten += other.ten
        self.twenty += other.twenty
        self.thirty += other.thirty
        self.forty += other.forty
        self.fifty += other.fifty
        self.sixty += other.sixty
        self.seventy += other.seventy
        self.eighty += other.eighty
        self.ninety += other.ninety
        self.plays += other.plays

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'ten': self.ten,
            'ten_pct': round(self.ten_pct, 2),
            'twenty': self.twenty,
            'twenty_pct': round(self.twenty_pct, 2),
            'thirty': self.thirty,
            'thirty_pct': round(self.thirty_pct, 2),
            'forty': self.forty,
            'forty_pct': round(self.forty_pct, 2),
            'fifty': self.fifty,
            'fifty_pct': round(self.fifty_pct, 2),
            'sixty': self.sixty,
            'sixty_pct': round(self.sixty_pct, 2),
            'seventy': self.seventy,
            'seventy_pct': round(self.seventy_pct, 2),
            'eighty': self.eighty,
            'eighty_pct': round(self.eighty_pct, 2),
            'ninety': self.ninety,
            'ninety_pct': round(self.ninety_pct, 2),
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
