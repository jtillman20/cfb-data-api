from app import db
from .game import Game
from .record import Record
from .team import Team


class SRS(db.Model):
    __tablename__ = 'srs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    year = db.Column(db.Integer, nullable=False)
    scoring_margin = db.Column(db.Integer, nullable=False)
    opponent_rating = db.Column(db.Integer, nullable=False)
    wins = db.Column(db.Integer, nullable=True)
    losses = db.Column(db.Integer, nullable=True)
    ties = db.Column(db.Integer, nullable=True)

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

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.ties

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
        self.wins += other.wins
        self.losses += other.losses
        self.ties += other.ties

        return self

    @classmethod
    def add_srs_ratings(cls) -> None:
        """
        Get SRS ratings for all teams for every year and add them
        to the database.
        """
        query = Game.query.with_entities(Game.year).distinct()
        years = [year.year for year in query]

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
        teams = Team.get_teams(year=year)

        for team in teams:
            record = Record.get_records(start_year=year, team=team.name)
            srs_rating = cls(
                team_id=team.id,
                year=year,
                scoring_margin=0,
                opponent_rating=0,
                wins=record.wins,
                losses=record.losses,
                ties=record.ties
            )
            srs_ratings[team.name] = srs_rating

        # Add a combined rating for all FCS teams
        srs_ratings['FCS'] = cls(
            year=year,
            scoring_margin=0,
            opponent_rating=0,
            wins=0,
            losses=0,
            ties=0
        )

        fcs = srs_ratings['FCS']
        games = Game.get_games(year=year)

        for game in games:
            home_team = game.home_team
            away_team = game.away_team

            result = game.determine_result(team=home_team)
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

                if result == 'win':
                    fcs.wins += 1
                elif result == 'loss':
                    fcs.losses += 1
                elif result == 'tie':
                    fcs.ties += 1

            if away_team in srs_ratings:
                srs_ratings[away_team].scoring_margin -= margin
            else:
                fcs.scoring_margin -= margin

                if result == 'win':
                    fcs.losses += 1
                elif result == 'loss':
                    fcs.wins += 1
                elif result == 'tie':
                    fcs.ties += 1

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
        srs_ratings = cls.query.filter_by(year=year).all()

        for rating in srs_ratings:
            # The team_id will be None for the rating that represents the
            # combined rating of FCS teams
            if rating.team_id is None:
                rating.opponent_rating = 0
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
                    rating.opponent_rating += fbs_opponent.srs
                continue

            team = rating.team.name
            rating.opponent_rating = 0
            schedule = Game.get_games(year=year, team=team)

            for game in schedule:
                opponent_name = game.home_team if team == game.away_team \
                    else game.away_team
                opponent = cls.query.filter_by(year=year).join(
                    Team).filter_by(name=opponent_name).first()

                if opponent is not None:
                    rating.opponent_rating += opponent.srs
                else:
                    fcs_rating = cls.query.filter(
                        cls.team_id.is_(None), cls.year == year).first()
                    rating.opponent_rating += fcs_rating.srs

        db.session.commit()

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'srs': round(self.srs, 2),
            'sos': round(self.sos, 2),
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
