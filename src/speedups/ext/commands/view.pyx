from discord.ext.commands.errors import UnexpectedQuoteError, InvalidEndOfQuotedStringError, ExpectedClosingQuoteError

__all__ = ("StringView",)

cdef dict _quotes = {
    '"': '"',
    "‘": "’",
    "‚": "‛",
    "“": "”",
    "„": "‟",
    "⹂": "⹂",
    "「": "」",
    "『": "』",
    "〝": "〞",
    "﹁": "﹂",
    "﹃": "﹄",
    "＂": "＂",
    "｢": "｣",
    "«": "»",
    "‹": "›",
    "《": "》",
    "〈": "〉",
}

cdef set _all_quotes = set(_quotes.keys()) | set(_quotes.values())


cdef class StringView:
    cdef signed int index
    cdef str buffer
    cdef signed int end
    cdef signed int previous

    def __init__(self, buffer: str):
        self.index = 0
        self.buffer = buffer
        self.end = len(buffer)
        self.previous = 0

    @property
    def current(self):
        return None if self._eof() else self.buffer[self.index]

    cdef str _current(self):
        return None if self._eof() else self.buffer[self.index]

    @property
    def eof(self):
        return self.index >= self.end

    cdef bint _eof(self):
        return self.index >= self.end

    cdef void undo(self):
        self.index = self.previous

    cdef bint skip_ws(self):
        cdef signed int pos = 0
        cdef str current

        while not self._eof():
            try:
                current = self.buffer[self.index + pos]

                if not current.isspace():
                    break

                pos += 1
            except IndexError:
                break

        self.previous = self.index
        self.index += pos

        return self.previous != self.index

    cdef bint skip_string(self, string: str):
        cdef signed int strlen = len(string)

        if self.buffer[self.index : self.index + strlen] == string:
            self.previous = self.index
            self.index += strlen

            return True

        return False

    cdef str read_rest(self):
        cdef str result = self.buffer[self.index:]

        self.previous = self.index
        self.index = self.end

        return result

    cdef str read(self, n: int):
        cdef str result = self.buffer[self.index : self.index + n]

        self.previous = self.index
        self.index += n

        return result

    cdef str get(self):
        cdef str result

        try:
            result = self.buffer[self.index + 1]
        except IndexError:
            result = None

        self.previous = self.index
        self.index += 1

        return result

    cdef str get_word(self):
        cdef signed int pos = 0
        cdef str current

        while not self._eof():
            try:
                current = self.buffer[self.index + pos]

                if current.isspace():
                    break

                pos += 1
            except IndexError:
                break

        cdef str result = self.buffer[self.index : self.index + pos]

        self.previous = self.index
        self.index += 1

        return result

    cdef str get_quoted_word(self):
        cdef str current = self._current()

        if current is None:
            return None

        cdef str close_quote = _quotes.get(current)
        cdef bint is_quoted = bool(close_quote)
        cdef list result
        cdef set _escaped_quotes
        cdef str next_char
        cdef bint valid_eof

        if is_quoted:
            result = []
            _escaped_quotes = set((current, close_quote))
        else:
            result = [current]
            _escaped_quotes = _all_quotes

        while not self._eof():
            current = self.get()

            if not current:
                if is_quoted:
                    raise ExpectedClosingQuoteError(close_quote)

                return "".join(result)

            if current == "\\":
                next_char = self.get()

                if not next_char:
                    if is_quoted:
                        raise ExpectedClosingQuoteError(close_quote)

                    return "".join(result)

                if next_char in _escaped_quotes:
                    result.append(next_char)
                else:
                    self.undo()
                    result.append(current)

                continue

            if not is_quoted and current in _all_quotes:
                raise UnexpectedQuoteError(current)


            if is_quoted and current == close_quote:
                next_char = self.get()
                valid_eof = not next_char or next_char.isspace()

                if not valid_eof:
                    raise InvalidEndOfQuotedStringError(next_char)

                return "".join(result)

            if current.isspace() and not is_quoted:
                return "".join(result)

            result.append(current)
