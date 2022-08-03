from flask_restful import Resource

from models import Punting, PuntReturns, PuntReturnPlays
from utils import (
    check_side_of_ball,
    flask_response,
    get_multiple_year_params,
    get_optional_param,
    rank,
    sort
)

ASC_SORT_ATTRS = ['punts', 'punts_per_game', 'returns', 'returns_per_game',
                  'yards', 'yards_per_game']


class PuntingRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> list[Punting]:
        """
        GET request to get punting or opponent punting for the given
        years. If team is provided only get punting data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            list[Punting]: Punting data for all teams or only punting
                data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='yards_per_punt')
        attrs, reverses = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        punting = Punting.get_punting(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        punting = sort(data=punting, attrs=attrs, reverses=reverses)
        return rank(data=punting, attr=sort_attr)


class PuntReturnsRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> list[PuntReturns]:
        """
        GET request to get punt returns or opponent punt returns for
        the given years. If team is provided only get punt return data
        for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            list[PuntReturns]: Punt return data for all teams or only
                punt return data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(
            name='sort', default_value='yards_per_return')
        attrs, reverses = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        returns = PuntReturns.get_punt_returns(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

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
    if attr in ['punts', 'punts_per_game', 'yards', 'yards_per_game', 'returns',
                'returns_per_game']:
        secondary_attr = 'games'

    elif attr in ['yards_per_punt', 'plays_per_punt']:
        secondary_attr = 'punts'

    elif attr in ['yards_per_return', 'td_pct']:
        return ['returns', attr], [True, side_of_ball == 'offense']

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

    return [secondary_attr, attr], [secondary_reverse, reverse]


class PuntReturnPlaysRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> list[PuntReturnPlays]:
        """
        GET request to get punt return plays or opponent punt return
        plays for the given years. If team is provided only get punt
        return play data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
            list[PuntReturnPlays]: Punt return play data for all teams
                or only punt return play data for one team
        """
        check_side_of_ball(value=side_of_ball)

        sort_attr = get_optional_param(name='sort', default_value='twenty_pct')
        start_year, end_year = get_multiple_year_params()
        team = get_optional_param(name='team')

        return_plays = PuntReturnPlays.get_punt_return_plays(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        attrs = ['returns', sort_attr]
        reverses = [True, side_of_ball == 'offense']

        return_plays = sort(data=return_plays, attrs=attrs, reverses=reverses)
        return rank(data=return_plays, attr=sort_attr)
