import pytest

from bot.utils.urls import url_join

EXAMPLE_UUID = "00000000-0000-0000-0000-000000000000"


@pytest.mark.parametrize(
    ("pieces", "expected"),
    [
        (["https://", "example.com", "abc", "123", "1.html"], "https://example.com/abc/123/1.html"),
        (["https://", "example.com", "abc", "123", "1.html/"], "https://example.com/abc/123/1.html/"),
        (["https://example.com", "abc", "/123////////", "/x.html/"], "https://example.com/abc/123/x.html/"),
        (["https://example.com", "abc", 123], "https://example.com/abc/123"),
        (["https://example.com", "abc", EXAMPLE_UUID], f"https://example.com/abc/{EXAMPLE_UUID}"),
        (["ftp://iapetus11.me", "super", "/secret/homework/"], "ftp://iapetus11.me/super/secret/homework/"),
        (["http://iapetus11.me/", "fractals", "#hash"], "http://iapetus11.me/fractals/#hash"),
        (["minecraft.global", "login"], "minecraft.global/login"),
        (["https://minecraft.global"], "https://minecraft.global"),
    ],
)
def test_url_join(pieces, expected):
    assert url_join(*pieces) == expected
