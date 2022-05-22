from inspect import stack
from typing import Union

from flask_restful import Resource

from models import Kickoffs, KickoffReturns
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)

ASC_SORT_ATTRS = ['out_of_bounds', 'out_of_bounds_pct']


class KickoffsRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[Kickoffs, list[Kickoffs]]:
        """
        GET request to get kickoffs or opponent kickoffs for the given
        years. If team is provided only get kickoff data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[Kickoffs, list[Kickoffs]]: Kickoff data for all teams
                or only kickoff data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='yards_per_kickoff')
        attrs, reverses = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        kickoffs = Kickoffs.get_kickoffs(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(kickoffs, Kickoffs):
            return kickoffs

        kickoffs = sort(data=kickoffs, attrs=attrs, reverses=reverses)
        return rank(data=kickoffs, attr=sort_attr)


class KickoffReturnsRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[KickoffReturns,
                                              list[KickoffReturns]]:
        """
        GET request to get kickoff returns or opponent kickoff returns
        for the given years. If team is provided only get kickoff
        return data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[KickoffReturns, list[KickoffReturns]]: Kickoff return
                data for all teams or only kickoff return data for one
                team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='yards_per_return')
        attrs, reverses = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        returns = KickoffReturns.get_kickoff_returns(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(returns, Kickoffs):
            return returns

        returns = sort(data=returns, attrs=attrs, reverses=reverses)
        return rank(data=returns, attr=sort_attr)


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

    if attr in ['yards_per_kickoff', 'touchback_pct', 'out_of_bounds_pct',
                'onside_pct']:
        secondary_attr = 'kickoffs'

    elif attr in ['returns', 'returns_per_game', 'yards_per_game']:
        secondary_attr = 'games'

    elif attr in ['yards_per_return', 'td_pct']:
        return ['returns', attr], [True, side_of_ball == 'offense']

    elif attr == 'kickoffs':
        secondary_attr = 'yards_per_kickoff'

    elif attr == 'yards':
        if class_name == 'Kickoffs':
            secondary_attr = 'kickoffs'
        else:
            secondary_attr = 'games'

    elif attr == 'touchbacks':
        secondary_attr = 'touchback_pct'

    elif attr == 'out_of_bounds':
        secondary_attr = 'out_of_bounds_pct'

    elif attr == 'onside':
        secondary_attr = 'onside_pct'

    elif attr == 'tds':
        secondary_attr = 'td_pct'

    elif attr == 'return_pct':
        secondary_attr = 'punts'

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

    if secondary_attr == 'kickoffs':
        secondary_reverse = True

    return [secondary_attr, attr], [secondary_reverse, reverse]
