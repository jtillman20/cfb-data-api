from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team


class Fumbles(db.Model):
    __tablename__ = 'fumbles'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    games = db.Column(db.Integer, nullable=False)
    fumbles = db.Column(db.Integer, nullable=False)
    fumbles_lost = db.Column(db.Integer, nullable=False)
    opponent_fumbles = db.Column(db.Integer, nullable=False)
    fumbles_recovered = db.Column(db.Integer, nullable=False)
    fumbles_forced = db.Column(db.Integer, nullable=False)

    @property
    def fumbles_lost_per_game(self):
        if self.games:
            return self.fumbles_lost / self.games
        return 0.0

    @property
    def fumble_lost_pct(self) -> float:
        if self.fumbles:
            return self.fumbles_lost / self.fumbles * 100
        return 0.0

    @property
    def fumbles_recovered_per_game(self):
        if self.games:
            return self.fumbles_recovered / self.games
        return 0.0

    @property
    def fumble_recovery_pct(self) -> float:
        if self.opponent_fumbles:
            return self.fumbles_recovered / self.opponent_fumbles * 100
        return 0.0

    @property
    def all_fumbles(self) -> int:
        return self.fumbles + self.opponent_fumbles

    @property
    def all_fumble_recovery_pct(self) -> float:
        recovered = (self.fumbles - self.fumbles_lost) + self.fumbles_recovered
        return recovered / self.all_fumbles * 100

    @property
    def fumbles_forced_per_game(self) -> float:
        if self.games:
            return self.fumbles_forced / self.games
        return 0.0

    @property
    def forced_fumble_pct(self) -> float:
        if self.fumbles:
            return self.fumbles_forced / self.opponent_fumbles * 100
        return 0.0

    @classmethod
    def add_fumbles(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get fumbles and opponent fumbles for all teams for the given
        years and add them to the database.

        Args:
            start_year (int): Year to start adding fumble stats
            end_year (int): Year to stop adding fumble stats
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
            print(f'Adding fumble stats for {year}')
            cls.add_fumbles_for_one_year(year=year)

    @classmethod
    def add_fumbles_for_one_year(cls, year: int) -> None:
        """
        Get fumbles and opponent fumbles for all teams for one year and
        add them to the database.

        Args:
            year (int): Year to add fumble stats
        """
        scraper = CFBStatsScraper(year=year)
        fumbles = {
            team.name: cls(
                team_id=team.id,
                year=year,
                games=0,
                fumbles=0,
                fumbles_lost=0,
                opponent_fumbles=0,
                fumbles_recovered=0,
                fumbles_forced=0
            )
            for team in Team.get_teams(year=year)
        }

        for category in ['17', '18', '22']:
            side_of_ball = 'defense' if category == '18' else 'offense'

            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category=category)
            fumble_data = scraper.parse_html_data(html_content=html_content)

            for item in fumble_data:
                team = item[1]

                if category == '17':
                    fumbles[team].games = item[2]
                    fumbles[team].fumbles = item[3]
                    fumbles[team].fumbles_lost = item[4]

                elif category == '18':
                    fumbles[team].opponent_fumbles = item[3]
                    fumbles[team].fumbles_recovered = item[4]

                elif category == '22':
                    fumbles[team].fumbles_forced = item[3]

        for team_fumbles in fumbles.values():
            db.session.add(team_fumbles)

        db.session.commit()

    def __add__(self, other: 'Fumbles') -> 'Fumbles':
        """
        Add two Fumbles objects to combine multiple years of data.

        Args:
            other (Fumbles): Data about a team's fumbles

        Returns:
            Fumbles: self
        """
        self.games += other.games
        self.fumbles += other.fumbles
        self.fumbles_lost += other.fumbles_lost
        self.opponent_fumbles += other.opponent_fumbles
        self.fumbles_recovered += other.fumbles_recovered
        self.fumbles_forced += other.fumbles_forced

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'games': self.games,
            'fumbles': self.fumbles,
            'fumbles_lost': self.fumbles_lost,
            'fubmles_lost_per_game': round(self.fumbles_lost_per_game, 2),
            'fumble_lost_pct': round(self.fumble_lost_pct, 2),
            'opponent_fumbles': self.opponent_fumbles,
            'fumbles_recovered': self.fumbles_recovered,
            'fumbles_recovered_per_game': round(
                self.fumbles_recovered_per_game, 2),
            'fumble_recovery_pct': round(self.fumble_recovery_pct, 2),
            'all_fumbles': self.all_fumbles,
            'all_fumble_recovery_pct': round(self.all_fumble_recovery_pct, 2),
            'fumbles_forced': self.fumbles_forced,
            'fumbles_forced_per_game': round(self.fumbles_forced_per_game, 2),
            'forced_fumble_pct': round(self.forced_fumble_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
