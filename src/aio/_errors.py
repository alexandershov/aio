class BaseError(Exception):
    pass


class CancelledError(BaseError):
    pass


class InvalidStateError(BaseError):
    pass
