from typing import Union

from flask_restful import Resource

from models import Record
from utils import (
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)

ASC_SORT_ATTRS = ['losses', 'conference_losses']


class RecordRoute(Resource):
    @flask_response
    def get(self) -> Union[Record, list[Record]]:
        """
        GET request to get win-loss records for a given number of years.
        If team is provided, only get records for that team.

        Returns:
            Union[Record, list[Record]]: Win-loss records for all teams
                or only win-loss records for one team
        """
        sort_attr = get_optional_param(name='sort', default_value='win_pct')
        secondary_attr, secondary_reverse = secondary_sort(attr=sort_attr)
        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        records = Record.get_records(
            start_year=start_year, end_year=end_year, team=team)

        if isinstance(records, Record):
            return records

        attrs = [secondary_attr, sort_attr]
        reverses = [secondary_reverse, sort_attr not in ASC_SORT_ATTRS]

        records = sort(data=records, attrs=attrs, reverses=reverses)
        return rank(data=records, attr=sort_attr)


def secondary_sort(attr: str) -> tuple:
    """
    Determine the secondary sort attribute and order when the
    primary sort attribute has the same value.

    Args:
        attr (str): The primary sort attribute

    Returns:
        tuple: Secondary sort attribute and sort order
    """
    if attr in ['wins', 'losses', 'ties']:
        secondary_attr = 'win_pct'

    elif attr == 'win_pct':
        secondary_attr = 'wins'

    elif attr in ['coference_wins', 'conferences_losses', 'conference_ties']:
        secondary_attr = 'conference_win_pct'

    elif attr == 'conference_win_pct':
        secondary_attr = 'conference_wins'

    else:
        secondary_attr = attr

    return secondary_attr, True
