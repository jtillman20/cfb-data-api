from numpy import sum

from app import db
from .conference import Conference
from .game import Game
from .record import ConferenceRecord, Record
from .team import Team


class RPI(db.Model):
    __tablename__ = 'rpi'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    year = db.Column(db.Integer, nullable=False)
    record_id = db.Column(db.Integer, db.ForeignKey('record.id'), nullable=False)
    opponent_win_pct = db.Column(db.Integer, nullable=False)
    opponents_opponent_win_pct = db.Column(db.Integer, nullable=True)
    opponent_games = db.Column(db.Integer, nullable=True)

    @property
    def opponent_avg_win_pct(self) -> float:
        if self.record.games:
            return self.opponent_win_pct / self.record.games
        return 0.0

    @property
    def opponents_opponent_avg_win_pct(self) -> float:
        if self.opponent_games:
            return self.opponents_opponent_win_pct / self.opponent_games
        return 0.0

    @property
    def sos(self) -> float:
        return (self.opponent_avg_win_pct * 0.55 +
                self.opponents_opponent_avg_win_pct * 0.45)

    @property
    def rpi(self) -> float:
        return self.record.win_pct * 0.35 + self.sos * 0.65

    @classmethod
    def get_rpi_ratings(cls, start_year: int, end_year: int = None,
                        team: str = None) -> list['RPI']:
        """
        Get RPI ratings for qualifying teams for the given years.
        If team is provided, only get ratings for that team.

        Args:
            start_year (int): Year to start getting ratings
            end_year (int): Year to stop getting ratings
            team (str): Team for which to get ratings

        Returns:
            list[RPI]: RPI ratings for qualifying teams or only the RPI
                rating for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.year >= start_year, cls.year <= end_year)

        if team is not None:
            ratings = query.filter_by(name=team).all()
            return [sum(ratings)] if ratings else []

        ratings = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_rating = query.filter_by(name=team_name).all()

            if team_rating:
                ratings[team_name] = sum(team_rating)

        return [ratings[team] for team in sorted(ratings.keys())]

    @classmethod
    def add_rpi_ratings(cls, start_year: int, end_year: int = None) -> None:
        """
        Get RPI ratings for all teams for every year and add them
        to the database.

        Args:
            start_year (int): Year to start adding ratings
            end_year (int): Year to stop adding ratings
        """
        if end_year is None:
            end_year = start_year
        years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding RPI ratings for {year}')
            cls.add_rpi_ratings_for_one_year(year=year)

    @classmethod
    def add_rpi_ratings_for_one_year(cls, year: int) -> None:
        """
        Get RPI ratings for all teams for one year and add them
        to the database.

        Args:
            year (int): Year to add RPI ratings
        """
        cls.add_records(year=year)
        cls.add_opponent_win_pct(year=year)
        cls.add_opponents_opponent_win_pct(year=year)

    @classmethod
    def add_records(cls, year: int) -> None:
        """
        Get the record for every team for the given year as part of
        the RPI rating.

        Args:
            year (int): Year to get records
        """
        rpi_ratings = {}

        for team in Team.get_teams(year=year):
            record = Record.query.filter_by(team_id=team.id, year=year).first()
            rpi_rating = cls(
                team_id=team.id,
                year=year,
                record_id=record.id,
                opponent_win_pct=0,
                opponents_opponent_win_pct=0,
                opponent_games=0
            )
            rpi_ratings[team.name] = rpi_rating

        # Add a combined rating for all FCS teams
        fcs_record = Record.query.filter(
            Record.year == year, Record.team_id.is_(None)).first()
        rpi_ratings['FCS'] = cls(
            year=year,
            record_id=fcs_record.id,
            opponent_win_pct=0
        )

        for rpi in rpi_ratings.values():
            db.session.add(rpi)

        db.session.commit()

    @classmethod
    def add_opponent_win_pct(cls, year: int) -> None:
        """
        Get the win percentage for every team's opponents for the
        given year as the strength of schedule part of the RPI
        rating formula.

        Args:
            year (int): Year to get strength of schedule
        """
        for rating in cls.query.filter_by(year=year).all():
            # The team_id will be None for the rating that represents the
            # combined rating of FCS teams
            if rating.team_id is None:
                for game in Game.get_fcs_games(year=year):
                    away_team = Team.query.filter_by(
                        name=game.away_team).first()
                    away_conference = (away_team.get_conference(year=year)
                                       if away_team is not None else None)

                    fbs_team = (game.home_team if away_conference is None
                                else game.away_team)
                    fbs_opponent = cls.query.filter_by(year=year).join(
                        Team).filter_by(name=fbs_team).first()

                    result = game.determine_result(team=fbs_team)
                    games = fbs_opponent.record.games - 1
                    wins = fbs_opponent.record.wins
                    ties = fbs_opponent.record.ties

                    if result == 'win':
                        win_pct = (wins + ties * 0.5) / games
                    elif result == 'loss':
                        win_pct = (wins - 1 + ties * 0.5) / games
                    else:
                        win_pct = (wins + (ties - 1) * 0.5) / games

                    rating.opponent_win_pct += win_pct

                continue

            team = rating.team.name
            for game in Game.get_games(year=year, team=team):
                result = game.determine_result(team=team)
                opponent_name = (game.home_team if team == game.away_team
                                 else game.away_team)
                opponent = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name).first()

                if opponent is not None:
                    games = opponent.record.games - 1
                    wins = opponent.record.wins
                    ties = opponent.record.ties

                    if result == 'win':
                        win_pct = (wins + ties * 0.5) / games
                    elif result == 'loss':
                        win_pct = (wins - 1 + ties * 0.5) / games
                    else:
                        win_pct = (wins + (ties - 1) * 0.5) / games

                else:
                    fcs_rating = cls.query.filter(
                        cls.team_id.is_(None), cls.year == year).first()
                    win_pct = (fcs_rating.record.win_pct
                               if fcs_rating.record.win_pct > 0.25 else 0.25)

                rating.opponent_win_pct += win_pct

        db.session.commit()

    @classmethod
    def add_opponents_opponent_win_pct(cls, year: int) -> None:
        """
        Get the win percentage for every team's opponents' opponents
        for the given year as the opponent's strength of schedule part
        of the RPI rating formula.

        Args:
            year (int): Year to get opponent strength of schedule
        """
        for rating in cls.query.filter_by(year=year).filter(
                cls.team_id.is_not(None)).all():
            team = rating.team.name

            for game in Game.get_games(year=year, team=team):
                opponent_name = (game.home_team if team == game.away_team
                                 else game.away_team)
                opponent = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name).first()

                if opponent is not None:
                    win_pct = opponent.opponent_win_pct
                    rating.opponent_games += opponent.record.games
                else:
                    fcs_rating = cls.query.filter(
                        cls.team_id.is_(None), cls.year == year).first()
                    win_pct = fcs_rating.opponent_win_pct
                    rating.opponent_games += fcs_rating.record.games

                rating.opponents_opponent_win_pct += win_pct

        db.session.commit()

    def __add__(self, other: 'RPI') -> 'RPI':
        """
        Add two RPI objects to combine multiple years of data.

        Args:
            other (RPI): Data about a team's RPI rating

        Returns:
            RPI: self
        """
        self.record += other.record
        self.opponent_win_pct += other.opponent_win_pct
        self.opponents_opponent_win_pct += other.opponents_opponent_win_pct
        self.opponent_games += other.opponent_games

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'rpi': round(self.rpi, 4),
            'sos': round(self.sos, 4),
            'wins': self.record.wins,
            'losses': self.record.losses,
            'ties': self.record.ties
        }


class ConferenceRPI(db.Model):
    __tablename__ = 'conference_rpi'
    id = db.Column(db.Integer, primary_key=True)
    conference_id = db.Column(
        db.Integer, db.ForeignKey('conference.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    record_id = db.Column(
        db.Integer, db.ForeignKey('conference_record.id'), nullable=False)
    opponent_win_pct = db.Column(db.Integer, nullable=False)
    opponents_opponent_win_pct = db.Column(db.Integer, nullable=True)
    opponent_games = db.Column(db.Integer, nullable=True)

    @property
    def opponent_avg_win_pct(self) -> float:
        if self.record.games:
            return self.opponent_win_pct / self.record.games
        return 0.0

    @property
    def opponents_opponent_avg_win_pct(self) -> float:
        if self.opponent_games:
            return self.opponents_opponent_win_pct / self.opponent_games
        return 0.0

    @property
    def sos(self) -> float:
        return (self.opponent_avg_win_pct * 0.55 +
                self.opponents_opponent_avg_win_pct * 0.45)

    @property
    def rpi(self) -> float:
        return self.record.win_pct * 0.35 + self.sos * 0.65

    @classmethod
    def get_rpi_ratings(cls, start_year: int, end_year: int = None,
                        conference: str = None) -> list['ConferenceRPI']:
        """
        Get RPI ratings for all conferences for the given years.
        If conference is provided, only get ratings for that conference.

        Args:
            start_year (int): Year to start getting ratings
            end_year (int): Year to stop getting ratings
            conference (str): Conference for which to get ratings

        Returns:
            list[ConferenceRPI]: RPI ratings for all conferences or only
                the RPI rating for one conference
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Conference).filter(
            cls.year >= start_year, cls.year <= end_year)

        if conference is not None:
            ratings = query.filter_by(name=conference).all()
            return [sum(ratings)] if ratings else []

        ratings = {}
        for conference in Conference.get_qualifying_conferences(
                start_year=start_year, end_year=end_year):
            conference_rating = query.filter_by(name=conference).all()

            if conference_rating:
                ratings[conference] = sum(conference_rating)

        return [ratings[conference] for conference in sorted(ratings.keys())]

    @classmethod
    def add_rpi_ratings(cls, start_year: int, end_year: int = None) -> None:
        """
        Get RPI ratings for all conferences for every year and add
        them to the database.

        Args:
            start_year (int): Year to start adding ratings
            end_year (int): Year to stop adding ratings
        """
        if end_year is None:
            end_year = start_year
        years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding conference RPI ratings for {year}')
            cls.add_rpi_ratings_for_one_year(year=year)

    @classmethod
    def add_rpi_ratings_for_one_year(cls, year: int) -> None:
        """
        Get conference RPI ratings for all teams for one year and add
        them to the database.

        Args:
            year (int): Year to add conference RPI ratings
        """
        cls.add_records(year=year)
        cls.add_opponent_win_pct(year=year)
        cls.add_opponents_opponent_win_pct(year=year)

    @classmethod
    def add_records(cls, year: int) -> None:
        """
        Get the non-conference record for every conference for the
        given year as part of the RPI rating.

        Args:
            year (int): Year to get records
        """
        for conference in Conference.get_conferences(year=year):
            record = ConferenceRecord.query.filter_by(
                conference_id=conference.id, year=year).first()
            db.session.add(cls(
                conference_id=conference.id,
                year=year,
                record_id=record.id,
                opponent_win_pct=0,
                opponents_opponent_win_pct=0,
                opponent_games=0
            ))

        db.session.commit()

    @classmethod
    def add_opponent_win_pct(cls, year: int) -> None:
        """
        Get the win percentage for every conference's non-conference
        opponents for the given year as the strength of schedule part
        of the RPI rating formula.

        Args:
            year (int): Year to get strength of schedule
        """
        for rating in cls.query.filter_by(year=year).all():
            conference = rating.conference
            schedule = []

            for team in conference.get_teams(year=year):
                for game in Game.get_games(year=year, team=team):
                    if not game.is_conference_game():
                        schedule.append(game)

            for game in schedule:
                home_team = Team.query.filter_by(name=game.home_team).first()
                if home_team is not None:
                    if conference.name == home_team.get_conference(year=year):
                        team = game.home_team
                    else:
                        team = game.away_team
                else:
                    team = game.away_team

                result = game.determine_result(team=team)
                opponent_name = (game.home_team if team == game.away_team
                                 else game.away_team)
                opponent = RPI.query.filter_by(year=year).join(Team).filter_by(
                    name=opponent_name).first()

                if opponent is not None:
                    games = opponent.record.games - 1
                    wins = opponent.record.wins
                    ties = opponent.record.ties

                    if result == 'win':
                        win_pct = (wins + ties * 0.5) / games
                    elif result == 'loss':
                        win_pct = (wins - 1 + ties * 0.5) / games
                    else:
                        win_pct = (wins + (ties - 1) * 0.5) / games

                else:
                    fcs_rating = RPI.query.filter(
                        RPI.team_id.is_(None), RPI.year == year).first()
                    win_pct = (fcs_rating.record.win_pct
                               if fcs_rating.record.win_pct > 0.25 else 0.25)

                rating.opponent_win_pct += win_pct

        db.session.commit()

    @classmethod
    def add_opponents_opponent_win_pct(cls, year: int) -> None:
        """
        Get the win percentage for every conference's non-conference
        opponents' opponents for the given year as the opponent's
        strength of schedule part of the RPI rating formula.

        Args:
            year (int): Year to get opponent strength of schedule
        """
        for rating in cls.query.filter_by(year=year).all():
            conference = rating.conference
            schedule = []

            for team in conference.get_teams(year=year):
                for game in Game.get_games(year=year, team=team):
                    if not game.is_conference_game():
                        schedule.append(game)

            for game in schedule:
                home_team = Team.query.filter_by(name=game.home_team).first()
                if home_team is not None:
                    if conference.name == home_team.get_conference(year=year):
                        team = game.home_team
                    else:
                        team = game.away_team
                else:
                    team = game.away_team

                opponent_name = (game.home_team if team == game.away_team
                                 else game.away_team)
                opponent = RPI.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name).first()

                if opponent is not None:
                    win_pct = opponent.opponent_win_pct
                    rating.opponent_games += opponent.record.games
                else:
                    fcs_rating = RPI.query.filter(
                        RPI.team_id.is_(None), RPI.year == year).first()
                    win_pct = fcs_rating.opponent_win_pct
                    rating.opponent_games += fcs_rating.record.games

                rating.opponents_opponent_win_pct += win_pct

        db.session.commit()

    def __add__(self, other: 'RPI') -> 'RPI':
        """
        Add two RPI objects to combine multiple years of data.

        Args:
            other (RPI): Data about a team's RPI rating

        Returns:
            RPI: self
        """
        self.record += other.record
        self.opponent_win_pct += other.opponent_win_pct
        self.opponents_opponent_win_pct += other.opponents_opponent_win_pct
        self.opponent_games += other.opponent_games

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'conference': self.conference.serialize(year=self.year),
            'year': self.year,
            'rpi': round(self.rpi, 4),
            'sos': round(self.sos, 4),
            'wins': self.record.wins,
            'losses': self.record.losses,
            'ties': self.record.ties
        }
