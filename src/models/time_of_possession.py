from typing import Union

from app import db


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
