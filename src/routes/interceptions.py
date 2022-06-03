from typing import Union

from flask_restful import Resource

from models import Interceptions
from utils import (
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class InterceptionsRoute(Resource):
    @flask_response
    def get(self) -> Union[Interceptions, list[Interceptions]]:
        """
        GET request to get punting or opponent punting for the given
        years. If team is provided only get punting data for that team.

        Returns:
            Union[Punting, list[Punting]]: Punting data for all teams
                or only punting data for one team
        """
        sort_attr = get_optional_param(
            name='sort', default_value='ints')
        secondary_attr, secondary_reverse = secondary_sort(attr=sort_attr)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        ints = Interceptions.get_interceptions(
            start_year=start_year, end_year=end_year, team=team)

        if isinstance(ints, Interceptions):
            return ints

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, True]

        ints = sort(data=ints, attrs=attrs, reverses=reverses)
        return rank(data=ints, attr=sort_attr)


def secondary_sort(attr: str) -> tuple:
    """
    Determine the secondary sort attribute and order when the
    primary sort attribute has the same value.

    Args:
        attr (str): The primary sort attribute

    Returns:
        tuple: Secondary sort attribute and sort order
    """
    if attr == 'ints':
        secondary_attr = 'ints_per_game'
    elif attr == 'yards':
        secondary_attr = 'yards_per_int'
    elif attr == 'tds':
        secondary_attr = 'td_pct'
    elif attr in ['ints_per_game', 'yards_per_int', 'td_pct']:
        secondary_attr = 'ints'
    else:
        secondary_attr = attr

    return secondary_attr, True
