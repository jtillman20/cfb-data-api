from typing import Union

from app import db


class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(100), nullable=True)

    record = db.relationship('Record', backref='team', lazy=True)
    srs = db.relationship('SRS', backref='team', lazy=True)

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
            return list(filter(
                lambda team: any(
                    year in membership.years and
                    conference == membership.conference.name
                    for membership in team.conferences
                ), teams
            ))

        return list(filter(
            lambda team: any(
                year in membership.years
                for membership in team.conferences
            ), teams
        ))

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
            years = [year for membership in team.conferences
                     for year in membership.years]

            active_years = list(filter(
                lambda year: year in range(start_year, end_year + 1), years
            ))

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
            return next(filter(
                lambda membership: year in membership.years,
                self.conferences
            )).conference.name
        except StopIteration:
            return None

    def serialize(self, year: int) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'conference': self.get_conference(year=year)
        }
