from inspect import stack
from typing import Union

from flask_restful import Resource

from models import FourthDowns, RedZone, ThirdDowns
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)

ASC_SORT_ATTRS = ['play_pct']


class FourthDownsRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[FourthDowns, list[FourthDowns]]:
        """
        GET request to get fourth down offense or defense for the given
        years. If team is provided only get fourth down data for that
        team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[FourthDowns, list[FourthDowns]]: Red zone down data for
                all teams or only red zone data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='conversion_pct')
        attrs, reverses = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        fourth_downs = FourthDowns.get_fourth_downs(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(fourth_downs, FourthDowns):
            return fourth_downs

        fourth_downs = sort(data=fourth_downs, attrs=attrs, reverses=reverses)
        return rank(data=fourth_downs, attr=sort_attr)


class RedZoneRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[RedZone, list[RedZone]]:
        """
        GET request to get red zone offense or defense for the given
        years. If team is provided only get red zone data for that
        team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[RedZone, list[RedZone]]: Red zone data for all
                teams or only red zone data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(name='sort', default_value='score_pct')
        secondary_attr, secondary_reverse = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)
        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        red_zone = RedZone.get_red_zone(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(red_zone, RedZone):
            return red_zone

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, side_of_ball == 'offense']

        red_zone = sort(data=red_zone, attrs=attrs, reverses=reverses)
        return rank(data=red_zone, attr=sort_attr)


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
    class_name = stack()[1][0].f_locals['self'].__class__.__name__

    if class_name in ['FourthDownsRoute', 'ThirdDownsRoute']:
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

    else:
        if attr in ['score_pct', 'td_pct', 'field_goal_pct',
                    'points_per_attempt']:
            secondary_attr = 'attempts'

        elif attr in ['attempts', 'scores']:
            secondary_attr = 'score_pct'

        elif attr == 'tds':
            secondary_attr = 'td_pct'

        elif attr == 'field_goals':
            secondary_attr = 'field_goal_pct'

        else:
            secondary_attr = attr

        return secondary_attr, side_of_ball == 'offense'
