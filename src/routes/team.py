from flask import request
from flask_restful import Resource

from models import Team
from utils import flask_response

from exceptions import InvalidRequestError


class TeamRoute(Resource):
    @flask_response
    def get(self) -> list[Team]:
        """
        GET request for FBS teams for the given year. If conference is
        provided only get teams from that conference.

        Returns:
            list[Team]: All teams or teams filtered by conference
        """
        try:
            year = int(request.args['year'])
        except KeyError:
            raise InvalidRequestError('Year is a required query parameter')
        except ValueError:
            raise InvalidRequestError('Query parameter year must be an integer')

        conference = request.args.get('conference')
        return Team.get_teams(year=year, conference=conference)
