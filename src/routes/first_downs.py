from typing import Union

from flask import request
from flask_restful import Resource

from exceptions import InvalidRequestError
from models import FirstDowns
from utils import flask_response, rank, sort

ASC_SORT_ATTRS = ['plays_per_first_down']


class FirstDownsRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[FirstDowns, list[FirstDowns]]:
        """
        GET request to get first down offense or defense for the given
        years. If team is provided only get first down data for that
        team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
          Union[FirstDowns, list[FirstDowns]]: First down data for all
            teams or only first down data for one team
        """
        if side_of_ball not in ['offense', 'defense']:
            raise InvalidRequestError(
                "Side of ball must be either 'offense' or 'defense'")

        sort_attr = request.args.get('sort', 'total_per_game')
        attrs, reverses = secondary_sort(
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

        first_downs = FirstDowns.get_first_downs(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(first_downs, FirstDowns):
            return first_downs

        passing = sort(data=first_downs, attrs=attrs, reverses=reverses)
        return rank(data=passing, attr=sort_attr)


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
    if attr == 'total_per_game':
        secondary_attr = 'games'

    elif attr == 'plays_per_first_down':
        secondary_attr = 'plays'

    else:
        secondary_attr = 'total_per_game'

    if attr not in ASC_SORT_ATTRS:
        reverse = side_of_ball == 'offense'
    else:
        reverse = side_of_ball == 'defense'

    if secondary_attr not in ASC_SORT_ATTRS:
        secondary_reverse = side_of_ball == 'offense'
    else:
        secondary_reverse = side_of_ball == 'defense'

    return [secondary_attr, attr], [secondary_reverse, reverse]
