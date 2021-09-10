from functools import wraps

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
