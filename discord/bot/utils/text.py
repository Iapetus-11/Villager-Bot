import io
import re
from typing import Iterable

import discord


def title_case(text: str) -> str:
    return " ".join([w.capitalize() for w in text.split()])


def shorten_text(text: str, to: int = 2000) -> str:
    if len(text) > to:
        return text[: to - 1] + "…"

    return text


def shorten_chunks(items: list[str], max_size: int) -> Iterable[str]:
    size = 0

    for item in items:
        if len(item) + size > max_size:
            break

        size += len(item)

        yield item


def chunk_by_lines(text: str, max_paragraph_size: int) -> Iterable[str]:
    text_lines = text.splitlines()

    for line in text_lines:
        if len(line) > max_paragraph_size:
            raise ValueError("A singular line may not exceed max_paragraph_size.")

    paragraph = []

    for line in text.splitlines():
        if sum(map(len, paragraph)) + len(line) > max_paragraph_size:
            yield "\n".join(paragraph)
            paragraph.clear()

        paragraph.append(line)

    if paragraph:
        yield "\n".join(paragraph)


def text_to_discord_file(text: str, *, file_name: str | None = None) -> discord.File:
    file_data = io.BytesIO(text.encode(encoding="utf8"))
    file_data.seek(0)
    return discord.File(file_data, filename=file_name)


def clean_user_text_for_output(msg: discord.Message, text: str) -> str:
    if msg.guild:

        def resolve_member(id_: int) -> str:
            m = msg.guild.get_member(id_) or discord.utils.get(msg.mentions, id=id_)  # type: ignore
            return f"@{m.display_name}" if m else "@deleted-user"

        def resolve_role(id_: int) -> str:
            r = msg.guild.get_role(id_) or discord.utils.get(msg.role_mentions, id=id_)  # type: ignore
            return f"@{r.name}" if r else "@deleted-role"

        def resolve_channel(id_: int) -> str:
            c = msg.guild._resolve_channel(id_)  # type: ignore
            return f"#{c.name}" if c else "#deleted-channel"

    else:

        def resolve_member(id_: int) -> str:
            m = discord.utils.get(msg.mentions, id=id_)
            return f"@{m.display_name}" if m else "@deleted-user"

        def resolve_role(id_: int) -> str:
            return "@deleted-role"

        def resolve_channel(id_: int) -> str:
            return "#deleted-channel"

    transforms = {
        "@": resolve_member,
        "@!": resolve_member,
        "#": resolve_channel,
        "@&": resolve_role,
    }

    def repl(match: re.Match) -> str:
        return transforms[match[1]](int(match[2]))

    result = re.sub(r"<(@[!&]?|#)([0-9]{15,20})>", repl, text)

    return discord.utils.escape_mentions(result)
