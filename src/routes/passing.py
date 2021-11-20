from typing import Union

from flask import request
from flask_restful import Resource

from exceptions import InvalidRequestError
from models import Passing, PassingPlays
from utils import flask_response, rank, sort

ASC_SORT_ATTRS = ['ints', 'int_pct']


class PassingRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[Passing, list[Passing]]:
        """
        GET request to get passing offense or defense for the given years.
        If team is provided only get passing data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
          Union[Passing, list[Passing]]: Passing data for all teams
              or only passing data for one team
        """
        if side_of_ball not in ['offense', 'defense']:
            raise InvalidRequestError(
                "Side of ball must be either 'offense' or 'defense'")

        sort_attr = request.args.get('sort', 'yards_per_game')
        attrs, reverses = secondary_sort(
            attr=sort_attr, side_of_ball=side_of_ball)

        try:
            start_year = int(request.args['start_year'])
        except KeyError:
            raise InvalidRequestError(
                'Start year is a required query parameter')
        except ValueError:
            raise InvalidRequestError(
                'Query parameter start year must be an integer')

        end_year = request.args.get('end_year')
        team = request.args.get('team')

        if end_year is not None:
            try:
                end_year = int(end_year)
            except ValueError:
                raise InvalidRequestError(
                    'Query parameter end year must be an integer')

        passing = Passing.get_passing(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(passing, Passing):
            return passing

        passing = sort(data=passing, attrs=attrs, reverses=reverses)
        return rank(data=passing, attr=sort_attr)


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
    if attr in ['yards_per_game', 'attemptsPerGame', 'completionsPerGame']:
        secondary_attr = 'games'

    elif attr in ['completion_pct', 'yards_per_attempt', 'td_pct', 'int_pct',
                  'td_int_ratio', 'rating']:
        secondary_attr = 'attempts'

    elif attr == 'attempts':
        secondary_attr = 'attemptsPerGame'

    elif attr == 'completions':
        secondary_attr = 'completionsPerGame'

    elif attr == 'yards_per_completions':
        secondary_attr = 'completions'

    elif attr == 'tds':
        secondary_attr = 'td_pct'

    elif attr == 'ints':
        secondary_attr = 'int_pct'

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


class PassingPlaysRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[PassingPlays, list[PassingPlays]]:
        """
        GET request to get passing plays or opponent passing plays for
        the given years. If team is provided only get passing play data
        for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
          Union[PassingPlays, list[PassingPlays]]: Passing play data
            for all teams or only passing play data for one team
        """
        if side_of_ball not in ['offense', 'defense']:
            raise InvalidRequestError(
                "Side of ball must be either 'offense' or 'defense'")

        sort_attr = request.args.get('sort', 'points_per_game')

        try:
            start_year = int(request.args['start_year'])
        except KeyError:
            raise InvalidRequestError(
                'Start year is a required query parameter')
        except ValueError:
            raise InvalidRequestError(
                'Query parameter start year must be an integer')

        end_year = request.args.get('end_year')
        team = request.args.get('team')

        if end_year is not None:
            try:
                end_year = int(end_year)
            except ValueError:
                raise InvalidRequestError(
                    'Query parameter end year must be an integer')

        passing_plays = PassingPlays.get_passing_plays(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(passing_plays, PassingPlays):
            return passing_plays

        attrs = ['plays', sort_attr]
        reverses = [True, side_of_ball == 'offense']

        passing_plays = sort(data=passing_plays, attrs=attrs, reverses=reverses)
        return rank(data=passing_plays, attr=sort_attr)
