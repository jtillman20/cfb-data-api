from typing import Union

from flask import request
from flask_restful import Resource

from exceptions import InvalidRequestError
from models import SRS, ConferenceSRS
from utils import flask_response, rank, sort


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
        sort_attr = request.args.get('sort', 'srs')

        try:
            start_year = int(request.args['start_year'])
        except KeyError:
            raise InvalidRequestError(
                'Start year is a required query parameter')
        except ValueError:
            raise InvalidRequestError(
                'Query parameter start year must be an integer')

        end_year = request.args.get('end_year')
        team = request.args.get('team')

        if end_year is not None:
            try:
                end_year = int(end_year)
            except ValueError:
                raise InvalidRequestError(
                    'Query parameter end year must be an integer')

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
        sort_attr = request.args.get('sort', 'srs')

        try:
            start_year = int(request.args['start_year'])
        except KeyError:
            raise InvalidRequestError(
                'Start year is a required query parameter')
        except ValueError:
            raise InvalidRequestError(
                'Query parameter start year must be an integer')

        end_year = request.args.get('end_year')
        conference = request.args.get('conference')

        if end_year is not None:
            try:
                end_year = int(end_year)
            except ValueError:
                raise InvalidRequestError(
                    'Query parameter end year must be an integer')

        ratings = ConferenceSRS.get_srs_ratings(
            start_year=start_year, end_year=end_year, conference=conference)

        if isinstance(ratings, ConferenceSRS):
            return ratings

        ratings = sort(data=ratings, attrs=[sort_attr], reverses=[True])
        return rank(data=ratings, attr=sort_attr)
