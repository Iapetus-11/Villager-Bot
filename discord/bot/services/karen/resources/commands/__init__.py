from typing import ClassVar

import aiohttp

from bot.services.karen.client import KarenResourceBase


class CommandsResourceGroup(KarenResourceBase):
    BASE_URL: ClassVar[str] = "/commands/"

    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http)

        from .profile import ProfileCommandResource
        from .shop import ShopCommandResource
        from .vault import VaultCommandResource

        self.profile = ProfileCommandResource(http)
        self.vault = VaultCommandResource(http)
        self.shop = ShopCommandResource(http)
