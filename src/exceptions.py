class BaseError(Exception):
    """
    Base error for all application errors.
    """
    STATUS_CODE = 500


class InvalidRequestError(BaseError):
    """
    An error for any invalid API request.
    """
    STATUS_CODE = 400
