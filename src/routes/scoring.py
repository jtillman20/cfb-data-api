from typing import Union

from flask import request
from flask_restful import Resource

from exceptions import InvalidRequestError
from models import Scoring
from utils import flask_response, rank, sort


class ScoringRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[Scoring, list[Scoring]]:
        """
        GET request to get scoring offense or defense for the given years.
        If team is provided only get scoring data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
          Union[Scoring, list[Scoring]]: Scoring data for all teams
              or only scoring data for one team
        """
        if side_of_ball not in ['offense', 'defense']:
            raise InvalidRequestError(
                "Side of ball must be either 'offense' or 'defense'")

        sort_attr = request.args.get('sort', 'points_per_game')
        secondary_attr, secondary_reverse = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

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

        scoring = Scoring.get_scoring(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(scoring, Scoring):
            return scoring

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, side_of_ball == 'offense']

        scoring = sort(data=scoring, attrs=attrs, reverses=reverses)
        return rank(data=scoring, attr=sort_attr)


def secondary_sort(attr: str, side_of_ball: str) -> tuple:
    """
    Determine the secondary sort attribute and order when the
    primary sort attribute has the same value.

    Args:
        attr (str): The primary sort attribute
        side_of_ball (str): Offense or defense

    Returns:
        tuple: Secondary sort attribute and sort order
    """
    if attr == 'points_per_game':
        secondary_attr = 'points'

    elif attr == 'points' or attr == 'relative_points_per_game':
        secondary_attr = 'points_per_game'

    else:
        secondary_attr = attr

    return secondary_attr, side_of_ball == 'offense'
