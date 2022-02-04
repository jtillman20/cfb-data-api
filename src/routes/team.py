from flask_restful import Resource

from models import Team
from utils import flask_response, get_optional_param, get_year_param


class TeamRoute(Resource):
    @flask_response
    def get(self) -> list[Team]:
        """
        GET request for FBS teams for the given year. If conference is
        provided only get teams from that conference.

        Returns:
            list[Team]: All teams or teams filtered by conference
        """
        year = get_year_param()
        conference = get_optional_param(name='conference')
        return Team.get_teams(year=year, conference=conference)
