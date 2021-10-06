from typing import Union

from app import db
from .game import Game
from .record import Record
from .team import Team


class RPI(db.Model):
    __tablename__ = 'rpi'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    year = db.Column(db.Integer, nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    ties = db.Column(db.Integer, nullable=False)
    opponent_win_pct = db.Column(db.Integer, nullable=False)
    opponents_opponent_win_pct = db.Column(db.Integer, nullable=True)
    opponent_games = db.Column(db.Integer, nullable=True)

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.ties

    @property
    def win_pct(self) -> float:
        if self.games:
            return (self.wins + self.ties * 0.5) / self.games
        return 0.0

    @property
    def opponent_avg_win_pct(self) -> float:
        if self.games:
            return self.opponent_win_pct / self.games
        return 0.0

    @property
    def opponents_opponent_avg_win_pct(self) -> float:
        if self.opponent_games:
            return self.opponents_opponent_win_pct / self.opponent_games
        return 0.0

    @property
    def sos(self) -> float:
        return self.opponent_avg_win_pct * 0.55 + \
               self.opponents_opponent_avg_win_pct * 0.45

    @property
    def rpi(self) -> float:
        return self.win_pct * 0.35 + self.sos * 0.65

    def __add__(self, other: 'RPI') -> 'RPI':
        """
        Add two RPI objects to combine multiple years of data.

        Args:
            other (RPI): Data about a team's RPI rating

        Returns:
            RPI: self
        """
        self.wins += other.wins
        self.losses += other.losses
        self.ties += other.ties
        self.opponent_win_pct += other.opponent_win_pct
        self.opponents_opponent_win_pct += other.opponents_opponent_win_pct
        self.opponent_games += other.opponent_games

        return self

    @classmethod
    def get_rpi_ratings(cls, start_year: int, end_year: int = None,
                        team: str = None) -> Union['RPI', list['RPI']]:
        """
        Get RPI ratings for qualifying teams for the given years.
        If team is provided, only get ratings for that team.

        Args:
            start_year (int): Year to start getting ratings
            end_year (int): Year to stop getting ratings
            team (str): Team for which to get ratings

        Returns:
            Union[RPI, list[RPI]]: RPI ratings for qualifying teams or
                only the RPI rating for one team
        """
        if end_year is None:
            end_year = start_year

        qualifying_teams = Team.get_qualifying_teams(
            start_year=start_year, end_year=end_year)

        query = cls.query.join(Team).filter(
            cls.year >= start_year, cls.year <= end_year)

        if team is not None:
            ratings = query.filter(team == Team.name).all()
            return sum(ratings[1:], ratings[0])

        ratings = {}
        for team_name in qualifying_teams:
            team_rating = query.filter(team_name == Team.name).all()

            if team_rating:
                ratings[team_name] = sum(team_rating[1:], team_rating[0])

        return [ratings[team] for team in sorted(ratings.keys())]

    @classmethod
    def add_rpi_ratings(cls) -> None:
        """
        Get RPI ratings for all teams for every year and add them
        to the database.
        """
        query = Game.query.with_entities(Game.year).distinct()
        years = [year.year for year in query]

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
        teams = Team.get_teams(year=year)

        # Add a combined rating for all FCS teams
        rpi_ratings['FCS'] = cls(
            year=year,
            wins=0,
            losses=0,
            ties=0,
            opponent_win_pct=0
        )
        fcs = rpi_ratings['FCS']

        for team in teams:
            record = Record.get_records(start_year=year, team=team.name)
            rpi_rating = cls(
                team_id=team.id,
                year=year,
                wins=record.wins,
                losses=record.losses,
                ties=record.ties,
                opponent_win_pct=0,
                opponents_opponent_win_pct=0,
                opponent_games=0
            )
            rpi_ratings[team.name] = rpi_rating

        fcs_games = Game.get_fcs_games(year=year)

        for game in fcs_games:
            away_team = Team.query.filter_by(name=game.away_team).first()
            if away_team is not None:
                away_conference = away_team.get_conference(year=year)
            else:
                away_conference = None

            fbs_team = game.home_team if away_conference is None \
                else game.away_team
            result = game.determine_result(team=fbs_team)

            if result == 'win':
                fcs.losses += 1
            elif result == 'loss':
                fcs.wins += 1
            else:
                fcs.ties += 1

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
        rpi_ratings = cls.query.filter_by(year=year).all()

        for rating in rpi_ratings:
            # The team_id will be None for the rating that represents the
            # combined rating of FCS teams
            if rating.team_id is None:
                games = Game.get_fcs_games(year=year)

                for game in games:
                    away_team = Team.query.filter_by(
                        name=game.away_team).first()
                    if away_team is not None:
                        away_conference = away_team.get_conference(year=year)
                    else:
                        away_conference = None

                    fbs_team = game.home_team if away_conference is None \
                        else game.away_team
                    fbs_opponent = cls.query.filter_by(year=year).join(
                        Team).filter_by(name=fbs_team).first()

                    result = game.determine_result(team=fbs_team)
                    games = fbs_opponent.games - 1
                    wins = fbs_opponent.wins
                    ties = fbs_opponent.ties

                    if result == 'win':
                        win_pct = (wins + ties * 0.5) / games
                    elif result == 'loss':
                        win_pct = (wins - 1 + ties * 0.5) / games
                    else:
                        win_pct = (wins + (ties - 1) * 0.5) / games

                    rating.opponent_win_pct += win_pct

                continue

            team = rating.team.name
            schedule = Game.get_games(year=year, team=team)

            for game in schedule:
                result = game.determine_result(team=team)
                opponent_name = game.home_team if team == game.away_team \
                    else game.away_team
                opponent = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name).first()

                if opponent is not None:
                    games = opponent.games - 1
                    wins = opponent.wins
                    ties = opponent.ties

                    if result == 'win':
                        win_pct = (wins + ties * 0.5) / games
                    elif result == 'loss':
                        win_pct = (wins - 1 + ties * 0.5) / games
                    else:
                        win_pct = (wins + (ties - 1) * 0.5) / games

                    opponent_win_pct = win_pct
                else:
                    fcs_rating = cls.query.filter(
                        cls.team_id.is_(None), cls.year == year).first()

                    if fcs_rating.win_pct > 0.25:
                        opponent_win_pct = fcs_rating.win_pct
                    else:
                        opponent_win_pct = 0.25

                rating.opponent_win_pct += opponent_win_pct

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
        rpi_ratings = cls.query.filter_by(year=year).filter(
            cls.team_id.is_not(None)).all()

        for rating in rpi_ratings:
            team = rating.team.name
            schedule = Game.get_games(year=year, team=team)

            for game in schedule:
                opponent_name = game.home_team if team == game.away_team \
                    else game.away_team
                opponent = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name).first()

                if opponent is not None:
                    opponent_win_pct = opponent.opponent_win_pct
                    rating.opponent_games += opponent.games
                else:
                    fcs_rating = cls.query.filter(
                        cls.team_id.is_(None), cls.year == year).first()
                    opponent_win_pct = fcs_rating.opponent_win_pct
                    rating.opponent_games += fcs_rating.games

                rating.opponents_opponent_win_pct += opponent_win_pct

        db.session.commit()

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'rpi': round(self.rpi, 4),
            'sos': round(self.sos, 4),
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
