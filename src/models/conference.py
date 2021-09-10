from sqlalchemy_utils import ScalarListType

from app import db
from scraper import SportsReferenceScraper
from .team import Team


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

    def serialize(self, year: int) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'teams': self.get_teams(year=year)
        }


class ConferenceMembership(db.Model):
    __tablename__ = 'conference_membership'
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), primary_key=True)
    conference_id = db.Column(
        db.Integer, db.ForeignKey('conference.id'), primary_key=True)
    years = db.Column(ScalarListType(int))
    conference = db.relationship('Conference', backref='teams')
    team = db.relationship('Team', backref='conferences')

    @classmethod
    def add_teams_and_conferences(cls, start_year: int, end_year: int) -> None:
        """
        Get all FBS teams and conferences for the given years and add
        them to the database. For each year, add an association for
        each team and the conference to which it belongs.

        Args:
            start_year (int): Year to begin adding teams/conferences
            end_year (int): Year to stop adding teams/conferences
        """
        scraper = SportsReferenceScraper()

        teams = set()
        conferences = set()
        memberships = {}

        for year in range(start_year, end_year + 1):
            html_content = scraper.get_html_data(path=f'{year}-standings.html')
            team_conference_data = scraper.parse_standings_html_data(
                html_content=html_content)

            for team, conference in team_conference_data:
                teams.add(team)
                conferences.add(conference)

                if team in memberships:
                    team_conferences = memberships[team]
                    if conference in team_conferences:
                        team_conferences[conference].append(year)
                    else:
                        team_conferences[conference] = [year]
                else:
                    memberships[team] = {conference: [year]}

        for team in sorted(teams):
            db.session.add(Team(name=team))

        for conference in sorted(conferences):
            db.session.add(Conference(name=conference))

        for team in sorted(memberships):
            for conference, years in memberships[team].items():
                team_id = Team.query.filter_by(name=team).first().id
                conference_id = Conference.query.filter_by(
                    name=conference).first().id

                db.session.add(ConferenceMembership(
                    team_id=team_id,
                    conference_id=conference_id,
                    years=years
                ))

        db.session.commit()
