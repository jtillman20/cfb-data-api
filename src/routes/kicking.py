from typing import Union

from flask_restful import Resource

from models import FieldGoals, PATs
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class FieldGoalsRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[FieldGoals, list[FieldGoals]]:
        """
        GET request to get field goals or opponent field goals for the
        given years. If team is provided only get field goal data for
        that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[FieldGoals, list[FieldGoals]]: Field goal data for
                all teams or only field goal data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(name='sort', default_value='pct')
        secondary_attr, secondary_reverse = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        field_goals = FieldGoals.get_field_goals(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(field_goals, FieldGoals):
            return field_goals

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, side_of_ball == 'offense']

        field_goals = sort(data=field_goals, attrs=attrs, reverses=reverses)
        return rank(data=field_goals, attr=sort_attr)


class PATsRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[PATs, list[PATs]]:
        """
        GET request to get PATs or opponent PATs for the given years.
        If team is provided only get PAT data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[PATs, list[PATs]]: PAT data for all teams or only PAT
                data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(name='sort', default_value='pct')
        secondary_attr, secondary_reverse = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        pats = PATs.get_pats(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(pats, FieldGoals):
            return pats

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, side_of_ball == 'offense']

        field_goals = sort(data=pats, attrs=attrs, reverses=reverses)
        return rank(data=field_goals, attr=sort_attr)


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
    if attr in ['attempts', 'field_goals', 'pats']:
        secondary_attr = 'pct'

    elif attr in ['attempts_per_game', 'field_goals_per_game', 'pats_per_game']:
        secondary_attr = 'games'

    elif attr == 'pct':
        secondary_attr = 'attempts'

    else:
        secondary_attr = attr

    return secondary_attr, side_of_ball == 'offense'
