from sqlalchemy_utils import ScalarListType

from app import db


class Conference(db.Model):
    __tablename__ = 'conference'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    @classmethod
    def get_conferences(cls, year: int) -> list['Conference']:
        """
        Get all FBS conferences for the given year.

        Args:
            year (int): Year to get conferences for

        Returns:
            list[Conference]: All conferences
        """
        return list(filter(
            lambda conference: any(
                year in membership.years for membership in conference.teams
            ), cls.query.all()
        ))

    def get_teams(self, year: int) -> list[str]:
        """
        Get the teams that belong to the conference for the given year.

        Args:
            year (int): Year to get a conference's teams

        Returns:
            list[str]: Teams who belong to the conference
        """
        return list(map(
            lambda membership: membership.team.name,
            filter(lambda membership: year in membership.years, self.teams)
        ))


class ConferenceMembership(db.Model):
    __tablename__ = 'conference_membership'
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), primary_key=True)
    conference_id = db.Column(
        db.Integer, db.ForeignKey('conference.id'), primary_key=True)
    years = db.Column(ScalarListType(int))
    conference = db.relationship('Conference', backref='teams')
    team = db.relationship('Team', backref='conferences')
