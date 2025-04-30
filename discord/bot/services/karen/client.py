import abc
import aiohttp


class KarenClient:
    def __init__(self, base_url: str, api_key: str):
        self._http = aiohttp.ClientSession(
            raise_for_status=True,
            conn_timeout=1.0,
            read_timeout=30.0,
            base_url=base_url,
            headers={"Authorization": f"Token {api_key}"},
        )

        from .resources.discord.discord_guild import DiscordGuildsResource
        from .resources.users import UsersResource

        self.users = UsersResource(self._http)
        self.discord_guilds = DiscordGuildsResource(self._http)

    async def close(self):
        await self._http.close()


class KarenResourceBase(abc.ABC):
    def __init__(self, http: aiohttp.ClientSession):
        self._http = http
