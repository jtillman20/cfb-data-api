from flask import request
from flask_restful import Resource

from models import Conference
from utils import flask_response

from exceptions import InvalidRequestError


class ConferenceRoute(Resource):
    @flask_response
    def get(self) -> list[Conference]:
        """
        GET request for FBS conferences for the given year.

        Returns:
            list[Conference]: All conferences
        """
        try:
            year = int(request.args['year'])
        except KeyError:
            raise InvalidRequestError('Year is a required query parameter')
        except ValueError:
            raise InvalidRequestError('Query parameter year must be an integer')

        return Conference.get_conferences(year=year)
