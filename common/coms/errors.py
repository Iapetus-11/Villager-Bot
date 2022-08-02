from typing import Optional


class InvalidPacketReceived(Exception):
    def __init__(self, message: str, exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = exception


class WebsocketStateError(Exception):
    def __init__(self, message: str, exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = exception
