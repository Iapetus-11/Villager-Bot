import asyncio
import cgi
import os
from pathlib import Path
from zipfile import ZipFile

import aiofiles
import aiohttp


class FontHandler:
    def __init__(self, font_urls: list[str], output_directory: str):
        self.font_urls = font_urls
        self.output_directory = output_directory

    @staticmethod
    def _get_file_name(response: aiohttp.ClientResponse) -> str:
        _, content_disposition = cgi.parse_header(response.headers["Content-Disposition"])
        return content_disposition["filename"]

    def _handle_zip_files(self):
        for file in os.listdir(self.output_directory):
            if file.endswith(".zip"):
                with ZipFile(Path(self.output_directory, file)) as zf:
                    zf.extractall(self.output_directory)

    async def _write_file(self, file_name: str, content: bytes) -> None:
        async with aiofiles.open(Path(self.output_directory, file_name), "wb+") as f:
            await f.write(content)

    async def retrieve(self) -> list[str]:
        async with aiohttp.ClientSession() as http:
            responses: list[aiohttp.ClientResponse] = await asyncio.gather(
                *map(http.get, self.font_urls)
            )
            contents: list[bytes] = await asyncio.gather(*[r.read() for r in responses])

            await asyncio.gather(
                *[
                    self._write_file(self._get_file_name(response), content)
                    for response, content in zip(responses, contents)
                ]
            )

        await asyncio.to_thread(self._handle_zip_files)

        files = await asyncio.to_thread(os.listdir, self.output_directory)
        return [
            str(Path(self.output_directory, f))
            for f in files
            if f.endswith(".ttf") or f.endswith(".otf")
        ]
