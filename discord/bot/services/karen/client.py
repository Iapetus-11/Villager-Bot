import abc
import aiohttp


class KarenClient:
    def __init__(self, base_url: str):
        self._http = aiohttp.ClientSession(
            raise_for_status=True, conn_timeout=1.0, read_timeout=30.0, allow_redirects=False, base_url=base_url
        )


class KarenResourceBase(abc.ABC):
    def __init__(self, http: aiohttp.ClientSession):
        self._http = http
