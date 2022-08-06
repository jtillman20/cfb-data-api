from app import db
from .conference import Conference
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
            return (self.wins + self.ties * 0.5) / self.games
        return 0.0

    @property
    def conference_games(self):
        return (self.conference_wins + self.conference_losses +
                self.conference_ties)

    @property
    def conference_win_pct(self):
        if self.conference_games:
            return ((self.conference_wins + self.conference_ties * 0.5) /
                    self.conference_games)
        return 0.0

    @classmethod
    def get_records(cls, start_year: int, end_year: int = None,
                    team: str = None) -> list['Record']:
        """
        Get win-loss records for qualifying teams for the given years.
        If team is provided, only get records for that team.

        Args:
            start_year (int): Year to start getting win-loss records
            end_year (int): Year to stop getting win-loss records
            team (str): Team for which to get win-loss record

        Returns:
            list[Record]: Win-loss records for qualifying teams or only
                the win-loss records for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.year >= start_year, cls.year <= end_year)

        if team is not None:
            records = query.filter_by(name=team).all()
            return [sum(records[1:], records[0])] if records else []

        records = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_record = query.filter_by(name=team_name).all()

            if team_record:
                records[team_name] = sum(team_record[1:], team_record[0])

        return [records[team] for team in sorted(records.keys())]

    @classmethod
    def add_records(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get win-loss records for all teams for every year and add them
        to the database.

        Args:
            start_year (int): Year to start adding win-loss records
            end_year (int): Year to stop adding win-loss records
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

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
        for team in Team.get_teams(year=year):
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

    def __add__(self, other: 'Record') -> 'Record':
        """
        Add two Record objects to combine multiple years of data.

        Args:
            other (Record): Data about a team's win-loss record

        Returns:
            Record: self
        """
        self.wins += other.wins
        self.losses += other.losses
        self.ties += other.ties
        self.conference_wins += other.conference_wins
        self.conference_losses += other.conference_losses
        self.conference_ties += other.conference_ties

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'games': self.games,
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties,
            'win_pct': round(self.win_pct, 4),
            'conference_games': self.conference_games,
            'conference_wins': self.conference_wins,
            'conference_losses': self.conference_losses,
            'conference_ties': self.conference_ties,
            'conference_win_pct': round(self.conference_win_pct, 4)
        }


class ConferenceRecord(db.Model):
    __tablename__ = 'conference_record'
    id = db.Column(db.Integer, primary_key=True)
    conference_id = db.Column(
        db.Integer, db.ForeignKey('conference.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    ties = db.Column(db.Integer, nullable=False)

    @property
    def games(self) -> float:
        return self.wins + self.losses + self.ties

    @property
    def win_pct(self) -> float:
        if self.games:
            return (self.wins + self.ties * 0.5) / self.games
        return 0.0

    @classmethod
    def add_records(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get win-loss records for all conferences for every year and add
        them to the database.

        Args:
            start_year (int): Year to start adding win-loss records
            end_year (int): Year to stop adding win-loss records
        """
        if start_year is None:
            query = Record.query.with_entities(Record.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding conference records for {year}')
            cls.add_records_for_one_year(year=year)

    @classmethod
    def add_records_for_one_year(cls, year: int) -> None:
        """
        Get win-loss records for all conferences for one year and add
        them to the database.

        Args:
            year (int): Year to add conference SRS ratings
        """
        conference_record = {}

        for conference in Conference.get_conferences(year=year):
            conference_record[conference.name] = cls(
                conference_id=conference.id,
                year=year,
                wins=0,
                losses=0,
                ties=0
            )

        for game in Game.get_non_conference_games(year=year):
            home_team = Team.query.filter_by(name=game.home_team).first()
            away_team = Team.query.filter_by(name=game.away_team).first()

            for team in [home_team, away_team]:
                if team is not None:
                    conference = team.get_conference(year=year)

                    if conference is not None:
                        result = game.determine_result(team=team.name)

                        if result == 'win':
                            conference_record[conference].wins += 1
                        elif result == 'loss':
                            conference_record[conference].losses += 1
                        elif result == 'tie':
                            conference_record[conference].ties += 1

        for record in conference_record.values():
            db.session.add(record)

        db.session.commit()

    def __add__(self, other: 'ConferenceRecord') -> 'ConferenceRecord':
        """
        Add two ConferenceRecord objects to combine multiple years of data.

        Args:
            other (ConferenceRecord): Data about a conference's
                non-conferencewin-loss record

        Returns:
            ConferenceRecord: self
        """
        self.wins += other.wins
        self.losses += other.losses
        self.ties += other.ties

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'games': self.games,
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties,
            'win_pct': round(self.win_pct, 4)
        }
