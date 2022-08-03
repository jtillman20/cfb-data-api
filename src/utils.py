from functools import wraps
from operator import attrgetter
from typing import Union

from flask import request, Response
from jsonpickle import encode

from exceptions import BaseError, InvalidRequestError

START_YEAR = 1973
END_YEAR = 2021


def check_side_of_ball(value: str) -> None:
    """
    Check if the side of ball in the request is a valid value of either
    'offense' or 'defense'.

    Args:
        value (str): Side of ball

    Raises:
        InvalidRequestError: The side of ball is an invalid value
    """
    if value not in ['offense', 'defense']:
        raise InvalidRequestError(
            "'side_of_ball' must be either 'offense' or 'defense'")


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


def get_multiple_year_params() -> tuple:
    """
    Get the required query parameter 'start_year' and the optional query
    parameter 'end_year' from the flask request.

    Returns:
        tuple: Start year and end year

    Raises:
        InvalidRequestError: The 'start_year' query paramter is missing
            or either the 'start_year' or 'end_year' query parameter
            has an invalid value
    """
    try:
        start_year = int(request.args['start_year'])
    except KeyError:
        raise InvalidRequestError("'start_year' is a required query parameter")
    except ValueError:
        raise InvalidRequestError(
            "Query parameter 'start_year' must be an integer")

    if not START_YEAR <= start_year <= END_YEAR:
        raise InvalidRequestError(
            f'Query paramter start_year must be between {START_YEAR} and {END_YEAR}')

    try:
        end_year = int(request.args['end_year'])
    except (KeyError, TypeError):
        end_year = None
    except ValueError:
        raise InvalidRequestError(
            "Query parameter 'end_year' must be an integer")

    if end_year and not START_YEAR <= end_year <= END_YEAR:
        raise InvalidRequestError(
            f"Query parameter 'end_year' must be between {START_YEAR} and {END_YEAR}")

    return start_year, end_year


def get_optional_param(name: str, default_value: str = None) -> Union[str, None]:
    """
    Get an optional query parameter from the flask request.

    Args:
        name (str): Parameter name to try to get
        default_value (str): Value if param is missing from the request

    Returns:
        Union[str, None]: Query parameter value
    """
    return request.args.get(name, default_value)


def get_year_param() -> int:
    """
    Get the required query param 'year' from the flask request.

    Returns:
        int: Year

    Raises:
        InvalidRequestError: The 'year' query paramter is missing
            or the 'year' query parameter has an invalid value
    """
    try:
        year = int(request.args['year'])
    except KeyError:
        raise InvalidRequestError("'year' is a required query parameter")
    except ValueError:
        raise InvalidRequestError("Query parameter 'year' must be an integer")

    if not START_YEAR <= year <= END_YEAR:
        raise InvalidRequestError(
            f"Query paramter 'year' must be between {START_YEAR} and {END_YEAR}")
    return year


def rank(data: list[any], attr: str) -> list[any]:
    """
    Add 'rank' attribute to each object in the list based on the value
    of the sorted attribute.

    Args:
        data (List): Data being sorted
        attr (str): Attribute to sort by

    Returns:
        list: Data with 'rank' attribute added to each object
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

    Raises:
        InvalidRequestError: An attribute in 'attrs' is not a valid
            attribute to sort on the list of objects
    """
    for attr, reverse in zip(attrs, reverses):
        try:
            data = sorted(data, key=attrgetter(attr), reverse=reverse)
        except AttributeError:
            raise InvalidRequestError(f"Cannot sort by attribute '{attr}'")

    return data
