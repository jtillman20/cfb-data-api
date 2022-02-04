from typing import Union

from flask_restful import Resource

from models import ConferenceRPI, RPI
from utils import (
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class RPIRoute(Resource):
    @flask_response
    def get(self) -> Union[RPI, list[RPI]]:
        """
        GET request to get RPI ratings for a given number of years.
        If team is provided, only get ratings for that team.

        Returns:
            Union[RPI, list[RPI]]: RPI ratings for all teams or only
                the RPI rating for one team
        """
        sort_attr = get_optional_param(name='sort', default_value='rpi')
        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        ratings = RPI.get_rpi_ratings(
            start_year=start_year, end_year=end_year, team=team)

        if isinstance(ratings, RPI):
            return ratings

        ratings = sort(data=ratings, attrs=[sort_attr], reverses=[True])
        return rank(data=ratings, attr=sort_attr)


class ConferenceRPIRoute(Resource):
    @flask_response
    def get(self) -> Union[ConferenceRPI, list[ConferenceRPI]]:
        """
        GET request to get conference RPI ratings for a given number
        of years. If conference is provided, only get ratings for that
        conference.

        Returns:
            Union[ConferenceRPI, list[ConferenceRPI]]: RPI ratings for
                all conferences or only the RPI rating for one conference
        """
        sort_attr = get_optional_param(name='sort', default_value='rpi')
        start_year, end_year = get_multiple_year_params()
        conference = get_optional_param(name='conference')

        ratings = ConferenceRPI.get_rpi_ratings(
            start_year=start_year, end_year=end_year, conference=conference)

        if isinstance(ratings, ConferenceRPI):
            return ratings

        ratings = sort(data=ratings, attrs=[sort_attr], reverses=[True])
        return rank(data=ratings, attr=sort_attr)
