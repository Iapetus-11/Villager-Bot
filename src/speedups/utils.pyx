import unicodedata
import datetime
import json
import re

from discord.errors import InvalidArgument

__all__ = (
    "DISCORD_EPOCH",
    "_IS_ASCII",
    "UNICODE_WIDE_CHAR_TYPE",
    "snowflake_time",
    "time_snowflake",
    "_unique",
    "_get_mime_type_for_image",
    "to_json",
    "valid_icon_size",
    "_string_width"
)

cdef signed long long DISCORD_EPOCH = 1420070400000
cdef object _IS_ASCII = re.compile(r"^[\x00-\x7f]+$")
cdef str UNICODE_WIDE_CHAR_TYPE = "WFA"


cdef object snowflake_time(id: int):
    cdef signed long long timestamp = ((id >> 22) + DISCORD_EPOCH) / 1000
    return datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=datetime.timezone.utc)


cdef signed long time_snowflake(dt: object, high: bool = False):
    cdef signed long long discord_millis = int(dt.timestamp() * 1000 - DISCORD_EPOCH)
    return (discord_millis << 22) + (2 ** 22 - 1 if high else 0)


cdef list _unique(iterable: object):
    return list(set(iterable))


cdef str _get_mime_type_for_image(data: bytes):
    if data.startswith(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"):
        return "image/png"
    elif data[0:3] == b"\xff\xd8\xff" or data[6:10] in (b"JFIF", b"Exif"):
        return "image/jpeg"
    elif data.startswith((b"\x47\x49\x46\x38\x37\x61", b"\x47\x49\x46\x38\x39\x61")):
        return "image/gif"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    else:
        raise InvalidArgument("Unsupported image type given")


cdef str to_json(obj: object):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True)


cdef bint valid_icon_size(size: int):
    return not size & (size - 1) and 4096 >= size >= 16


cdef int _string_width(string: str, _IS_ASCII: object = _IS_ASCII):
    cdef bint match = _IS_ASCII.match(string)

    if match:
        return match.endpos

    cdef object func = unicodedata.east_asian_width
    return sum(2 if func(char_) in UNICODE_WIDE_CHAR_TYPE else 1 for char_ in string)
