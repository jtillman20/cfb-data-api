from typing import Union

from flask_restful import Resource

from models import Fumbles
from utils import (
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)

ASC_SORT_ATTRS = ['fumbles', 'fumbles_lost', 'fumbles_lost_per_game',
                  'fumble_lost_pct']


class FumblesRoute(Resource):
    @flask_response
    def get(self) -> Union[Fumbles, list[Fumbles]]:
        """
        GET request to get fumbles and opponent fumbles for the given
        years. If team is provided only get fumble data for that team.

        Returns:
            Union[Fumbles, list[Fumbles]]: Fumble data for all teams
                or only fumble data for one team
        """
        sort_attr = get_optional_param(
            name='sort', default_value='fumbles')
        attrs, reverses = secondary_sort(attr=sort_attr)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        fumbles = Fumbles.get_fumbles(
            start_year=start_year, end_year=end_year, team=team)

        if isinstance(fumbles, Fumbles):
            return fumbles

        fumbles = sort(data=fumbles, attrs=attrs, reverses=reverses)
        return rank(data=fumbles, attr=sort_attr)


def secondary_sort(attr: str) -> tuple:
    """
    Determine the secondary sort attribute and order when the
    primary sort attribute has the same value.

    Args:
        attr (str): The primary sort attribute

    Returns:
        tuple: Secondary sort attribute and sort order
    """
    if attr in ['fumbles', 'fumbles_lost_per_game', 'fumble_lost_pct']:
        secondary_attr = 'fumbles_lost'
    elif attr == 'fumbles_lost':
        secondary_attr = 'fumbles_lost_per_game'
    elif attr in ['opponent_fumbles', 'fumbles_recovered_per_game',
                  'fumble_recovery_pct']:
        secondary_attr = 'fumbles_recovered'
    elif attr == 'all_fumbles':
        secondary_attr = 'all_fumble_recovery_pct'
    elif attr == 'all_fumble_recovery_pct':
        secondary_attr = 'all_fumbles'
    elif attr in ['fumbles_forced', 'fumbles_forced_per_game']:
        secondary_attr = 'forced_fumble_pct'
    elif attr == 'forced_fumble_pct':
        secondary_attr = 'forced_fumbles'
    else:
        secondary_attr = attr

    secondary_reverse = secondary_attr not in ASC_SORT_ATTRS
    reverse = attr not in ASC_SORT_ATTRS

    return [secondary_attr, attr], [secondary_reverse, reverse]
