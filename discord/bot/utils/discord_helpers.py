import time
import discord


async def fetch_aprox_ban_count(guild: discord.Guild, seconds: float, chunk_size: int = 500) -> str:
    assert chunk_size > 0

    start_time: float = time.time()
    last_entry: discord.User | None = None
    ban_count = 0

    while True:
        # ran out of time
        if (time.time() - start_time) > seconds:
            return f"{ban_count}+"

        ban_entries_chunk = [e async for e in guild.bans(limit=chunk_size, after=last_entry)]

        if ban_entries_chunk:
            last_entry = ban_entries_chunk[-1].user
            ban_count += len(ban_entries_chunk)

        # there are no more ban entries to fetch
        if len(ban_entries_chunk) < chunk_size or last_entry is None:
            return str(ban_count)
