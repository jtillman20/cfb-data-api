from operator import attrgetter

from numpy import sum

from app import db
from scraper import CFBStatsScraper
from .first_downs import FirstDowns
from .game import Game
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
    first_downs = db.Column(db.Integer, nullable=False)
    opponents_games = db.Column(db.Integer, nullable=False)
    opponents_attempts = db.Column(db.Integer, nullable=False)
    opponents_completions = db.Column(db.Integer, nullable=False)
    opponents_yards = db.Column(db.Integer, nullable=False)
    opponents_tds = db.Column(db.Integer, nullable=False)
    opponents_ints = db.Column(db.Integer, nullable=False)

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

    @property
    def first_down_pct(self) -> float:
        if self.attempts:
            return self.first_downs / self.attempts * 100
        return 0.0

    @property
    def opponents_yards_per_attempt(self) -> float:
        if self.opponents_attempts:
            return self.opponents_yards / self.opponents_attempts
        return 0.0

    @property
    def opponents_yards_per_game(self) -> float:
        if self.opponents_games:
            return self.opponents_yards / self.opponents_games
        return 0.0

    @property
    def opponents_rating(self) -> float:
        if self.opponents_attempts:
            return (self.opponents_yards * 8.4 + self.opponents_completions
                    * 100 + self.opponents_tds * 330 - self.opponents_ints
                    * 200) / self.opponents_attempts
        return 0.0

    @property
    def relative_yards_per_attempt(self) -> float:
        if self.opponents_yards_per_attempt:
            return ((self.yards_per_attempt / self.opponents_yards_per_attempt)
                    * 100)

    @property
    def relative_yards_per_game(self) -> float:
        if self.opponents_yards_per_game:
            return (self.yards_per_game / self.opponents_yards_per_game) * 100
        return 0.0

    @property
    def relative_rating(self) -> float:
        if self.opponents_rating:
            return (self.rating / self.opponents_rating) * 100
        return 0.0

    @classmethod
    def get_passing(cls, side_of_ball: str, start_year: int,
                    end_year: int = None, team: str = None) -> list['Passing']:
        """
        Get passing offense or defense for qualifying teams for the
        given years. If team is provided, only get passing data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting passing data
            end_year (int): Year to stop getting passing data
            team (str): Team for which to get passing data

        Returns:
            list[Passing]: Passing offense or defense for all teams or
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
            passing = query.filter_by(name=team).all()
            return [sum(passing)] if passing else []

        passing = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_passing = query.filter_by(name=team_name).all()

            if team_passing:
                passing[team_name] = sum(team_passing)

        return [passing[team] for team in sorted(passing.keys())]

    @classmethod
    def add_passing(cls, start_year: int, end_year: int = None) -> None:
        """
        Get passing offense and defense stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding passing stats
            end_year (int): Year to stop adding passing stats
        """
        if end_year is None:
            end_year = start_year
        years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding passing stats for {year}')
            cls.add_passing_for_one_year(year=year)
            cls.add_opponent_passing(year=year)

    @classmethod
    def add_passing_for_one_year(cls, year: int) -> None:
        """
        Get passing offense and defense stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to get passing stats
        """
        for team in Team.get_teams(year=year):
            games = Game.get_games(year=year, team=team.name)
            game_stats = [game.stats for game in games]

            for side_of_ball in ['offense', 'defense']:
                attempts, completions, yards, tds, ints = 0, 0, 0, 0, 0

                for stats in game_stats:
                    home_team = stats.game.home_team

                    if side_of_ball == 'offense':
                        side = 'home' if home_team == team.name else 'away'
                    else:
                        side = 'away' if home_team == team.name else 'home'

                    attempts += getattr(stats, f'{side}_passing_attempts')
                    completions += getattr(stats, f'{side}_completions')
                    yards += getattr(stats, f'{side}_passing_yards')
                    tds += getattr(stats, f'{side}_passing_tds')
                    ints += getattr(stats, f'{side}_ints')

                first_downs = FirstDowns.query.filter_by(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                ).first()

                db.session.add(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=len(games),
                    attempts=attempts,
                    completions=completions,
                    yards=yards,
                    tds=tds,
                    ints=ints,
                    first_downs=first_downs.passing,
                    opponents_games=0,
                    opponents_attempts=0,
                    opponents_completions=0,
                    opponents_yards=0,
                    opponents_tds=0,
                    opponents_ints=0
                ))

        db.session.commit()

    @classmethod
    def add_opponent_passing(cls, year: int) -> None:
        """
        Get passing offense and defense for all team's opponents
        and add them to the database.

        Args:
            year (int): Year to add passing stats
        """
        for team_passing in cls.query.filter_by(year=year).all():
            team = team_passing.team.name

            for game in Game.get_games(year=year, team=team):
                game_stats = game.stats

                if team == game.away_team:
                    opponent_name = game.home_team
                    attempts = game_stats.away_passing_attempts
                    completions = game_stats.away_completions
                    yards = game_stats.away_passing_yards
                    tds = game_stats.away_passing_tds
                    ints = game_stats.away_ints
                else:
                    opponent_name = game.away_team
                    attempts = game_stats.home_passing_attempts
                    completions = game_stats.home_completions
                    yards = game_stats.home_passing_yards
                    tds = game_stats.home_passing_tds
                    ints = game_stats.home_ints

                opponent_query = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name)

                if opponent_query.first() is not None:
                    opponent = Team.query.filter_by(name=opponent_name).first()
                    side_of_ball = team_passing.side_of_ball
                    opposite_side_of_ball = ('defense'if side_of_ball == 'offense'
                                             else 'offense')

                    opponent_stats = cls.query.filter_by(
                        team_id=opponent.id,
                        year=year,
                        side_of_ball=opposite_side_of_ball,
                    ).first()

                    opponent_games = opponent_stats.games
                    team_passing.opponents_games += opponent_games - 1

                    opponent_attempts = opponent_stats.attempts - attempts
                    team_passing.opponents_attempts += opponent_attempts

                    opponent_completions = opponent_stats.completions - completions
                    team_passing.opponents_completions += opponent_completions

                    opponent_yards = opponent_stats.yards - yards
                    team_passing.opponents_yards += opponent_yards

                    opponent_tds = opponent_stats.tds - tds
                    team_passing.opponents_tds += opponent_tds

                    opponent_ints = opponent_stats.ints - ints
                    team_passing.opponents_ints += opponent_ints

        db.session.commit()

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
        self.first_downs += other.first_downs
        self.opponents_games += other.opponents_games
        self.opponents_attempts += other.opponents_attempts
        self.opponents_completions += other.opponents_completions
        self.opponents_yards += other.opponents_yards
        self.opponents_tds += other.opponents_tds
        self.opponents_ints += other.opponents_ints

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
            'rating': round(self.rating, 2),
            'first_down_pct': round(self.first_down_pct, 1),
            'relative_yards_per_attempt': round(
                self.relative_yards_per_attempt, 1),
            'relative_yards_per_game': round(self.relative_yards_per_game, 1),
            'relative_rating': round(self.relative_rating, 1)
        }


class PassingPlays(db.Model):
    __tablename__ = 'passing_plays'
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
    def get_passing_plays(cls, side_of_ball: str, start_year: int,
                          end_year: int = None, team: str = None
                          ) -> list['PassingPlays']:
        """
        Get passing plays or opponent passing plays for qualifying
        teams for the given years. If team is provided, only get
        scrimmage plays data for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting passing play data
            end_year (int): Year to stop getting passing play data
            team (str): Team for which to get passing play data

        Returns:
            list[PassingPlays]: Passing plays or opponent passing plays
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
            passing_plays = query.filter_by(name=team).all()
            return [sum(passing_plays)] if passing_plays else []

        passing_plays = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_passing_plays = query.filter_by(name=team_name).all()

            if team_passing_plays:
                passing_plays[team_name] = sum(team_passing_plays)

        return [passing_plays[team] for team in sorted(passing_plays.keys())]

    @classmethod
    def add_passing_plays(cls, start_year: int, end_year: int = None) -> None:
        """
        Get passing plays and opponent passing plays for all teams
        for the given years and add them to the database.

        Args:
            start_year (int): Year to start adding passing play stats
            end_year (int): Year to stop adding passing play stats
        """
        if end_year is None:
            end_year = start_year
        years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding passing play stats for {year}')
            cls.add_passing_plays_for_one_year(year=year)

    @classmethod
    def add_passing_plays_for_one_year(cls, year: int) -> None:
        """
        Get passing plays and opponent passing plays for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to add passing play stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            passing_plays = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='32')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()
                passing = Passing.query.filter_by(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                ).first()

                passing_plays.append(cls(
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
                    plays=passing.attempts
                ))

            for team_passing_plays in sorted(
                    passing_plays, key=attrgetter('team_id')):
                db.session.add(team_passing_plays)

        db.session.commit()

    def __add__(self, other: 'PassingPlays') -> 'PassingPlays':
        """
        Add two PassingPlays objects to combine multiple years of data.

        Args:
            other (PassingPlays): Data about a team's passing plays
                or opponent passing plays

        Returns:
            PassingPlays: self
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
        return {
            'id': self.id,
            'rank': self.rank,
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
