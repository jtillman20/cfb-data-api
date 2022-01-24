from app import db
from .game import Game
from .team import Team


class Penalties(db.Model):
    __tablename__ = 'penalties'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    penalties = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)

    @property
    def penalties_per_game(self) -> float:
        if self.games:
            return self.penalties / self.games
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def yards_per_penalty(self) -> float:
        if self.penalties:
            return self.yards / self.penalties
        return 0.0

    @classmethod
    def add_penalties(cls, start_year: int = None,
                      end_year: int = None) -> None:
        """
        Get penalties and opponent penalties for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding penalty stats
            end_year (int): Year to stop adding penalty stats
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
            print(f'Adding penalty stats for {year}')
            cls.add_penalties_for_one_year(year=year)

    @classmethod
    def add_penalties_for_one_year(cls, year: int) -> None:
        """
        Get penalties and opponent penalties for all teams for one year
        and add them to the database.

        Args:
            year (int): Year to get penalty stats
        """
        teams = Team.get_teams(year=year)

        for team in teams:
            games = Game.get_games(year=year, team=team.name)
            game_stats = [game.stats[0] for game in games]

            for side_of_ball in ['offense', 'defense']:
                penalties = 0
                yards = 0

                for stats in game_stats:
                    home_team = stats.game.home_team

                    if side_of_ball == 'offense':
                        side = 'home' if home_team == team.name else 'away'
                    else:
                        side = 'away' if home_team == team.name else 'home'

                    penalties += getattr(stats, f'{side}_penalties')
                    yards += getattr(stats, f'{side}_penalty_yards')

                db.session.add(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=len(games),
                    penalties=penalties,
                    yards=yards,
                ))

        db.session.commit()

    def __add__(self, other: 'Penalties') -> 'Penalties':
        """
        Add two Penalties objects to combine multiple years of data.

        Args:
            other (Penalties): Data about a team's penalties or
                opponent's penalties

        Returns:
            Penalties: self
        """
        self.games += other.games
        self.penalties += other.penalties
        self.yards += other.yards

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'penalties': self.penalties,
            'penalties_per_game': round(self.penalties_per_game, 1),
            'yards': self.yards,
            'yards_per_game': round(self.yards_per_game, 1),
            'yards_per_penalty': round(self.yards_per_penalty, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
