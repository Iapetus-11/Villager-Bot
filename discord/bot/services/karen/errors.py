from __future__ import annotations

from functools import cached_property
from http import HTTPStatus
from typing import NoReturn, Self, cast

import aiohttp
import pydantic_core

from bot.services.karen.utils import Json


class KarenResponseError(Exception):
    _response: aiohttp.ClientResponse
    _content: bytes | None

    status: HTTPStatus

    def __init__(self, response: aiohttp.ClientResponse, status: HTTPStatus, content: bytes | None) -> None:
        self._response = response
        self._content = content

        self.status = status

        content_repr: str | None
        try:
            content_repr = None if content is None else content.decode()
        except UnicodeDecodeError:
            content_repr = str(content)

        super().__init__(": ".join(filter(None, [
            f"HTTP {status} {status.phrase}",
            content_repr,
        ])))

    @classmethod
    async def from_response(cls, response: aiohttp.ClientResponse) -> Self | None:
        """Returns None if the response is OK, otherwise an instance of KarenResponseError"""

        status = HTTPStatus(response.status)

        if status.is_success:
            return None

        content: bytes | None = None
        try:
            content = await response.read()
        except Exception:  # noqa: S110
            pass

        return cls(response=response, status=status, content=content)

    @cached_property
    def json(self) -> Json | None:
        """Attempts to get the json value of the response content"""

        if not self._content:
            return None

        try:
            return pydantic_core.from_json(self._content)
        except ValueError:
            return None


class KarenGameError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    @staticmethod
    def raise_from_response_error(error: KarenResponseError) -> NoReturn:
        """
        Attempts to convert a KarenResponseError to a KarenGameError,
        re-raises the KarenResponseError if it can't be translated
        """

        if not isinstance(error.json, dict):
            raise error

        match error.json.get("error_type"):
            case "UserDoesNotExist":
                raise UserDoesNotExistError()
            case "UserLockCannotBeAcquired":
                raise UserLockCannotBeAcquiredError(cast(str, error.json["lock"]))
            case "NotEnoughEmeralds":
                raise NotEnoughEmeraldsError()

        raise error


class UserDoesNotExistError(KarenGameError):
    def __init__(self) -> None:
        super().__init__("User does not exist")


class UserLockCannotBeAcquiredError(KarenGameError):
    def __init__(self, lock: str) -> None:
        super().__init__(f"User lock {lock!r} cannot be acquired")


class NotEnoughEmeraldsError(KarenGameError):
    def __init__(self) -> None:
        super().__init__("User does not have enough emeralds")
