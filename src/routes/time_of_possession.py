from flask_restful import Resource

from models import TimeOfPossession
from utils import (
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)

ASC_SORT_ATTRS = ['seconds_per_play']


class TimeOfPossessionRoute(Resource):
    @flask_response
    def get(self) -> list[TimeOfPossession]:
        """
        GET request to get time of possession for the given years. If
        team is provided only get time of possession data for that team.

        Returns:
            list[TimeOfPossession]: Time of possession data for all
                teams or only time of possession data for one team
        """
        sort_attr = get_optional_param(
            name='sort', default_value='time_of_possession_per_game')
        attrs, reverses = secondary_sort(attr=sort_attr)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        time_of_possession = TimeOfPossession.get_time_of_possession(
            start_year=start_year, end_year=end_year, team=team)

        time_of_possession = sort(data=time_of_possession, attrs=attrs, reverses=reverses)
        return rank(data=time_of_possession, attr=sort_attr)


def secondary_sort(attr: str) -> tuple:
    """
    Determine the secondary sort attribute and order when the
    primary sort attribute has the same value.

    Args:
        attr (str): The primary sort attribute

    Returns:
        tuple: Secondary sort attribute and sort order
    """
    if attr == 'time_of_possession':
        secondary_attr = 'time_of_possession_per_game'
    elif attr == 'time_of_possession_per_game':
        secondary_attr = 'games'
    elif attr == 'seconds_per_play':
        secondary_attr = 'plays'
    else:
        secondary_attr = attr

    reverse = attr not in ASC_SORT_ATTRS

    return [secondary_attr, attr], [True, reverse]
