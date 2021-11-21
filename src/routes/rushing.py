from typing import Union

from flask import request
from flask_restful import Resource

from exceptions import InvalidRequestError
from models import Rushing, RushingPlays
from utils import flask_response, rank, sort


class RushingRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[Rushing, list[Rushing]]:
        """
        GET request to get rushing offense or defense for the given years.
        If team is provided only get rushing data for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
          Union[rushing, list[rushing]]: Rushing data for all teams
              or only rushing data for one team
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

        rushing = Rushing.get_rushing(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(rushing, Rushing):
            return rushing

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
    if attr in ['yards_per_game', 'attemptsPerGame']:
        secondary_attr = 'games'

    elif attr in ['yards_per_attempt', 'td_pct']:
        secondary_attr = 'attempts'

    elif attr == 'attempts':
        secondary_attr = 'attemptsPerGame'

    elif attr == 'tds':
        secondary_attr = 'td_pct'

    else:
        secondary_attr = attr

    return [secondary_attr, attr], [side_of_ball == 'offense'] * 2


class RushingPlaysRoute(Resource):
    @flask_response
    def get(self, side_of_ball: str) -> Union[RushingPlays, list[RushingPlays]]:
        """
        GET request to get rushing plays or opponent rushing plays for
        the given years. If team is provided only get rushing play data
        for that team.

        Args:
            side_of_ball (str): Offense or defense

        Returns:
          Union[RushingPlays, list[RushingPlays]]: Rushing play data
            for all teams or only rushing play data for one team
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

        rushing_plays = RushingPlays.get_rushing_plays(
            side_of_ball=side_of_ball,
            start_year=start_year,
            end_year=end_year,
            team=team
        )

        if isinstance(rushing_plays, RushingPlays):
            return rushing_plays

        attrs = ['plays', sort_attr]
        reverses = [True, side_of_ball == 'offense']

        rushing_plays = sort(data=rushing_plays, attrs=attrs, reverses=reverses)
        return rank(data=rushing_plays, attr=sort_attr)
