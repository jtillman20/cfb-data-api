from typing import Union

from app import db


class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(100), nullable=True)

    ap_poll = db.relationship('APPoll', backref='team', lazy=True)
    ap_poll_ranking = db.relationship(
        'APPollRanking', backref='team', lazy=True)
    field_goals = db.relationship('FieldGoals', backref='team', lazy=True)
    first_downs = db.relationship('FirstDowns', backref='team', lazy=True)
    fourth_downs = db.relationship('FourthDowns', backref='team', lazy=True)
    kickoff_return_plays = db.relationship(
        'KickoffReturnPlays', backref='team', lazy=True)
    kickoff_returns = db.relationship(
        'KickoffReturns', backref='team', lazy=True)
    kickoffs = db.relationship('Kickoffs', backref='team', lazy=True)
    passing = db.relationship('Passing', backref='team', lazy=True)
    passing_plays = db.relationship('PassingPlays', backref='team', lazy=True)
    pats = db.relationship('PATs', backref='team', lazy=True)
    penalties = db.relationship('Penalties', backref='team', lazy=True)
    punt_return_plays = db.relationship(
        'PuntReturnPlays', backref='team', lazy=True)
    punt_returns = db.relationship('PuntReturns', backref='team', lazy=True)
    punting = db.relationship('Punting', backref='team', lazy=True)
    record = db.relationship('Record', backref='team', lazy=True)
    red_zone = db.relationship('RedZone', backref='team', lazy=True)
    rpi = db.relationship('RPI', backref='team', lazy=True)
    rushing = db.relationship('Rushing', backref='team', lazy=True)
    rushing_plays = db.relationship('RushingPlays', backref='team', lazy=True)
    sacks = db.relationship('Sacks', backref='team', lazy=True)
    scoring = db.relationship('Scoring', backref='team', lazy=True)
    scrimmage_plays = db.relationship(
        'ScrimmagePlays', backref='team', lazy=True)
    srs = db.relationship('SRS', backref='team', lazy=True)
    tackles_for_loss = db.relationship(
        'TacklesForLoss', backref='team', lazy=True)
    third_downs = db.relationship('ThirdDowns', backref='team', lazy=True)
    total = db.relationship('Total', backref='team', lazy=True)
    turnovers = db.relationship('Turnovers', backref='team', lazy=True)

    @classmethod
    def get_teams(cls, year: int, conference: str = None) -> list['Team']:
        """
        Get FBS teams for the given year. If conference is provided,
        only get teams belonging to that conference.

        Args:
            year (int): Year to get teams
            conference (str): Conference name to filter teams

        Returns:
            list[Team]: All teams or teams filtered by conference
        """
        teams = cls.query.all()

        if conference is not None:
            return [
                team for team in teams
                if any(
                    year in membership.years and
                    conference == membership.conference.name
                    for membership in team.conferences
                )
            ]

        return [
            team for team in teams
            if any(year in membership.years for membership in team.conferences)
        ]

    @classmethod
    def get_qualifying_teams(cls, start_year: int, end_year: int) -> list[str]:
        """
        Get teams that qualify for records and stats for the given years.
        The criteria is that the teams must be in FBS for the end year
        and at least 50% of the years.

        Args:
            start_year (int): Start year
            end_year (int): End year

        Returns:
            list[str]: Qualifying teams
        """
        min_years = (end_year - start_year + 1) / 2
        teams = cls.get_teams(year=end_year)
        qualifying_teams = []

        for team in teams:
            years = [
                year for membership in team.conferences
                for year in membership.years
            ]

            active_years = [
                year for year in years
                if year in range(start_year, end_year + 1)
            ]

            if len(active_years) >= min_years:
                qualifying_teams.append(team.name)

        return qualifying_teams

    def get_conference(self, year: int) -> Union[str, None]:
        """
        Get the conference a team belongs to for the given year, if the
        team was in FBS for the given year.

        Args:
            year (int): Year to get the team's conference

        Returns:
            str: Conference name
        """
        try:
            return next((
                membership for membership in self.conferences
                if year in membership.years
            )).conference.name
        except StopIteration:
            return None

    def serialize(self, year: int) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'conference': self.get_conference(year=year)
        }
