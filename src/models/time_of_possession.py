from operator import attrgetter
from typing import Union

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team
from .total import Total


class TimeOfPossession(db.Model):
    __tablename__ = 'time_of_possession'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    games = db.Column(db.Integer, nullable=False)
    time_of_possession = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def time_of_possession_per_game(self) -> float:
        if self.games:
            return self.time_of_possession / self.games
        return 0.0

    @property
    def seconds_per_play(self) -> float:
        if self.plays:
            return self.time_of_possession / self.plays
        return 0.0

    @classmethod
    def add_time_of_possession(cls, start_year: int = None,
                               end_year: int = None) -> None:
        """
        Get time of possession for all teams for the given years and add
        them to the database.

        Args:
            start_year (int): Year to start adding time of possession
                stats
            end_year (int): Year to stop adding time of possession
                stats
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
            print(f'Adding time of possession stats for {year}')
            cls.add_time_of_possession_for_one_year(year=year)

    @classmethod
    def add_time_of_possession_for_one_year(cls, year: int) -> None:
        """
        Get time of possession for all teams for one year and add them
        to the database.

        Args:
            year (int): Year to add time of possession stats
        """
        scraper = CFBStatsScraper(year=year)
        time_of_possession = []

        html_content = scraper.get_html_data(
            side_of_ball='offense', category='15')
        time_of_possession_data = scraper.parse_html_data(
            html_content=html_content)

        for item in time_of_possession_data:
            team = Team.query.filter_by(name=item[1]).first()
            total = Total.get_total(
                side_of_ball='offense',
                start_year=year,
                team=team.name
            )

            time = item[3].split(':')

            time_of_possession.append(cls(
                team_id=team.id,
                year=year,
                games=item[2],
                time_of_possession=int(time[0]) * 60 + int(time[1]),
                plays=total.plays
            ))

        for team_time_of_possession in sorted(
                time_of_possession, key=attrgetter('team_id')):
            db.session.add(team_time_of_possession)

        db.session.commit()

    @classmethod
    def format_time(cls, time: Union[int, float]) -> str:
        """
        Format a time in seconds into a string format of m:s.

        Args:
            time: Time to format in seconds

        Returns:
            str: Formatted time string
        """
        minutes, seconds = divmod(time, 60)

        if isinstance(time, int):
            seconds = f'{seconds:02}'
        else:
            minutes = int(minutes)
            seconds = f'{round(seconds, 2):05.2f}'

        return f'{minutes:02}:{seconds}'

    def __add__(self, other: 'TimeOfPossession') -> 'TimeOfPossession':
        """
        Add two TimeOfPossession objects to combine multiple years of
        data.

        Args:
            other (TimeOfPossession): Data about a team's time of
                possession

        Returns:
            TimeOfPossession: self
        """
        self.games += other.games
        self.time_of_possession += other.time_of_possession
        self.plays += other.plays

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'games': self.games,
            'time_of_possession': self.format_time(self.time_of_possession),
            'time_of_possession_per_game': self.format_time(
                self.time_of_possession_per_game),
            'plays': self.plays,
            'seconds_per_play': round(self.seconds_per_play, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
