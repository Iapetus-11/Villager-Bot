import datetime
import typing

from discord.errors import InvalidArgument

__all__ = (
    "DISCORD_EPOCH",
    "snowflake_time",
    "time_snowflake",
    "_unique",
    "_get_mime_type_for_image",
)

cdef signed long DISCORD_EPOCH = 1420070400000


cdef object snowflake_time(id: int):
    cdef signed long timestamp = ((id >> 22) + DISCORD_EPOCH) / 1000
    return datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=datetime.timezone.utc)


cdef signed long time_snowflake(dt: object, high: bool = False):
    cdef signed long discord_millis = int(dt.timestamp() * 1000 - DISCORD_EPOCH)
    return (discord_millis << 22) + (2 ** 22 - 1 if high else 0)


cdef list _unique(iterable: object):
    return list(set(iterable))


cdef str _get_mime_type_for_image(data: bytes):
    if data.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
        return 'image/png'
    elif data[0:3] == b'\xff\xd8\xff' or data[6:10] in (b'JFIF', b'Exif'):
        return 'image/jpeg'
    elif data.startswith((b'\x47\x49\x46\x38\x37\x61', b'\x47\x49\x46\x38\x39\x61')):
        return 'image/gif'
    elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return 'image/webp'
    else:
        raise InvalidArgument('Unsupported image type given')
