import aiohttp


async def read_limited(res: aiohttp.ClientResponse, *, max_bytes: int = 1e6) -> bytes:
    out = bytearray()

    async for data in res.content.iter_any():
        out.extend(data)

        if len(out) > max_bytes:
            raise ValueError("Content length exceeds max length")

    return bytes(out)
