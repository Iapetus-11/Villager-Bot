from bot.services.karen.client import KarenResourceBase
from bot.utils.urls import url_join


class BadgesResource(KarenResourceBase):
    BASE_URL = "/users/{user_id}/badges/"

    async def get_image(self, user_id: str) -> bytes:
        response = await self._http.get(
            url_join(self.BASE_URL.format(user_id=user_id), "/image/"),
            allow_redirects=False,
        )

        return await response.read()
