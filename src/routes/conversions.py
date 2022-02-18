from typing import Union

from flask_restful import Resource

from models import ThirdDowns
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)

ASC_SORT_ATTRS = ['play_pct']


class ThirdDownsRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[ThirdDowns, list[ThirdDowns]]:
        """
        GET request to get third down offense or defense for the given
        years. If team is provided only get third down data for that
        team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[ThirdDowns, list[ThirdDowns]]: Third down data for all
                teams or only third down data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='conversion_pct')
        attrs, reverses = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        third_downs = ThirdDowns.get_third_downs(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(third_downs, ThirdDowns):
            return third_downs

        third_downs = sort(data=third_downs, attrs=attrs, reverses=reverses)
        return rank(data=third_downs, attr=sort_attr)


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
    if attr in ['conversion_pct', 'play_pct']:
        secondary_attr = 'attempts'

    elif attr in ['conversions', 'attempts']:
        secondary_attr = 'conversion_pct'

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