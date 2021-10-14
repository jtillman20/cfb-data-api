from functools import wraps
from operator import attrgetter

from flask import request, Response
from jsonpickle import encode

from exceptions import BaseError


def flask_response(function) -> Response:
    """
    A decorator to create a flask Response object with the data
    returned from the given function.

    Args:
        function: Function to execute

    Returns:
        Response: Response object with returned data
    """

    @wraps(function)
    def wrapper(*args, **kwargs) -> Response:
        try:
            data = function(*args, **kwargs)
            status_code = 200

            if request.path[5:] in {'teams', 'conferences'}:
                year = int(request.args['year'])
                data = [item.serialize(year=year) for item in data]

        except (Exception, BaseError) as e:
            data = f'{str(e.__class__.__name__)}: {str(e)}'
            status_code = e.STATUS_CODE if isinstance(e, BaseError) else 500

        return Response(
            response=encode(value=data, unpicklable=False),
            mimetype='application/json',
            status=status_code
        )

    return wrapper


def rank(data: list[any], attr: str) -> list[any]:
    """
    Add `rank` attribute to each object in the list based on the value
    of the sorted attribute.

    Args:
        data (List): Data being sorted
        attr (str): Attribute to sort by

    Returns:
        list: Data with `rank` attribute added to each object
    """
    for index, team in enumerate(data):
        if not index:
            team.rank = 1
            continue

        current_team = data[index]
        current_value = getattr(current_team, attr)

        previous_team = data[index - 1]
        previous_value = getattr(previous_team, attr)

        if current_value != previous_value:
            team.rank = index + 1
        else:
            team.rank = previous_team.rank

    return data


def sort(data: list[any], attrs: list[str], reverses: list[bool]) -> list[any]:
    """
    Sort a list based on the attributes (attrs) and the sort order
    property for each attribute (reverses).

    Args:
        data (list[any]): List to sort
        attrs (list[str]): List of attrbibutes to sort by
        reverses (list[bool]): Sort order property for each attribute
            to determine if reverse should be set to True or False

    Returns:
        list: Sorted list
    """
    for attr, reverse in zip(attrs, reverses):
        data = sorted(data, key=attrgetter(attr), reverse=reverse)

    return data
