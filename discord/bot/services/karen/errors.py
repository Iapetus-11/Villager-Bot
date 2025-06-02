class KarenGameError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)

        self.message = message


class UserDoesNotExistError(KarenGameError):
    def __init__(self) -> None:
        super().__init__("User does not exist")


class UserLockCannotBeAcquiredError(KarenGameError):
    def __init__(self, lock: str) -> None:
        super().__init__(f"User lock {lock!r} cannot be acquired")


class NotEnoughEmeraldsError(KarenGameError):
    def __init__(self) -> None:
        super().__init__("User does not have enough emeralds")
