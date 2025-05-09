import re
from typing import Any

URL_SCHEME_REGEX = re.compile(r"^[a-zA-Z0-9+.-]*://$")


def url_join(*raw_pieces: Any) -> str:
    """
    Takes in pieces of a URL and joins them together, ignoring extra forward slashes (/). If the
    first piece is a scheme (ex: https://), it is left untouched, however the other pieces
    have extra forward slashes stripped and added in later for consistency purposes. Pieces can be
    any type, but are stringified (str(...)).

    Examples:
        url_join('https://', 'example.com', 'abc/123', 'x.html////', '#heresahash')
            -> https://example.com/abc/123/x.html/#heresahash

        url_join('https://example.com', '/abc/123/', '/x.html/')
            -> https://example.com/abc/123/x.html/
    """

    pieces = list(map(str, raw_pieces))

    scheme = ""
    out = []

    for piece in pieces:
        if URL_SCHEME_REGEX.match(piece):
            if scheme:
                raise ValueError(f"Encountered two schemes: {scheme!r} and {piece!r}")

            scheme = piece
            continue

        out.append(piece.strip("/"))

    if pieces[-1].endswith("/"):
        out.append("")

    return scheme + "/".join(out)
