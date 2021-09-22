from typing import Union

from app import db
from .game import Game
from .team import Team


class Record(db.Model):
    __tablename__ = 'record'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    ties = db.Column(db.Integer, nullable=False)
    conference_wins = db.Column(db.Integer, nullable=False)
    conference_losses = db.Column(db.Integer, nullable=False)
    conference_ties = db.Column(db.Integer, nullable=False)

    @property
    def games(self):
        return self.wins + self.losses + self.ties

    @property
    def win_pct(self):
        if self.games:
            return round((self.wins + self.ties * 0.5) / self.games, 4)
        return 0.0

    @property
    def conference_games(self):
        return self.conference_wins + self.conference_losses \
               + self.conference_ties

    @property
    def conference_win_pct(self):
        if self.conference_games:
            return round((self.conference_wins + self.conference_ties * 0.5)
                         / self.conference_games, 4)
        return 0.0

    def __add__(self, other: 'Record') -> 'Record':
        """
        Add two Record objects to combine multiple years of data.

        Args:
            other (Record): Data about a team's win-loss record

        Returns:
            Record: self
        """
        self.year = other.year
        self.wins += other.wins
        self.losses += other.losses
        self.ties += other.ties
        self.conference_wins += other.conference_wins
        self.conference_losses += other.conference_losses
        self.conference_ties += other.conference_ties

        return self

    @classmethod
    def get_records(cls, start_year: int, end_year: int = None,
                    team: str = None) -> Union['Record', list['Record']]:
        """
        Get win-loss records for qualifying teams for the given years.
        If team is provided, only get records for that team.

        Args:
            start_year (int): Year to start getting win-loss records
            end_year (int): Year to stop getting win-loss records
            team (str): Team for which to get win-loss record

        Returns:
            Union[Record, list[Record]]: Win-loss records for qualifying
                teams or only the win-loss records for one team
        """
        if end_year is None:
            end_year = start_year

        qualifying_teams = Team.get_qualifying_teams(
            start_year=start_year, end_year=end_year)

        query = cls.query.join(Team).filter(
            cls.year >= start_year, cls.year <= end_year)

        if team is not None:
            records = query.filter(team == Team.name).all()
            return sum(records[1:], records[0])

        records = {}
        for team_name in qualifying_teams:
            team_record = query.filter(team_name == Team.name).all()

            if team_record:
                records[team_name] = sum(team_record[1:], team_record[0])

        return [records[team] for team in sorted(records.keys())]

    @classmethod
    def add_records(cls) -> None:
        """
        Get win-loss records for all teams for every year and add them
        to the database.
        """
        query = Game.query.with_entities(Game.year).distinct()
        years = [year.year for year in query]

        for year in years:
            print(f'Adding records for {year}')
            cls.add_records_for_one_year(year=year)

    @classmethod
    def add_records_for_one_year(cls, year: int) -> None:
        """
        Get win-loss records for all teams for one year and add them
        to the database.

        Args:
            year (int): Year to add records
        """
        teams = Team.get_teams(year=year)

        for team in teams:
            record = cls(
                team_id=team.id,
                year=year,
                wins=0,
                losses=0,
                ties=0,
                conference_wins=0,
                conference_losses=0,
                conference_ties=0
            )

            for game in Game.get_games(year=year, team=team.name):
                result = game.determine_result(team=team.name)

                if result == 'win':
                    record.wins += 1

                    if game.is_conference_game():
                        record.conference_wins += 1

                elif result == 'loss':
                    record.losses += 1

                    if game.is_conference_game():
                        record.conference_losses += 1

                elif result == 'tie':
                    record.ties += 1

                    if game.is_conference_game():
                        record.conference_ties += 1

            db.session.add(record)

        db.session.commit()

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'games': self.games,
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties,
            'win_pct': self.win_pct,
            'conference_games': self.conference_games,
            'conference_wins': self.conference_wins,
            'conference_losses': self.conference_losses,
            'conference_ties': self.conference_ties,
            'conference_win_pct': self.conference_win_pct
        }
