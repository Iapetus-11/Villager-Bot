from contextlib import suppress


class SuppressCtxManager:
    def __init__(self, manager):
        self._manager = manager

    def __enter__(self):
        with suppress(Exception):
            self._manager.__enter__()

    def __exit__(self, *args, **kwargs):
        with suppress(Exception):
            self._manager.__exit__(*args, **kwargs)

    async def __aenter__(self):
        with suppress(Exception):
            await self._manager.__aenter__()

    async def __aexit__(self, *args, **kwargs):
        with suppress(Exception):
            await self._manager.__aexit__(*args, **kwargs)
