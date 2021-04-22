import asyncio
import datetime
import re
import io

from discord.errors import InvalidArgument
import discord

from .mixins import Hashable

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


cdef class Message(Hashable):
    cdef object _state
    cdef signed int id
    cdef signed int webhook_id
    cdef list reactions
    cdef list attachments
    cdef list embeds
    cdef object application
    cdef object activity
    cdef object channel
    cdef object _edited_timestamp
    cdef object type
    cdef bint pinned
    cdef object flags
    cdef bint mention_everyone
    cdef bint tts
    cdef str content
    cdef str nonce
    cdef list stickers
    cdef object reference

    def __init__(self, *, state, channel, data):
        self._state = state
