from typing import Union

from flask import request
from flask_restful import Resource

from exceptions import InvalidRequestError
from models import APPoll, APPollRanking
from utils import flask_response, rank, sort

ASC_SORT_ATTRS = ['avg_preseason', 'avg_final']
WEEKS = ['weeks_number_one', 'weeks_top_five', 'weeks_top_ten', 'weeks']
PRESEASON = ['preseason_number_one', 'preseason_top_five', 'preseason_top_ten',
             'preseason']
FINAL = ['final_number_one', 'final_top_five', 'final_top_ten', 'final']


class APPollRoute(Resource):
    @flask_response
    def get(self) -> Union[APPoll, list[APPoll]]:
        """
        GET request to get AP Poll ranking data for one year. If team
        is provided only get poll data for that team.

        Returns:
          Union[APPoll, list[APPoll]]: Poll data for all teams
              or only poll data for one team
        """
        sort_attr = request.args.get('sort', 'weeks')
        secondary_attr, secondary_reverse = secondary_sort(attr=sort_attr)

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

        poll_data = APPoll.get_ap_poll_data(
            start_year=start_year, end_year=end_year, team=team)

        if isinstance(poll_data, APPoll):
            return poll_data

        attrs = [*secondary_attr, sort_attr]
        reverses = [*secondary_reverse, sort_attr not in ASC_SORT_ATTRS]

        if sort_attr in ['avg_preseason', 'avg_final']:
            poll_data = [item for item in poll_data
                         if getattr(item, sort_attr) is not None]

        poll_data = sort(data=poll_data, attrs=attrs, reverses=reverses)
        return rank(data=poll_data, attr=sort_attr)


def secondary_sort(attr: str) -> tuple:
    """
    Determine the secondary sort attributes and order when the
    primary sort attribute has the same value.

    Args:
        attr (str): The primary sort attribute

    Returns:
        tuple: Secondary sort attributes
    """
    if attr.startswith('weeks'):
        WEEKS.remove(attr)
        secondary_attr = WEEKS

    elif attr.startswith('preseason'):
        PRESEASON.remove(attr)
        secondary_attr = PRESEASON

    elif attr.startswith('final'):
        FINAL.remove(attr)
        secondary_attr = FINAL

    else:
        secondary_attr = [attr]

    return secondary_attr, [True] * len(secondary_attr)


class APPollRankingRoute(Resource):
    @flask_response
    def get(self) -> list[APPollRanking]:
        """
        GET request to get AP Poll rankings for the given year.
        If week is provided, only get rankings for that week. If team
        is provided, only get rankings for that team.

        Returns:
            list[APPollRanking]: AP Poll rankings
        """
        try:
            year = int(request.args['year'])
        except KeyError:
            raise InvalidRequestError(
                'Year is a required query parameter')
        except ValueError:
            raise InvalidRequestError(
                'Query parameter year must be an integer')

        week = request.args.get('week')
        team = request.args.get('team')

        if week is not None:
            try:
                week = int(week)
            except ValueError:
                raise InvalidRequestError(
                    'Query parameter week must be an integer')

        return APPollRanking.get_rankings(year=year, week=week, team=team)
