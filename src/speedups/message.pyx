import asyncio
import datetime
import re
import io

from .errors import InvalidArgument

cpdef str convert_emoji_reaction(emoji: object):
    if isinstance(emoji, Reaction):
        emoji = emoji.emoji

    if isinstance(emoji, Emoji):
        return f'{emoji.name}:{emoji.id}'

    if isinstance(emoji, PartialEmoji):
        return emoji._as_reaction()

    if isinstance(emoji, str):
        # Reactions can be in :name:id format, but not <:name:id>.
        # No existing emojis have <> in them, so this should be okay.
        return emoji.strip('<>')

    raise InvalidArgument(f'emoji argument must be str, Emoji, or Reaction not {emoji.__class__.__name__}.')
