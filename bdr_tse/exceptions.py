class BdrTseException(Exception):
    pass


class TimeoutException(BdrTseException):
    pass


class TransportError(BdrTseException):
    pass