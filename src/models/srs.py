from numpy import sum

from app import db
from .conference import Conference
from .game import Game
from .record import ConferenceRecord, Record
from .team import Team


class SRS(db.Model):
    __tablename__ = 'srs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    year = db.Column(db.Integer, nullable=False)
    scoring_margin = db.Column(db.Integer, nullable=False)
    opponent_rating = db.Column(db.Integer, nullable=False)
    record_id = db.Column(db.Integer, db.ForeignKey('record.id'), nullable=False)

    @property
    def avg_scoring_margin(self) -> float:
        if self.record.games:
            return self.scoring_margin / self.record.games
        return 0.0

    @property
    def sos(self) -> float:
        if self.record.games:
            return self.opponent_rating / self.record.games
        return 0.0

    @property
    def srs(self) -> float:
        return self.avg_scoring_margin + self.sos

    @classmethod
    def get_srs_ratings(cls, start_year: int, end_year: int = None,
                        team: str = None) -> list['SRS']:
        """
        Get SRS ratings for qualifying teams for the given years.
        If team is provided, only get ratings for that team.

        Args:
            start_year (int): Year to start getting ratings
            end_year (int): Year to stop getting ratings
            team (str): Team for which to get ratings

        Returns:
            list[SRS]: SRS ratings for qualifying teams or only the SRS
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
    def add_srs_ratings(cls, start_year: int, end_year: int = None) -> None:
        """
        Get SRS ratings for all teams for every year and add them
        to the database.

        Args:
            start_year (int): Year to start adding ratings
            end_year (int): Year to stop adding ratings
        """
        if end_year is None:
            end_year = start_year
        years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding SRS ratings for {year}')
            cls.add_srs_ratings_for_one_year(year=year)

    @classmethod
    def add_srs_ratings_for_one_year(cls, year: int) -> None:
        """
        Get SRS ratings for all teams for one year and add them
        to the database.

        Args:
            year (int): Year to add SRS ratings
        """
        cls.add_ratings_with_scoring_margins(year=year)
        for _ in range(20):
            cls.add_sos(year=year)

    @classmethod
    def add_ratings_with_scoring_margins(cls, year: int) -> None:
        """
        Get the scoring margin for every team for the given year.
        The scoring margin for each game is adjusted to have a
        maximum of 35 and minumum of 7.

        Args:
            year (int): Year to get scoring margins
        """
        max_margin = 35
        min_margin = 7
        srs_ratings = {}

        for team in Team.get_teams(year=year):
            record = Record.query.filter_by(team_id=team.id, year=year).first()
            srs_rating = cls(
                team_id=team.id,
                year=year,
                scoring_margin=0,
                opponent_rating=0,
                record_id=record.id
            )
            srs_ratings[team.name] = srs_rating

        # Add a combined rating for all FCS teams
        fcs_record = Record.query.filter(
            Record.year == year, Record.team_id.is_(None)).first()
        srs_ratings['FCS'] = cls(
            year=year,
            scoring_margin=0,
            opponent_rating=0,
            record_id=fcs_record.id
        )
        fcs = srs_ratings['FCS']

        for game in Game.get_games(year=year):
            home_team = game.home_team
            away_team = game.away_team
            margin = game.home_score - game.away_score

            if margin > max_margin:
                margin = max_margin
            elif margin < -max_margin:
                margin = -max_margin
            elif 0 < margin < min_margin:
                margin = min_margin
            elif 0 > margin > -min_margin:
                margin = -min_margin

            if home_team in srs_ratings:
                srs_ratings[home_team].scoring_margin += margin
            else:
                fcs.scoring_margin += margin

            if away_team in srs_ratings:
                srs_ratings[away_team].scoring_margin -= margin
            else:
                fcs.scoring_margin -= margin

        for srs in srs_ratings.values():
            db.session.add(srs)

        db.session.commit()

    @classmethod
    def add_sos(cls, year: int) -> None:
        """
        Get the strength of schedule for every team for the given year.

        Args:
            year (int): Year to get strength of schedule
        """
        for rating in cls.query.filter_by(year=year).all():
            # The team_id will be None for the rating that represents the
            # combined rating of FCS teams
            if rating.team_id is None:
                rating.opponent_rating = 0

                for game in Game.get_fcs_games(year=year):
                    away_team = Team.query.filter_by(
                        name=game.away_team).first()
                    if away_team is not None:
                        away_conference = away_team.get_conference(year=year)
                    else:
                        away_conference = None

                    fbs_team = (game.home_team if away_conference is None
                                else game.away_team)
                    fbs_opponent = cls.query.filter_by(year=year).join(
                        Team).filter_by(name=fbs_team).first()
                    rating.opponent_rating += fbs_opponent.srs

                continue

            team = rating.team.name
            rating.opponent_rating = 0

            for game in Game.get_games(year=year, team=team):
                opponent_name = (game.home_team if team == game.away_team
                                 else game.away_team)
                opponent = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name).first()

                if opponent is not None:
                    rating.opponent_rating += opponent.srs
                else:
                    fcs_rating = cls.query.filter(
                        cls.team_id.is_(None), cls.year == year).first()
                    rating.opponent_rating += fcs_rating.srs

        db.session.commit()

    def __add__(self, other: 'SRS') -> 'SRS':
        """
        Add two SRS objects to combine multiple years of data.

        Args:
            other (SRS): Data about a team's SRS rating

        Returns:
            SRS: self
        """
        self.scoring_margin += other.scoring_margin
        self.opponent_rating += other.opponent_rating
        self.record += other.record

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'srs': round(self.srs, 2),
            'sos': round(self.sos, 2),
            'wins': self.record.wins,
            'losses': self.record.losses,
            'ties': self.record.ties
        }


class ConferenceSRS(db.Model):
    __tablename__ = 'conference_srs'
    id = db.Column(db.Integer, primary_key=True)
    conference_id = db.Column(
        db.Integer, db.ForeignKey('conference.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    scoring_margin = db.Column(db.Integer, nullable=False)
    opponent_rating = db.Column(db.Integer, nullable=False)
    games = db.Column(db.Integer, nullable=True)
    record_id = db.Column(
        db.Integer, db.ForeignKey('conference_record.id'), nullable=False)

    @property
    def avg_scoring_margin(self) -> float:
        if self.games:
            return self.scoring_margin / self.games
        return 0.0

    @property
    def sos(self) -> float:
        if self.games:
            return self.opponent_rating / self.games
        return 0.0

    @property
    def srs(self) -> float:
        return self.avg_scoring_margin + self.sos

    @classmethod
    def get_srs_ratings(cls, start_year: int, end_year: int = None,
                        conference: str = None) -> list['ConferenceSRS']:
        """
        Get SRS ratings for all conferences for the given years.
        If conference is provided, only get ratings for that conference.

        Args:
            start_year (int): Year to start getting ratings
            end_year (int): Year to stop getting ratings
            conference (str): Conference for which to get ratings

        Returns:
            list[ConferenceSRS]: SRS ratings for all conferences or only
                the SRS rating for one conference
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Conference).filter(
            cls.year >= start_year, cls.year <= end_year)

        if conference is not None:
            ratings = query.filter(conference == Conference.name).all()
            return [sum(ratings)] if ratings else []

        ratings = {}
        for conference in Conference.get_qualifying_conferences(
                start_year=start_year, end_year=end_year):
            conference_rating = query.filter(
                conference == Conference.name).all()

            if conference_rating:
                ratings[conference] = sum(conference_rating)

        return [ratings[conference] for conference in sorted(ratings.keys())]

    @classmethod
    def add_srs_ratings(cls, start_year: int, end_year: int = None) -> None:
        """
        Get SRS ratings for all conferences for every year and add
        them to the database.

        Args:
            start_year (int): Year to start adding ratings
            end_year (int): Year to stop adding ratings
        """
        if end_year is None:
            end_year = start_year
        years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding conference SRS ratings for {year}')
            cls.add_srs_ratings_for_one_year(year=year)

    @classmethod
    def add_srs_ratings_for_one_year(cls, year: int) -> None:
        """
        Get conference SRS ratings for all teams for one year and add
        them to the database.

        Args:
            year (int): Year to add conference SRS ratings
        """
        for conference in Conference.get_conferences(year=year):
            record = ConferenceRecord.query.filter_by(
                conference_id=conference.id, year=year).first()
            srs_rating = cls(
                conference_id=conference.id,
                year=year,
                scoring_margin=0,
                opponent_rating=0,
                games=0,
                record_id=record.id
            )

            for team in conference.get_teams(year=year):
                rating = SRS.query.filter_by(year=year).join(
                    Team).filter_by(name=team).first()

                srs_rating.scoring_margin += rating.scoring_margin
                srs_rating.opponent_rating += rating.opponent_rating
                srs_rating.games += rating.record.games

            db.session.add(srs_rating)

        db.session.commit()

    def __add__(self, other: 'ConferenceSRS') -> 'ConferenceSRS':
        """
        Add two ConferenceSRS objects to combine multiple years of data.

        Args:
            other (ConferenceSRS): Data about a conference's SRS rating

        Returns:
            ConferenceSRS: self
        """
        self.scoring_margin += other.scoring_margin
        self.opponent_rating += other.opponent_rating
        self.games += other.games
        self.record += other.record

        return self

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'conference': self.conference.serialize(year=self.year),
            'year': self.year,
            'srs': round(self.srs, 2),
            'sos': round(self.sos, 2),
            'wins': self.record.wins,
            'losses': self.record.losses,
            'ties': self.record.ties
        }
