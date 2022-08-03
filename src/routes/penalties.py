from flask_restful import Resource

from models import Penalties
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class PenaltiesRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> list[Penalties]:
        """
        GET request to get penalties or opponent penalties for a given
        number of years. If team is provided, only get records for that
        team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            list[Penalties]: Penalty data for all teams or only penalty
                for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='yards_per_game')
        secondary_attr, secondary_reverse = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        penalties = Penalties.get_penalties(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, side_of_ball == 'defense']

        penalties = sort(data=penalties, attrs=attrs, reverses=reverses)
        return rank(data=penalties, attr=sort_attr)


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
    if attr in ['penalties_per_game', 'yards_per_game']:
        secondary_attr = 'games'

    elif attr == 'yards_per_penalty':
        secondary_attr = 'penalties'

    elif attr == 'penalties':
        secondary_attr = 'yards'

    else:
        secondary_attr = attr

    return secondary_attr, side_of_ball == 'defense'
