from typing import Union

from flask import request
from flask_restful import Resource

from exceptions import InvalidRequestError
from models import Turnovers
from utils import flask_response, rank, sort

ASC_SORT_ATTRS = ['ints', 'fumbles', 'giveaways']


class TurnoversRoute(Resource):
    @flask_response
    def get(self) -> Union[Turnovers, list[Turnovers]]:
        """
        GET request to get turnovers and opponent turnovers for the
        given years. If team is provided only get scoring data for that
        team.

        Returns:
          Union[Turnovers, list[Turnovers]]: Turnover data for all teams
              or only turnover data for one team
        """
        sort_attr = request.args.get('sort', 'margin_per_game')
        secondary_attr, secondary_reverse = secondary_sort(attr=sort_attr)

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

        turnovers = Turnovers.get_turnovers(
            start_year=start_year, end_year=end_year, team=team)

        if isinstance(turnovers, Turnovers):
            return turnovers

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, sort_attr not in ASC_SORT_ATTRS]

        turnovers = sort(data=turnovers, attrs=attrs, reverses=reverses)
        return rank(data=turnovers, attr=sort_attr)


def secondary_sort(attr: str) -> tuple:
    """
    Determine the secondary sort attribute and order when the
    primary sort attribute has the same value.

    Args:
        attr (str): The primary sort attribute

    Returns:
        tuple: Secondary sort attribute and sort order
    """
    if attr in ['ints', 'fumbles']:
        secondary_attr = 'giveaways'

    elif attr in ['opponent_ints', 'opponent_fumbles']:
        secondary_attr = 'takeways'

    elif attr in ['giveaways', 'takeaways']:
        secondary_attr = 'games'

    elif attr in ['margin_per_game']:
        secondary_attr = 'margin'

    elif attr == 'margin':
        secondary_attr = 'margin_per_game'

    else:
        secondary_attr = attr

    return secondary_attr, secondary_attr not in ASC_SORT_ATTRS
