from flask_restful import Resource

from models import FirstDowns
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)

ASC_SORT_ATTRS = ['plays_per_first_down']


class FirstDownsRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> list[FirstDowns]:
        """
        GET request to get first down offense or defense for the given
        years. If team is provided only get first down data for that
        team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            list[FirstDowns]: First down data for all teams or only
                first down data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='total_per_game')
        attrs, reverses = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        first_downs = FirstDowns.get_first_downs(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

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
        secondary_attr = attr

    if attr not in ASC_SORT_ATTRS:
        reverse = side_of_ball == 'offense'
    else:
        reverse = side_of_ball == 'defense'

    if secondary_attr not in ASC_SORT_ATTRS:
        secondary_reverse = side_of_ball == 'offense'
    else:
        secondary_reverse = side_of_ball == 'defense'

    return [secondary_attr, attr], [secondary_reverse, reverse]
