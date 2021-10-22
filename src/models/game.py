from operator import itemgetter

from sqlalchemy import and_, or_

from app import db
from scraper import SportsReferenceScraper
from .team import Team


class Game(db.Model):
    __tablename__ = 'game'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date(), nullable=False)
    neutral_site = db.Column(db.Boolean, nullable=False)
    home_team = db.Column(db.String(100), nullable=False)
    home_score = db.Column(db.Integer, nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    away_score = db.Column(db.Integer, nullable=False)

    stats = db.relationship('GameStats', backref='game', lazy=True)

    def determine_result(self, team: str) -> str:
        """
        Determine the result of the game for the given team.

        Args:
            team (str): Team for which to determine the result

        Returns:
            str: Game result as 'win', 'loss', or 'tie'
        """
        if self.home_score == self.away_score:
            return 'tie'

        if self.home_team == team:
            return 'win' if self.home_score > self.away_score else 'loss'
        else:
            return 'win' if self.away_score > self.home_score else 'loss'

    def is_conference_game(self) -> bool:
        """
        Determine if a game was played between teams from the same
        conference for the given year, ignoring if the conference
        is Independent.

        Returns:
            bool: Whether the game was played between teams from the
                same conference
        """
        home_team = Team.query.filter_by(name=self.home_team).first()
        away_team = Team.query.filter_by(name=self.away_team).first()

        if home_team is not None and away_team is not None:
            home_conference = home_team.get_conference(year=self.year)
            away_conference = away_team.get_conference(year=self.year)
        else:
            return False

        if home_conference == 'Independent':
            return False

        return home_conference == away_conference

    @classmethod
    def get_games(cls, year: int, team: str = None) -> list['Game']:
        """
        Get FBS games for the given year. If team is provided, only
        get that team's games.

        Args:
            year (int): Year to get games
            team (str): Team for which to get games

        Returns:
            list[Game]: All games or only a team's games
        """
        query = cls.query.filter_by(year=year)

        if team is not None:
            query = query.filter(
                or_(cls.home_team == team, cls.away_team == team))

        return query.all()

    @classmethod
    def get_fcs_games(cls, year: int) -> list['Game']:
        """
        Get FBS vs. FCS games for the given year.

        Args:
            year (int): Year to get games

        Returns:
            list[Game]: All games vs. FCS teams
        """
        games = []
        all_games = cls.query.filter_by(year=year).all()

        for game in all_games:
            home_team = Team.query.filter_by(name=game.home_team).first()
            away_team = Team.query.filter_by(name=game.away_team).first()

            if home_team is not None:
                home_conference = home_team.get_conference(year=year)
            else:
                home_conference = None

            if away_team is not None:
                away_conference = away_team.get_conference(year=year)
            else:
                away_conference = None

            if home_conference is None or away_conference is None:
                games.append(game)

        return games

    @classmethod
    def add_games(cls, start_year: int, end_year: int) -> None:
        """
        Get all FBS games for the given years and add them to the
        database.

        Args:
            start_year (int): Year to begin adding games
            end_year (int): Year to stop adding games
        """
        scraper = SportsReferenceScraper()

        for year in range(start_year, end_year + 1):
            print(f'Adding games for {year}')
            html_content = scraper.get_html_data(path=f'{year}-schedule.html')
            game_data = scraper.parse_schedule_html_data(
                html_content=html_content)

            for game in game_data:
                db.session.add(cls(
                    year=year,
                    week=game[0],
                    date=game[1],
                    neutral_site=game[2],
                    home_team=game[3],
                    home_score=game[4],
                    away_team=game[5],
                    away_score=game[6]
                ))

        db.session.commit()

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'year': self.year,
            'week': self.week,
            'date': self.date,
            'neutral_site': self.neutral_site,
            'home_team': self.team,
            'home_score': self.home_score,
            'away_team': self.away_team,
            'away_score': self.away_score
        }


