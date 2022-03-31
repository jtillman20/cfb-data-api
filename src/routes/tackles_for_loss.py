from typing import Union

from flask_restful import Resource

from models import TacklesForLoss
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)


class TacklesForLossRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[TacklesForLoss,
                                              list[TacklesForLoss]]:
        """
        GET request to get tackles for loss or opponent tackles for loss
        for the given years. If team is provided only get tackles for
        loss data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            Union[TacklesForLoss, list[TacklesForLoss]]: Tackles for
                loss data for all teams or only tackles for loss data
                for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='tackles_for_loss_per_game')
        secondary_attr, secondary_reverse = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        tfl = TacklesForLoss.get_tackles_for_loss(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(tfl, TacklesForLoss):
            return tfl

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, side_of_ball == 'offense']

        tfl = sort(data=tfl, attrs=attrs, reverses=reverses)
        return rank(data=tfl, attr=sort_attr)


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
    if attr == 'tackles_for_loss_per_game':
        secondary_attr = 'games'

    elif attr == 'tackles_for_loss':
        secondary_attr = 'tackles_for_loss_per_game'

    elif attr in ['tackles_for_loss_pct', 'yards_per_tackle_for_loss']:
        secondary_attr = 'tackles_for_loss'

    else:
        secondary_attr = attr

    return secondary_attr, side_of_ball == 'offense'
