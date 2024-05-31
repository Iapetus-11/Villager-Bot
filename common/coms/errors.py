class InvalidPacketReceived(Exception):
    """Raised when an invalid packet is received"""

    def __init__(self, message: str, exception: Exception | None = None):
        super().__init__(message)
        self.original_exception = exception


class WebsocketStateError(Exception):
    """Raised when a websocket is in an invalid state"""

    def __init__(self, message: str, exception: Exception | None = None):
        super().__init__(message)
        self.original_exception = exception


class NoConnectedClientsError(Exception):
    """Raised when there are no connected clients to broadcast to"""

    def __init__(self):
        super().__init__("There are no connected clients to broadcast to")
