from typing import Union

from flask_restful import Resource

from models import Total, ScrimmagePlays
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class TotalRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[Total, list[Total]]:
        """
        GET request to get total offense or defense for the given years.
        If team is provided only get total data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[Total, list[Total]]: Total data for all teams
                or only total data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='yards_per_game')
        secondary_attr, secondary_reverse = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        total = Total.get_total(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(total, Total):
            return total

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, side_of_ball == 'offense']

        total = sort(data=total, attrs=attrs, reverses=reverses)
        return rank(data=total, attr=sort_attr)


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
    if attr in ['yards_per_game', 'plays_per_game']:
        secondary_attr = 'games'

    elif attr in ['yards', 'relative_yards_per_game']:
        secondary_attr = 'yards_per_game'

    elif attr == 'yards_per_play':
        secondary_attr = 'plays'

    elif attr == 'plays':
        secondary_attr = 'plays_per_game'

    elif attr == 'relative_yards_per_play':
        secondary_attr = 'yards_per_play'

    else:
        secondary_attr = attr

    return secondary_attr, side_of_ball == 'offense'


class ScrimmagePlaysRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[ScrimmagePlays,
                                              list[ScrimmagePlays]]:
        """
        GET request to get scrimmage plays or opponent scrimmage plays
        for the given years. If team is provided only get scrimmage play
        data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[ScrimmagePlays, list[ScrimmagePlays]]: Scrimmage play
                data for all teams or only scrimmage play data for one
                team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(name='sort', default_value='ten_pct')
        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        scrimmage_plays = ScrimmagePlays.get_scrimmage_plays(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(scrimmage_plays, ScrimmagePlays):
            return scrimmage_plays

        attrs = ['plays', sort_attr]
        reverses = [True, side_of_ball == 'offense']

        scrimmage_plays = sort(
            data=scrimmage_plays, attrs=attrs, reverses=reverses)
        return rank(data=scrimmage_plays, attr=sort_attr)
