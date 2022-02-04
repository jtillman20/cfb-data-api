from flask_restful import Resource

from models import Conference
from utils import flask_response, get_year_param


class ConferenceRoute(Resource):
    @flask_response
    def get(self) -> list[Conference]:
        """
        GET request for FBS conferences for the given year.

        Returns:
            list[Conference]: All conferences
        """
        year = get_year_param()
        return Conference.get_conferences(year=year)
