from flask_restful import Resource

from models import Rushing, RushingPlays
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class RushingRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> list[Rushing]:
        """
        GET request to get rushing offense or defense for the given years.
        If team is provided only get rushing data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
          list[Rushing]: Rushing data for all teams or only rushing
            data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='yards_per_game')
        attrs, reverses = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        rushing = Rushing.get_rushing(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        rushing = sort(data=rushing, attrs=attrs, reverses=reverses)
        return rank(data=rushing, attr=sort_attr)


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
    if attr in ['yards_per_game', 'attempts_per_game']:
        secondary_attr = 'games'

    elif attr in ['yards_per_attempt', 'td_pct']:
        secondary_attr = 'attempts'

    elif attr == 'attempts':
        secondary_attr = 'attempts_per_game'

    elif attr == 'tds':
        secondary_attr = 'td_pct'

    else:
        secondary_attr = attr

    return [secondary_attr, attr], [side_of_ball == 'offense'] * 2


class RushingPlaysRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> list[RushingPlays]:
        """
        GET request to get rushing plays or opponent rushing plays for
        the given years. If team is provided only get rushing play data
        for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            list[RushingPlays]: Rushing play data for all teams or only
                rushing play data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(name='sort', default_value='ten_pct')
        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        rushing_plays = RushingPlays.get_rushing_plays(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        attrs = ['plays', sort_attr]
        reverses = [True, side_of_ball == 'offense']

        rushing_plays = sort(data=rushing_plays, attrs=attrs, reverses=reverses)
        return rank(data=rushing_plays, attr=sort_attr)