class GameStats(db.Model):
    __tablename__ = 'game_stats'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    home_passing_attempts = db.Column(db.Integer, nullable=False)
    home_completions = db.Column(db.Integer, nullable=False)
    home_passing_yards = db.Column(db.Integer, nullable=False)
    home_passing_tds = db.Column(db.Integer, nullable=False)
    home_rushing_attempts = db.Column(db.Integer, nullable=False)
    home_rushing_yards = db.Column(db.Integer, nullable=False)
    home_rushing_tds = db.Column(db.Integer, nullable=False)
    home_passing_first_downs = db.Column(db.Integer, nullable=False)
    home_rushing_first_downs = db.Column(db.Integer, nullable=False)
    home_penalty_first_downs = db.Column(db.Integer, nullable=False)
    home_penalties = db.Column(db.Integer, nullable=False)
    home_penalty_yards = db.Column(db.Integer, nullable=False)
    home_fumbles = db.Column(db.Integer, nullable=False)
    home_ints = db.Column(db.Integer, nullable=False)
    away_passing_attempts = db.Column(db.Integer, nullable=False)
    away_completions = db.Column(db.Integer, nullable=False)
    away_passing_yards = db.Column(db.Integer, nullable=False)
    away_passing_tds = db.Column(db.Integer, nullable=False)
    away_rushing_attempts = db.Column(db.Integer, nullable=False)
    away_rushing_yards = db.Column(db.Integer, nullable=False)
    away_rushing_tds = db.Column(db.Integer, nullable=False)
    away_passing_first_downs = db.Column(db.Integer, nullable=False)
    away_rushing_first_downs = db.Column(db.Integer, nullable=False)
    away_penalty_first_downs = db.Column(db.Integer, nullable=False)
    away_penalties = db.Column(db.Integer, nullable=False)
    away_penalty_yards = db.Column(db.Integer, nullable=False)
    away_fumbles = db.Column(db.Integer, nullable=False)
    away_ints = db.Column(db.Integer, nullable=False)

    @property
    def home_plays(self) -> int:
        return self.home_passing_attempts + self.home_rushing_attempts

    @property
    def home_total_yards(self) -> int:
        return self.home_passing_yards + self.home_rushing_yards

    @property
    def home_first_downs(self) -> int:
        return self.home_passing_first_downs + self.home_rushing_first_downs \
               + self.home_penalty_first_downs

    @property
    def home_turnovers(self) -> int:
        return self.home_fumbles + self.home_ints

    @property
    def away_plays(self) -> int:
        return self.away_passing_attempts + self.away_rushing_attempts

    @property
    def away_total_yards(self) -> int:
        return self.away_passing_yards + self.away_rushing_yards

    @property
    def away_first_downs(self) -> int:
        return self.away_passing_first_downs + self.away_rushing_first_downs \
               + self.away_penalty_first_downs

    @property
    def away_turnovers(self) -> int:
        return self.away_fumbles + self.away_ints

    @classmethod
    def add_game_stats(cls, start_year: int, end_year: int) -> None:
        """
        Get stats for all FBS games for the given years and add them
        to the database.

        Args:
            start_year (int): Year to begin adding game stats
            end_year (int): Year to stop adding game stats
        """
        game_stats = {}
        scraper = SportsReferenceScraper()

        for year in range(start_year, end_year + 1):
            print(f'Adding game stats for {year}')
            teams = Team.get_teams(year=year)

            for team in teams:
                html_content = scraper.get_game_log_html_data(
                    team=team.name, year=year)
                offense_stats = scraper.parse_game_log_data(
                    html_content=html_content, side_of_ball='offense')
                defense_stats = scraper.parse_game_log_data(
                    html_content=html_content, side_of_ball='defense')

                for offense, defense in zip(offense_stats, defense_stats):
                    opponent = offense[1]

                    query = Game.query.filter(Game.date == offense[0].date())
                    game = query.filter(or_(
                        and_(
                            Game.home_team == team.name,
                            Game.away_team == opponent
                        ),
                        and_(
                            Game.away_team == team.name,
                            Game.home_team == opponent
                        )
                    )).first()

                    if game.id in game_stats:
                        continue

                    if team.name == game.home_team:
                        home = offense
                        away = defense
                    else:
                        home = defense
                        away = offense

                    game_stats[game.id] = cls(
                        game_id=game.id,
                        home_passing_attempts=home[2],
                        home_completions=home[3],
                        home_passing_yards=home[4],
                        home_passing_tds=home[5],
                        home_rushing_attempts=home[7],
                        home_rushing_yards=home[8],
                        home_rushing_tds=home[9],
                        home_passing_first_downs=home[10],
                        home_rushing_first_downs=home[11],
                        home_penalty_first_downs=home[12],
                        home_penalties=home[13],
                        home_penalty_yards=home[14],
                        home_fumbles=home[15],
                        home_ints=home[6],
                        away_passing_attempts=away[2],
                        away_completions=away[3],
                        away_passing_yards=away[4],
                        away_passing_tds=away[5],
                        away_rushing_attempts=away[7],
                        away_rushing_yards=away[8],
                        away_rushing_tds=away[9],
                        away_passing_first_downs=away[10],
                        away_rushing_first_downs=away[11],
                        away_penalty_first_downs=away[12],
                        away_penalties=away[13],
                        away_penalty_yards=away[14],
                        away_fumbles=away[15],
                        away_ints=away[6]
                    )

        for game_id, game in sorted(game_stats.items(), key=itemgetter(0)):
            db.session.add(game)

        db.session.commit()
