from typing import Union

from flask_restful import Resource

from models import SRS, ConferenceSRS
from utils import (
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class SRSRoute(Resource):
    @flask_response
    def get(self) -> Union[SRS, list[SRS]]:
        """
        GET request to get SRS ratings for a given number of years.
        If team is provided, only get ratings for that team.

        Returns:
            Union[SRS, list[SRS]]: SRS ratings for all teams or only
                the SRS rating for one team
        """
        sort_attr = get_optional_param(name='sort', default_value='srs')
        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        ratings = SRS.get_srs_ratings(
            start_year=start_year, end_year=end_year, team=team)

        if isinstance(ratings, SRS):
            return ratings

        ratings = sort(data=ratings, attrs=[sort_attr], reverses=[True])
        return rank(data=ratings, attr=sort_attr)


class ConferenceSRSRoute(Resource):
    @flask_response
    def get(self) -> Union[ConferenceSRS, list[ConferenceSRS]]:
        """
        GET request to get conference SRS ratings for a given number
        of years. If conference is provided, only get ratings for that
        conference.

        Returns:
            Union[ConferenceSRS, list[ConferenceSRS]]: SRS ratings for
                all conferences or only the SRS rating for one conference
        """
        sort_attr = get_optional_param(name='sort', default_value='srs')
        start_year, end_year = get_multiple_year_params()
        conference = get_optional_param(name='conference')

        ratings = ConferenceSRS.get_srs_ratings(
            start_year=start_year, end_year=end_year, conference=conference)

        if isinstance(ratings, ConferenceSRS):
            return ratings

        ratings = sort(data=ratings, attrs=[sort_attr], reverses=[True])
        return rank(data=ratings, attr=sort_attr)
