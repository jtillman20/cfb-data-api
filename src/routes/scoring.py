from typing import Union

from flask_restful import Resource

from models import Scoring
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class ScoringRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[Scoring, list[Scoring]]:
        """
        GET request to get scoring offense or defense for the given years.
        If team is provided only get scoring data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[Scoring, list[Scoring]]: Scoring data for all teams
                or only scoring data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='points_per_game')
        secondary_attr, secondary_reverse = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        scoring = Scoring.get_scoring(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(scoring, Scoring):
            return scoring

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, side_of_ball == 'offense']

        scoring = sort(data=scoring, attrs=attrs, reverses=reverses)
        return rank(data=scoring, attr=sort_attr)


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
    if attr == 'points_per_game':
        secondary_attr = 'games'

    elif attr in ['points', 'relative_points_per_game']:
        secondary_attr = 'points_per_game'

    else:
        secondary_attr = attr

    return secondary_attr, side_of_ball == 'offense'
