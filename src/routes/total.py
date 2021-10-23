from typing import Union

from flask import request
from flask_restful import Resource

from exceptions import InvalidRequestError
from models import Total
from utils import flask_response, rank, sort


class TotalRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[Total, list[Total]]:
        """
        GET request to get total offense or defense for the given years.
        If team is provided only get total data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
          Union[Total, list[Total]]: Total data for all teams
              or only total data for one team
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

        total = Total.get_total(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(total, Total):
            return total

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, side_of_ball == 'offense']

        scoring = sort(data=total, attrs=attrs, reverses=reverses)
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
    if attr in ['yards_per_game', 'plays_per_game']:
        secondary_attr = 'games'

    elif attr in ['yards', 'relative_yards_per_game']:
        secondary_attr = 'yards_per_game'

    elif attr == 'yards_per_play':
        secondary_attr = 'plays'

    elif attr == 'plays':
        secondary_attr = 'plays_per_game'

    elif attr == 'relative_yards_per_play':
        secondary_attr = 'yards_per_play'

    else:
        secondary_attr = attr

    return secondary_attr, side_of_ball == 'offense'
