from typing import Union

from flask_restful import Resource

from models import Sacks
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class SacksRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[Sacks, list[Sacks]]:
        """
        GET request to get sacks or opponent sacls for the given years.
        If team is provided only get sack data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[Sacks, list[Sacks]]: Sack data for all teams or only
                sack data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='sacks_per_game')
        secondary_attr, secondary_reverse = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        sacks = Sacks.get_sacks(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(sacks, Sacks):
            return sacks

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, side_of_ball == 'offense']

        sacks = sort(data=sacks, attrs=attrs, reverses=reverses)
        return rank(data=sacks, attr=sort_attr)


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
    if attr == 'sacks_per_game':
        secondary_attr = 'games'

    elif attr == 'sacks':
        secondary_attr = 'sacks_per_game'

    elif attr in ['sack_pct', 'yards_per_sack']:
        secondary_attr = 'sacks'

    else:
        secondary_attr = attr

    return secondary_attr, side_of_ball == 'offense'
