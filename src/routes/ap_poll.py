from flask import request
from flask_restful import Resource

from exceptions import InvalidRequestError
from models import APPollRanking
from utils import flask_response


class APPollRankingRoute(Resource):
    @flask_response
    def get(self) -> list[APPollRanking]:
        """
        GET request to get AP Poll rankings for the given year.
        If week is provided, only get rankings for that week. If team
        is provided, only get rankings for that team.

        Returns:
            list[APPollRanking]: AP Poll rankings
        """
        try:
            year = int(request.args['year'])
        except KeyError:
            raise InvalidRequestError(
                'Year is a required query parameter')
        except ValueError:
            raise InvalidRequestError(
                'Query parameter year must be an integer')

        week = request.args.get('week')
        team = request.args.get('team')

        if week is not None:
            try:
                week = int(week)
            except ValueError:
                raise InvalidRequestError(
                    'Query parameter week must be an integer')

        return APPollRanking.get_rankings(year=year, week=week, team=team)
