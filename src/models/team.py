from app import db


class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(100), nullable=True)

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

    def get_conference(self, year: int) -> str:
        """
        Get the conference a team belongs to for the given year.

        Args:
            year (int): Year to get the team's conference

        Returns:
            str: Conference name
        """
        return next(filter(
            lambda membership: year in membership.years,
            self.conferences
        )).conference.name

    def serialize(self, year: int) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'conference': self.get_conference(year=year)
        }
