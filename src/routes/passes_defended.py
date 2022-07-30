from typing import Union

from flask_restful import Resource

from models import PassesDefended
from utils import (
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class PassesDefendedRoute(Resource):
    @flask_response
    def get(self) -> Union[PassesDefended, list[PassesDefended]]:
        """
        GET request to get passes defended for the given years. If team
        is provided only get passed defended data for that team.

        Returns:
            Union[PassesDefended, list[PassesDefended]]: Passes defended
                data for all teams or only passes defended data for one
                team
        """
        sort_attr = get_optional_param(
            name='sort', default_value='passes_defended_per_game')
        secondary_attr, secondary_reverse = secondary_sort(attr=sort_attr)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        passes_defended = PassesDefended.get_passes_defended(
            start_year=start_year, end_year=end_year, team=team)

        if isinstance(passes_defended, PassesDefended):
            return passes_defended

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, True]

        passes_defended = sort(data=passes_defended, attrs=attrs, reverses=reverses)
        return rank(data=passes_defended, attr=sort_attr)


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
        secondary_attr = 'int_pct'
    elif attr == 'int_pct':
        secondary_attr = 'ints'
    elif attr == 'passes_defended':
        secondary_attr = 'passes_defended_per_game'
    elif attr in ['passes_broken_up', 'passes_defended_per_game',
                  'passes_defended_pct']:
        secondary_attr = 'passes_defended'
    elif attr == 'forced_incompletion_pct':
        secondary_attr = 'attempts'
    else:
        secondary_attr = attr

    return secondary_attr, True
