from typing import ClassVar, Literal, NoReturn, Self

import aiohttp

from bot.services.karen.client import KarenResourceBase
from bot.services.karen.errors import KarenGameError, KarenResponseError
from bot.utils.urls import url_join


class VaultDepositError(KarenGameError):
    @staticmethod
    def raise_from_response_error(error: KarenResponseError) -> NoReturn:
        if isinstance(error.json, dict):
            match error.json.get("error_type"):
                case "NotEnoughVaultCapacity":
                    raise NotEnoughVaultCapacityError()
                case "NonPositiveAmount":
                    raise NonPositiveDepositAmountError()

        raise error


class NotEnoughVaultCapacityError(VaultDepositError):
    def __init__(self) -> None:
        super().__init__("User does not have enough vault capacity")


class NonPositiveDepositAmountError(VaultDepositError):
    def __init__(self) -> None:
        super().__init__("Cannot deposit a negative amount")


class VaultWithdrawError(KarenGameError):
    @staticmethod
    def raise_from_response_error(error: KarenResponseError) -> NoReturn:
        if isinstance(error.json, dict):
            match error.json.get("error_type"):
                case "NotEnoughEmeraldBlocks":
                    raise NotEnoughEmeraldBlocksError()
                case "NonPositiveAmount":
                    raise NonPositiveWithdrawAmountError()

        raise error


class NotEnoughEmeraldBlocksError(VaultWithdrawError):
    def __init__(self) -> None:
        super().__init__("User does not have enough emerald blocks in their vault")


class NonPositiveWithdrawAmountError(VaultWithdrawError):
    def __init__(self) -> None:
        super().__init__("Cannot withdraw a negative amount")


class VaultCommandResource(KarenResourceBase):
    BASE_URL: ClassVar[str] = "/commands/vault/"

    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http)

    async def deposit(self, user_id: str, *, blocks: int | Literal["Max"]) -> None:
        try:
            await self._http.post(
                url_join(self.BASE_URL, user_id, "deposit"),
                json={
                    "blocks": blocks,
                },
                allow_redirects=False,
            )
        except KarenResponseError as e:
            VaultDepositError.raise_from_response_error(e)

    async def withdraw(self, user_id: str, *, blocks: int | Literal["Max"]) -> None:
        await self._http.post(
            url_join(self.BASE_URL, user_id, "withdraw"),
            json={
                "blocks": blocks,
            },
            allow_redirects=False,
        )
